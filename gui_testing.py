import sys
import PySide6.QtWidgets as qt
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

class MainWindow(qt.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Central layout
        window_title = qt.QLabel("Analysis here")
        window_title.setAlignment(Qt.AlignCenter)

        layout = qt.QVBoxLayout()
        layout.addWidget(window_title)

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

        layout.addWidget(import_panel)

        central_widget = qt.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        import_action = QAction("Import", self)
        import_action.triggered.connect(self.browse_file)  # Menu also opens dialog
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(import_action)
        file_menu.addAction(exit_action)

        self.setWindowTitle("MemResistor Analysis Tool")
        self.resize(500, 200)

    def browse_file(self):
        file_path, _ = qt.QFileDialog.getOpenFileName(self, "Select file")
        if file_path:
            self.import_path_label.setText(file_path)  # Show chosen file

if __name__ == "__main__":
    app = qt.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
