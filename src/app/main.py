import sys
from pathlib import Path
import PySide6.QtWidgets as qt
from ui import MainWindow

def main():
    app = qt.QApplication(sys.argv)
    app.setStyle("Fusion")

    CURRENT_DIR = Path(__file__).resolve().parent
    qss_file = CURRENT_DIR / "styles.qss"

    try:
        with open(qss_file, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: styles.qss not found.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()