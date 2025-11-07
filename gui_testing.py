import PySide6.QtWidgets as qt
import sys

class MainWindow(qt.QMainWindow):
    def __init__ (self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        window_title = qt.QLabel("Analysis here")

        layout = qt.QVBoxLayout()

        layout.addWidget(window_title)

        central_widget = qt.QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

        self.setWindowTitle("MemResistor Analysis Tool")
        self.resize(400, 200)

if __name__ == "__main__":
    app = qt.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
