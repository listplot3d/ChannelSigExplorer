import inspect
import os
import sys
import importlib.util
import traceback

from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph.dockarea as pg_dockarea
from GUIComp_StreamMgmt import EEGStreamManager


class MainWindow(QtWidgets.QMainWindow):
    """Main Window Class"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-TIme Single-Channel EEG Explorer")
        self.resize(1000, 400)

        # Initialize components
        self.init_state()
        self.init_status_bar()
        self.init_layout()

        self.init_toolbar()

    # ------------------------ Initialization ------------------------

    def init_state(self):
        """Initialize state variables"""
        self.stream_mgr: EEGStreamManager

        # Store loaded indicator modules
        self.loaded_indicators = []

        self.loaded_docks = {}  # {file_name: (dock, indicator_handler)}

    def init_status_bar(self):
        """Initialize the status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Status: Ready")

    def init_layout(self):
        """Initialize layout and Dock"""
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)

        # Initialize the file browser
        self.init_file_browser()

        # Initialize the right DockArea
        self.init_dock_area()

    def init_toolbar(self):
        """Initialize the toolbar"""
        tool_bar = self.addToolBar("Toolbar")
        self.stream_mgr = EEGStreamManager(self)  # Stream management functionality, initialized here
        self.stream_mgr.add_conn_menu_on_toolbar(tool_bar)
        self.stream_mgr.add_record_menu_on_toolbar(tool_bar)

    def init_file_browser(self):
        """Initialize the indicator file browser"""
        file_browser_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        # Create a tree browser with directory structure
        self.file_tree = QtWidgets.QTreeWidget()
        self.file_tree.setHeaderLabel("Indicator Files")
        self.file_tree.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        self.file_tree.itemSelectionChanged.connect(self.update_load_button_state)
        self.file_tree.setAnimated(True)  # Enable animation for expansion

        # Define the load button
        self.load_button = QtWidgets.QPushButton("Load Indicator")  # Initialize button
        self.load_button.clicked.connect(self.load_selected_indicator)
        self.load_button.setEnabled(False)  # Initially disable the button

        # Configure icons (optional, for folder/file icons)
        self.icon_provider = QtWidgets.QFileIconProvider()

        # Build the directory tree
        self.build_file_tree()

        layout.addWidget(self.file_tree)
        layout.addWidget(self.load_button)
        file_browser_widget.setLayout(layout)

        # Add the file browser to the left side of the splitter
        self.splitter.addWidget(file_browser_widget)

    def on_tree_item_double_clicked(self, item, column):
        """Handle tree node double-click event"""
        path = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if os.path.isfile(path):
            rel_path = os.path.relpath(path, "indicators")
            self.load_indicator_module(rel_path)

    def update_load_button_state(self):
        """Update button state based on the selected item type"""
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            self.load_button.setEnabled(False)
            return

        item = selected_items[0]
        path = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        self.load_button.setEnabled(os.path.isfile(path))

    def build_file_tree(self):
        """Build the directory tree structure"""
        self.file_tree.clear()
        indicators_dir = "indicators"

        if not os.path.exists(indicators_dir):
            self.status_bar.showMessage("Status: Indicator folder not found")
            return

        # Recursively scan the directory
        root_item = self.create_tree_item(indicators_dir, is_dir=True)
        self.file_tree.addTopLevelItem(root_item)
        self.file_tree.expandAll()  # Expand all nodes by default

    def create_tree_item(self, path, parent=None, is_dir=False):
        """Recursively create tree nodes"""
        name = os.path.basename(path)
        item = QtWidgets.QTreeWidgetItem([name])
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, path)  # Store the complete path

        if is_dir:
            # item.setIcon(0, self.folder_icon)
            # Add child nodes
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path) and not entry.startswith("__"):
                    child = self.create_tree_item(full_path, item, is_dir=True)
                    item.addChild(child)
                elif entry.endswith(".py") and not entry.startswith("__"):
                    child = self.create_tree_item(full_path, item)
                    item.addChild(child)
        # else:
        # item.setIcon(0, self.file_icon)

        return item

    def load_selected_indicator(self):
        """Load the selected indicator file"""
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("Status: No indicator file selected")
            return

        for item in selected_items:
            file_name = item.text(0)
            self.load_indicator_module(file_name)

    def load_indicator_module(self, file_name):
        """Dynamically load an indicator module and create a new Dock on the right"""
        try:
            indicators_dir = os.path.join(os.getcwd(), "indicators")

            # Add the indicators directory to sys.path if it is not already present
            if indicators_dir not in sys.path:
                sys.path.insert(0, indicators_dir)

            module_name = file_name[:-3]  # Remove the `.py` suffix
            module_path = os.path.join(indicators_dir, file_name)

            # Check if the module has already been loaded
            if file_name in self.loaded_docks:
                # If the module is already loaded, invoke the close method
                dock, _ = self.loaded_docks[file_name]
                dock.close()  # Trigger Dock's close behavior
                return

            # Dynamically load the module
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get all classes in the module
            classes = [
                obj for _, obj in inspect.getmembers(module, inspect.isclass)
                if obj.__module__ == module_name  # Ensure the class is defined in the module
            ]

            if not classes:
                self.status_bar.showMessage(f"Status: No classes found")
                return

            # Find the first class that implements the process_data_and_update_plot interface
            IndicatorClass = next(
                (cls for cls in classes if
                 hasattr(cls, "process_new_data_and_update_plot") and callable(
                     getattr(cls, "process_new_data_and_update_plot"))),
                None
            )

            if not IndicatorClass:
                self.status_bar.showMessage(f"Status: No class found implementing process_new_data_and_update_plot")
                return

            self.status_bar.showMessage(f"Status: Found class {IndicatorClass.__name__}")

            indicator_handler = IndicatorClass()

            # Create the plotting widget
            plot_widget = indicator_handler.create_pyqtgraph_plotWidget()

            # Create a new Dock
            new_dock = pg_dockarea.Dock(file_name, size=(1, 1))  # Set Dock title as file name
            new_dock.setTitle(module_name)
            new_dock.addWidget(plot_widget)

            # Add Dock to DockArea
            self.dock_area.addDock(new_dock, 'top')  # Add to the top

            # Save the loaded indicator module and instance
            self.loaded_docks[file_name] = (new_dock, indicator_handler)
            self.loaded_indicators.append(indicator_handler)
            self.status_bar.showMessage(f"Status: Successfully loaded indicator {module_name}")

            # Handle Dock close events
            new_dock.sigClosed.connect(lambda: self.remove_dock(file_name))

        except Exception as e:
            traceback.print_exc()
            self.status_bar.showMessage(f"Status: Failed to load indicator {file_name}")

    def remove_dock(self, file_name):
        """Remove records and release resources when the Dock is closed"""
        if file_name in self.loaded_docks:
            dock, indicator_handler = self.loaded_docks[file_name]

            # Remove from the state
            self.loaded_docks.pop(file_name)

            # If needed, release resources of indicator_handler here
            if indicator_handler in self.loaded_indicators:
                self.loaded_indicators.remove(indicator_handler)

            # Display status information
            self.status_bar.showMessage(f"Status: Successfully removed indicator {file_name}")

    # ------------------------ Dock Initialization ------------------------

    def init_dock_area(self):
        """Initialize DockArea"""
        self.dock_area = pg_dockarea.DockArea()
        self.splitter.addWidget(self.dock_area)
        self.splitter.setStretchFactor(1, 2)  # The right side occupies a larger proportion

    # def update_indicators(self):
    #     self.stream_mgr.update_indicators(self.loaded_indicators)

    # ------------------------ Window Close Event ------------------------

    def closeEvent(self, event):
        """Window close event"""
        if self.stream_mgr.timer:
            self.stream_mgr.timer.stop()
            self.stream_mgr.disconnect_stream()
            event.accept()


def check_pycache_and_compile():
    """
    检查 __pycache__ 是否存在，如果不存在，提示用户并模拟编译过程。
    """
    pycache_exists = os.path.exists("__pycache__")
    if not pycache_exists:
        print("Compiling for the first time... This may take a few moments.")
        # time.sleep(5)  # 模拟编译耗时
        # print("Compilation completed!")
    # else:
    #     print("Detected existing __pycache__. Skipping compilation.")

if __name__ == "__main__":
    check_pycache_and_compile()

    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    app.exec()
