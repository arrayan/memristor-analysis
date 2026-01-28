import PySide6.QtWidgets as qt
from PySide6.QtGui import QAction

class ActionBar(qt.QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # File Menu
        self.file_menu = self.addMenu("File")

        self.action_import_device = QAction("Import Device", self)
        self.action_import_stack = QAction("Import Stack", self)
        self.action_export_all = QAction("Export All", self)
        self.action_exit = QAction("Exit", self)

        self.file_menu.addAction(self.action_import_device)
        self.file_menu.addAction(self.action_import_stack)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.action_export_all)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.action_exit)

        # Help Menu
        self.help_menu = self.addMenu("Help")
        self.action_view_help = QAction("View Help", self)
        self.help_menu.addAction(self.action_view_help)