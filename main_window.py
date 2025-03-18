import inspect
import os
import sys
import importlib.util
import traceback
import time
import argparse

from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph.dockarea as pg_dockarea
from GUIComp_StreamMgmt import EEGStreamManager
from GUIComp_FileDataMgmt import FileDataManager



class MainWindow(QtWidgets.QMainWindow):
    """Main Window Class"""

    def __init__(self, debug_mode=False, mode="realtime"):
        self.debug_mode = debug_mode

        super().__init__()
        self.setWindowTitle("Real-TIme Single-Channel EEG Explorer")
        self.resize(1000, 400)

        # Initialize components
        self.init_state(mode)
        self.init_status_bar()
        self.init_layout()

        self.init_toolbar()

    # ------------------------ Initialization ------------------------

    def init_state(self, mode):
        """Initialize state variables"""
        self.stream_mgr: EEGStreamManager
        self.file_mgr: FileDataManager

        # Store loaded indicator modules
        self.loaded_indicators = []

        self.loaded_docks = {}  # {file_name: (dock, indicator_handler)}
        
        # 模式标志：实时模式或离线模式
        self.mode = mode  # "realtime" 或 "offline"

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
        
        # 添加模式切换按钮
        self.mode_button = QtWidgets.QPushButton("实时模式")
        self.mode_button.clicked.connect(self.toggle_mode)
        tool_bar.addWidget(self.mode_button)
        
        # 添加分隔符
        tool_bar.addSeparator()
        
        # 初始化流管理器和文件管理器
        self.stream_mgr = EEGStreamManager(self, self.debug_mode)  # Stream management functionality
        self.file_mgr = FileDataManager(self, self.debug_mode)  # File data management functionality

        # 根据当前模式显示相应的管理器控件
        self.update_toolbar_by_mode(tool_bar)
        
        # Add a spacer to push the GitHub link to the right
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        tool_bar.addWidget(spacer)
        
        # Add GitHub link label
        github_label = QtWidgets.QLabel('<a href="https://github.com/listplot3d/ChannelSigExplorer/">Help</a>')
        github_label.setOpenExternalLinks(True)
        github_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        github_label.setStyleSheet("QLabel { padding-right: 10px; }")
        tool_bar.addWidget(github_label)

    def update_toolbar_by_mode(self, toolbar):
        """根据当前模式更新工具栏"""
        # 清除现有的动态控件
        actions_to_remove = []
        for action in toolbar.actions():
            if action.text() not in ["实时模式", "离线模式", "Help"]:
                actions_to_remove.append(action)
        
        for action in actions_to_remove:
            toolbar.removeAction(action)
        
        if self.mode == "realtime":
            self.stream_mgr.add_conn_menu_on_toolbar(toolbar)
            self.stream_mgr.add_record_menu_on_toolbar(toolbar)
        else:  # offline mode
            self.file_mgr.add_file_menu_on_toolbar(toolbar)
            self.file_mgr.add_timeline_controls_on_toolbar(toolbar)

    def toggle_mode(self):
        """切换实时/离线模式"""
        if self.mode == "realtime":
            self.mode = "offline"
            self.mode_button.setText("离线模式")
            # 关闭所有已加载的指标
            self.close_all_indicators()
            # 更新工具栏
            self.update_toolbar_by_mode(self.addToolBar("Toolbar"))
            self.status_bar.showMessage("已切换到离线模式")
        else:
            self.mode = "realtime"
            self.mode_button.setText("实时模式")
            # 关闭所有已加载的指标
            self.close_all_indicators()
            # 更新工具栏
            self.update_toolbar_by_mode(self.addToolBar("Toolbar"))
            self.status_bar.showMessage("已切换到实时模式")

    def close_all_indicators(self):
        """关闭所有已加载的指标"""
        for file_name in list(self.loaded_docks.keys()):
            dock, _ = self.loaded_docks[file_name]
            dock.close()

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
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='ChannelSigExplorer - EEG数据分析工具')
    parser.add_argument('--debug', type=str, choices=['true', 'false'], default='false',
                        help='是否启用调试模式 (true/false)')
    parser.add_argument('--mode', type=str, choices=['realtime', 'offline'], default='realtime',
                        help='运行模式: realtime(实时模式) 或 offline(离线模式)')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 设置调试模式和运行模式
    debug_mode = args.debug.lower() == 'true'
    mode = args.mode.lower()
    
    # 输出当前设置
    print(f"启动参数: 运行模式={mode}，调试模式={debug_mode}")

    check_pycache_and_compile()

    app = QtWidgets.QApplication([])  
    win = MainWindow(debug_mode, mode)
    win.show()
    app.exec()
