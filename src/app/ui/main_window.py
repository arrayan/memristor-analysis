import PySide6.QtWidgets as qt
from .menu_bar import MenuBar
from .navigation_bar import NavigationBar
from core import MenuAction, Mode
from converter import BatchConverter, path_to_glob

class MainWindow(qt.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Memristor Analysis Tool")
        self.resize(1200, 800)

        self.setup_ui()        
        self.setup_connections()

    def setup_ui(self) -> None:
        """Initializes the layout."""
        # 1. Menu Bar
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        # 2. Central Widget
        central_widget = qt.QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = qt.QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # 3. Add the Unified Navigation/Tab Bar
        # This now contains the dropdown AND the tabs on one line
        self.nav_bar = NavigationBar()
        self.main_layout.addWidget(self.nav_bar)

    def setup_connections(self):
        """Connects Menu signals to the active tab."""
        menu_actions = self.menu_bar.menu_actions

        # File Actions
        menu_actions[MenuAction.EXIT].triggered.connect(self.close)
        menu_actions[MenuAction.IMPORT_DEVICE].triggered.connect(
            lambda: self.handle_import(mode=Mode.DEVICE)
        )
        menu_actions[MenuAction.IMPORT_STACK].triggered.connect(
            lambda: self.handle_import(mode=Mode.STACK)
        )

        # Scaling/Export (Applies to the currently visible tab)
        menu_actions[MenuAction.SCALE_LINEAR].triggered.connect(
            lambda: self.apply_to_active(lambda v: v.set_scale("linear"))
        )
        menu_actions[MenuAction.SCALE_LOG].triggered.connect(
            lambda: self.apply_to_active(lambda v: v.set_scale("log"))
        )
        menu_actions[MenuAction.EXPORT_CURRENT_PNG].triggered.connect(
            lambda: self.apply_to_active(lambda v: v.export_image())
        )

    def apply_to_active(self, callback):
        """Helper to act on the current visible PlotViewer."""
        viewer = self.nav_bar.get_current_viewer()
        if viewer:
            callback(viewer)

    def handle_import(self, mode: Mode):
        """Handles directory selection and refreshes plots."""
        folder = qt.QFileDialog.getExistingDirectory(self, f"Select {mode.value} Folder")
        if not folder:
            return
        
        try:
            # Conversion Logic
            path = path_to_glob(folder, mode)
            converter = BatchConverter("output.duckdb")
            converter.convert(path)
            
            # Re-trigger the tab builder to reload HTML files with new data
            current_level = self.nav_bar.level_dropdown.currentText()
            self.nav_bar.update_tabs_by_level(current_level)
            
            qt.QMessageBox.information(self, "Import Successful", "Data processed and plots updated.")
        except Exception as e:
            qt.QMessageBox.critical(self, "Error", f"Could not process data: {e}")