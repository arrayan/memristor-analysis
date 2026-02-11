import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt
from .menu_bar import MenuBar
from .navigation_bar import NavigationBar
from .plot_viewer import PlotViewer
from core import MenuAction, Mode
from converter import BatchConverter, path_to_glob

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

        self.plot_viewer.load_html_file("C:/Users/pineapple/Desktop/repos/memristor-analysis/characteristic_plots.html")
        
        
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
        self.plot_viewer = PlotViewer()
        self.main_layout.addWidget(self.plot_viewer, stretch=1)

    def setup_connections(self):
        menu_actions = self.menu_bar.menu_actions

        menu_actions[MenuAction.EXIT].triggered.connect(self.close)

        menu_actions[MenuAction.IMPORT_DEVICE].triggered.connect(
            lambda: self.handle_import(mode=Mode.DEVICE)
        )
        menu_actions[MenuAction.IMPORT_STACK].triggered.connect(
            lambda: self.handle_import(mode=Mode.STACK)
        )

        menu_actions[MenuAction.SCALE_LINEAR].triggered.connect(
            lambda: self.plot_viewer.set_scale("linear")
        )
        menu_actions[MenuAction.SCALE_LOG].triggered.connect(
            lambda: self.plot_viewer.set_scale("log")
        )


        # Since your PlotViewer.export_image opens a dialog, 
        # we can connect several actions to the same generic function.
        menu_actions[MenuAction.EXPORT_CURRENT_PNG].triggered.connect(self.plot_viewer.export_image)
        menu_actions[MenuAction.EXPORT_CURRENT_JPEG].triggered.connect(self.plot_viewer.export_image)
        
        # If you want to bypass the dialog and export directly based on the menu click:
        # actions[MenuAction.EXPORT_CURRENT_PNG].triggered.connect(
        #     lambda: self.plot_viewer.figure.write_image("quick_export.png")
        # )

    def handle_import(self, mode: Mode): # TODO connect to converter
        # Set Window Title
        title = f"Select {mode.value.capitalize} Folder"

        # Get path to import directory
        folder = qt.QFileDialog.getExistingDirectory(self, title)

        # If User presses "Cancel"
        if not folder:
            return
        
        path = path_to_glob(folder, mode)
        
        # Set up Converter
        converter = BatchConverter("output.duckdb")
        converter.convert(path)
        
        # if mode == "device":
        #     # Find all Excel files recursively in the device folder
        #     converter.convert(path)

        # elif mode == "stack":
        #     # Stack import also uses recursive glob pattern
        #     converter.convert(path) 
