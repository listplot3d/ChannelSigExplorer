from pyqtgraph.Qt import QtWidgets


class GUI_Utils:
    @staticmethod
    def transform_menu_to_toolbutton(text, menu):
        """创建菜单按钮"""
        button = QtWidgets.QToolButton()
        button.setText(text)
        button.setMenu(menu)
        button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        return button