import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt
from .navigation_bar import NavigationBar
from .menu_bar import MenuBar
from core import MenuActions
from converter import BatchConverter, path_to_glob
from pathlib import Path
import subprocess

class MainWindow(qt.QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize Window
        self.setWindowTitle("Memristor Analysis Tool")
        self.resize(1200, 800)

        # Build UI
        self.setup_ui()        

        # Connect Buttons
        self.setup_connections()

        
        
    def setup_ui(self) -> None:
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Central Layout
        central_widget = qt.QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = qt.QVBoxLayout(central_widget)

        # Add Navigation Row
        self.nav_bar = NavigationBar()
        self.main_layout.addLayout(self.nav_bar, stretch=0)

        
        
        # Plot Area
        self.plot_area = qt.QFrame()
        self.plot_area.setStyleSheet("background-color: #000; border: 2px solid #444;")
        plot_layout = qt.QVBoxLayout(self.plot_area)
        plot_layout.addWidget(qt.QLabel("Plot Canvas Area", alignment=Qt.AlignmentFlag.AlignCenter))

        self.main_layout.addWidget(self.plot_area, stretch=1)

    def setup_connections(self):
        menu_actions = self.menu_bar.menu_actions

        menu_actions[MenuActions.EXIT].triggered.connect(self.close)

        menu_actions[MenuActions.IMPORT_DEVICE].triggered.connect(
            lambda: self.handle_import(mode="device")
        )
        menu_actions[MenuActions.IMPORT_STACK].triggered.connect(
            lambda: self.handle_import(mode="stack")
        )

    def handle_import(self, mode: str): # TODO connect to converter
        # Set Window Title
        title = f"Select {mode.capitalize} Folder"

        # Get path to import directory
        folder = qt.QFileDialog.getExistingDirectory(self, title)

        # If User presses "Cancel"
        if not folder:
            return
        
        path = path_to_glob(folder)
        
        # Set up Converter
        converter = BatchConverter("output.duckdb")

        #
        if mode == "device":
            # Find all Excel files recursively in the device folder
            converter.convert(path)

        elif mode == "stack":
            # Stack import also uses recursive glob pattern
            converter.convert(path) 
