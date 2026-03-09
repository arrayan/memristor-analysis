import multiprocessing
import sys
import os
import argparse
import PySide6.QtWidgets as qt
from src.app.ui import MainWindow

if __package__ is None:
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def main():
    multiprocessing.freeze_support()
    # Smoke Test
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    args, unknown = parser.parse_known_args()

    app = qt.QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    if args.smoke_test:
        print("Smoke test: UI initialized successfully. Exiting.")
        sys.exit(0)  # Exit before app.exec()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
