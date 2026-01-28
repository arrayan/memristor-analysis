import PySide6.QtWidgets as qt
from PySide6.QtGui import QAction
from core.actions import MenuActions

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

        # File Menu
        self.file_menu = self.addMenu("File")

        # Actions
        # self.action_import_device = QAction("Device", self)
        # self.action_import_stack = QAction("Stack", self)
        # self.action_export_all_to = QAction("All To", self)
        # self.action_export_current_to = QAction("Current To", self)
        # self.action_export_all = QAction("Export All", self)
        # self.action_export_current = QAction("Current", self)
        # self.action_exit = QAction("Exit", self)
        # self.action_exit.triggered.connect(qt.QApplication.quit)

        # Import
        self.file_menu.addSection("Import")
        self.file_menu.addAction(self.menu_actions[MenuActions.IMPORT_DEVICE])
        self.file_menu.addAction(self.menu_actions[MenuActions.IMPORT_STACK])
        self.file_menu.addSeparator()
        # Export
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
        # Exit
        self.file_menu.addAction(self.menu_actions[MenuActions.EXIT])

        # Help Menu
        self.help_menu = self.addMenu("Help")
        self.action_view_help = QAction("View Help", self)
        self.help_menu.addAction(self.action_view_help)