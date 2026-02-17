import sys
import PySide6.QtWidgets as qt
from .ui import MainWindow


def main():
    app = qt.QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
