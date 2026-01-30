import PySide6.QtWidgets as qt
from PySide6.QtGui import QAction, QActionGroup
from core import MenuActions

class MenuBar(qt.QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.menu_actions = {}
        self.setup_ui()

    def setup_ui(self):
        # Create Actions from enum
        for action in MenuActions:
            menu_action = QAction(action.text, self)
            if action.shortcut:
                menu_action.setShortcut(action.shortcut)
            
            # Store it so we can access it later
            self.menu_actions[action] = menu_action

        self.setup_file_menu()
        self.setup_options_menu()
        self.setup_help_menu()
        

    def setup_file_menu(self):
        self.file_menu = self.addMenu("File")

        self.file_menu.addSection("Import")
        self.file_menu.addAction(self.menu_actions[MenuActions.IMPORT_DEVICE])
        self.file_menu.addAction(self.menu_actions[MenuActions.IMPORT_STACK])
        self.file_menu.addSeparator()

        self.file_menu.addSection("Export")
        self.file_sub_menu_export_all = self.file_menu.addMenu("All To")
        self.file_sub_menu_export_current = self.file_menu.addMenu("Current To")
        self.file_sub_menu_export_all.addAction(self.menu_actions[MenuActions.EXPORT_ALL_PNG])
        self.file_sub_menu_export_all.addAction(self.menu_actions[MenuActions.EXPORT_ALL_JPEG])
        self.file_sub_menu_export_all.addAction(self.menu_actions[MenuActions.EXPORT_ALL_APS])
        self.file_sub_menu_export_current.addAction(self.menu_actions[MenuActions.EXPORT_CURRENT_PNG])
        self.file_sub_menu_export_current.addAction(self.menu_actions[MenuActions.EXPORT_CURRENT_JPEG])
        self.file_sub_menu_export_current.addAction(self.menu_actions[MenuActions.EXPORT_CURRENT_APS])
        self.file_menu.addAction(self.menu_actions[MenuActions.EXPORT_ALL])
        self.file_menu.addAction(self.menu_actions[MenuActions.EXPORT_CURRENT])
        self.file_menu.addSeparator()

        self.file_menu.addAction(self.menu_actions[MenuActions.EXIT])

    def setup_options_menu(self):
        self.options_menu = self.addMenu("Options")
        scale = QActionGroup(self)
        scale.setExclusive(True)
        scale_lin = QAction("linear", self, checkable=True)
        scale_log = QAction("linear", self, checkable=True)
        scale.addAction(scale_lin)
        scale_lin.setChecked(True)
        scale.addAction(scale_log)

        self.options_menu.addSection("Scale")
        self.options_menu.addActions([scale_lin, scale_log])


        return

    def setup_help_menu(self):
        self.help_menu = self.addMenu("Help")
        self.action_view_help = QAction("View Help", self)
        self.help_menu.addAction(self.action_view_help)