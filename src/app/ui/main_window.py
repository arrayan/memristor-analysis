import PySide6.QtWidgets as qt
from PySide6.QtCore import QThread, Qt
from .menu_bar import MenuBar
from .navigation_bar import NavigationBar
from core import MenuAction, Mode
from converter import BatchConverter, path_to_glob
from .import_worker import ImportWorker


class MainWindow(qt.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memristor Analysis Tool")
        self.resize(1200, 800)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self) -> None:
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)
        central_widget = qt.QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = qt.QVBoxLayout(central_widget)
        self.nav_bar = NavigationBar()
        self.main_layout.addWidget(self.nav_bar)

    def setup_connections(self):
        menu_actions = self.menu_bar.menu_actions

        # Connect Imports (Shortcuts and Menu)
        menu_actions[MenuAction.IMPORT_DEVICE].triggered.connect(
            lambda: self.handle_import(mode=Mode.DEVICE)
        )
        menu_actions[MenuAction.IMPORT_STACK].triggered.connect(
            lambda: self.handle_import(mode=Mode.STACK)
        )

        # Plot Controls
        menu_actions[MenuAction.SCALE_LINEAR].triggered.connect(
            lambda: self.apply_to_active(lambda v: v.set_scale("linear"))
        )
        menu_actions[MenuAction.SCALE_LOG].triggered.connect(
            lambda: self.apply_to_active(lambda v: v.set_scale("log"))
        )

    def handle_import(self, mode: Mode):
        folder = qt.QFileDialog.getExistingDirectory(
            self, f"Select {mode.value} Folder"
        )
        if not folder:
            return

        path = path_to_glob(folder, mode)

        # 1. Create Progress Dialog
        self.pd = qt.QProgressDialog("Initializing...", None, 0, 100, self)
        self.pd.setWindowTitle("Processing Data")
        self.pd.setWindowModality(Qt.WindowModal)
        self.pd.setMinimumDuration(0)
        self.pd.show()

        # 2. Setup Thread and Worker
        self.import_thread = QThread()
        self.worker = ImportWorker(path, mode, BatchConverter)
        self.worker.moveToThread(self.import_thread)

        # 3. Connect Signals
        self.import_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.pd.setValue)
        self.worker.status_message.connect(self.pd.setLabelText)

        # Clean up thread when finished
        self.worker.finished.connect(self.import_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.import_thread.finished.connect(self.import_thread.deleteLater)

        # UI Refresh on success
        self.worker.finished.connect(self.on_import_success)
        self.worker.error.connect(self.on_import_error)

        # 4. Start
        self.import_thread.start()

    def on_import_success(self):
        self.pd.close()
        # Force the NavigationBar to reload the tabs (which now have new HTML files)
        self.nav_bar.level_dropdown.setCurrentText("Device Level")
        self.nav_bar.update_tabs_by_level("Device Level")
        qt.QMessageBox.information(
            self, "Success", "Data imported and plots generated successfully."
        )

    def on_import_error(self, err_msg):
        self.pd.close()
        qt.QMessageBox.critical(
            self, "Error", f"An error occurred during processing:\n{err_msg}"
        )

    def apply_to_active(self, callback):
        viewer = self.nav_bar.get_current_viewer()
        if viewer:
            callback(viewer)
