import sys
import PySide6.QtWidgets as qt
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from graph_section import GraphSection

class MainWindow(qt.QMainWindow):
    def __init__(self):
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

        # Import panel at the bottom
        import_panel = qt.QWidget()
        import_layout = qt.QHBoxLayout()
        import_label = qt.QLabel("Import file:")
        self.import_path_label = qt.QLabel("")  # To show selected file path
        import_button = qt.QPushButton("Browse")
        import_button.clicked.connect(self.browse_file)  # Connect button
        import_layout.addWidget(import_label)
        import_layout.addWidget(self.import_path_label)
        import_layout.addWidget(import_button)
        import_panel.setLayout(import_layout)

        analysis_layout.addWidget(import_panel)
        analysis_tab.setLayout(analysis_layout)

        # Help tab
        help_tab = qt.QWidget()
        help_layout = qt.QVBoxLayout()
        
        help_title = qt.QLabel("Help & Documentation")
        help_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        
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
            "<li>View analysis results in the Analysis tab</li>"
            "</ul>"
            "<p><b>Need Help?</b></p>"
            "<p>For more information, check the File menu or contact support.</p>"
        )
        
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_text)
        help_tab.setLayout(help_layout)

        # Add tabs to the widget
        self.tabs.addTab(analysis_tab, "Analysis")
        self.tabs.addTab(help_tab, "Help")

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
        #PullRequest

        # Help menu
        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("View Help", self)
        help_action.triggered.connect(self.show_help_tab)
        help_menu.addAction(help_action)

        self.setWindowTitle("MemResistor Analysis Tool")
        self.resize(600, 400)
        self.showMaximized()

    def browse_file(self):
        file_path, _ = qt.QFileDialog.getOpenFileName(self, "Select file")
        if file_path:
            self.import_path_label.setText(file_path)  # Show chosen file
            # Testing Pull request

    def show_help_tab(self):
        """Switch to the help tab"""
        self.tabs.setCurrentIndex(1)  # Help tab is at index 1

if __name__ == "__main__":
    app = qt.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
