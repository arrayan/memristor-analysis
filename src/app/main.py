import sys
import os
import PySide6.QtWidgets as qt
from src.app.ui import MainWindow

if __package__ is None:
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def main():
    app = qt.QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
