import sys
import PySide6.QtWidgets as qt
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from .graph_section import GraphSection
from src.data.data_handler import DataHandler
from src.data.validators import is_valid_excel



class MainWindow(qt.QMainWindow):
    def __init__(self):
        self.loaded_data = None
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Create tab widget
        self.tabs = qt.QTabWidget()

        # Analysis tab
        analysis_tab = qt.QWidget()
        analysis_layout = qt.QVBoxLayout()

        window_title = qt.QLabel("Analysis here")
        window_title.setAlignment(Qt.AlignCenter)
        analysis_layout.addWidget(window_title)

        # Create graph section using the separate class
        self.graph_section = GraphSection()
        analysis_layout.addWidget(self.graph_section, stretch=1)

        # Import panel - centered under the graphs
        import_panel = qt.QWidget()
        import_layout = qt.QHBoxLayout()
        import_label = qt.QLabel("Import file:")
        self.import_path_label = qt.QLabel("")  # To show selected file path
        import_button = qt.QPushButton("Browse")
        import_button.clicked.connect(self.browse_file)  # Connect button
        import_layout.addStretch()
        import_layout.addWidget(import_label)
        import_layout.addWidget(self.import_path_label, stretch=1)
        import_layout.addWidget(import_button)
        import_layout.addStretch()
        import_panel.setLayout(import_layout)

        analysis_layout.addWidget(import_panel)
        analysis_tab.setLayout(analysis_layout)

        # Add only Analysis tab to the widget
        self.tabs.addTab(analysis_tab, "Analysis")

        self.setCentralWidget(self.tabs)

        # Menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        import_action = QAction("Import", self)
        import_action.triggered.connect(self.browse_file)  # Menu also opens dialog
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(import_action)
        file_menu.addAction(exit_action)
        # PullRequest

        # Help menu
        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("View Help", self)
        help_action.triggered.connect(self.show_help_dialog)
        help_menu.addAction(help_action)

        self.setWindowTitle("MemResistor Analysis Tool")
        self.resize(600, 400)
        self.showMaximized()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Select Excel file",
        filter="Excel Files (*.xlsx)"
    )

        if not file_path:
            return

    # Validate using validators.py
        if not is_valid_excel(file_path):
            QMessageBox.warning(
            self,
            "Invalid file",
            "Only .xlsx files are supported."
        )
            return

    # Let the GUI display the chosen file
        self.import_path_label.setText(file_path)

    # Load using data_handler
        try:
            self.loaded_data = DataHandler.load_excel(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Read Error", f"Failed to load file:\n{e}")
        return

    def show_help_dialog(self):
        """Show help in a dialog window"""
        help_dialog = qt.QDialog(self)
        help_dialog.setWindowTitle("Help & Documentation")
        help_dialog.setGeometry(100, 100, 600, 400)

        layout = qt.QVBoxLayout()

        help_text = qt.QTextEdit()
        help_text.setReadOnly(True)
        help_text.setText(
            "<h2>MemResistor Analysis Tool</h2>"
            "<p><b>Getting Started:</b></p>"
            "<ul>"
            "<li>Click 'Browse' to select a file for analysis</li>"
            "<li>The selected file path will appear in the import panel</li>"
            "</ul>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Import and analyze memristor data files</li>"
            "<li>View analysis results in the I-V-T graphs</li>"
            "</ul>"
            "<p><b>Need Help?</b></p>"
            "<p>For more information, check the Help menu or contact support.</p>"
        )

        layout.addWidget(help_text)

        close_button = qt.QPushButton("Close")
        close_button.clicked.connect(help_dialog.close)
        layout.addWidget(close_button)

        help_dialog.setLayout(layout)
        help_dialog.exec()


if __name__ == "__main__":
    app = qt.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
