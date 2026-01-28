import sys
import PySide6.QtWidgets as qt
from ui.main_window import MainWindow

def main():
    app = qt.QApplication(sys.argv)
    app.setStyle("Fusion")

    # Load External Stylesheet
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