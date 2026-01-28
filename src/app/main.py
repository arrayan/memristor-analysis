import sys
import PySide6.QtWidgets as qt
from ui import MainWindow

def main():
    app = qt.QApplication(sys.argv)
    app.setStyle("Fusion")

    try:
        with open("styles.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: styles.qss not found.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()