import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt

from .side_bar import OptionsSidebar
from .navigation_bar import NavigationBar
from .action_bar import ActionBar

class MainWindow(qt.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memristor Analysis Tool")
        self.resize(1200, 800)

        self.setup_menu_bar()

        # Central Layout
        central_widget = qt.QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = qt.QVBoxLayout(central_widget)

        # Add Navigation Row
        self.nav_bar = NavigationBar()
        self.main_layout.addLayout(self.nav_bar)

        # Body Layout
        body_layout = qt.QHBoxLayout()
        
        # Plot Area
        self.plot_area = qt.QFrame()
        self.plot_area.setStyleSheet("background-color: #000; border: 2px solid #444;")
        plot_layout = qt.QVBoxLayout(self.plot_area)
        plot_layout.addWidget(qt.QLabel("Plot Canvas Area", alignment=Qt.AlignmentFlag.AlignCenter))

        # Sidebar
        self.sidebar = OptionsSidebar()

        body_layout.addWidget(self.plot_area, stretch=4)
        body_layout.addWidget(self.sidebar, stretch=1)
        
        self.main_layout.addLayout(body_layout)

    def setup_menu_bar(self):
        bar = self.menuBar()
        file_menu = bar.addMenu("File")
        file_menu.addAction("Import Device")
        file_menu.addAction("Import Stack")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        help_menu = bar.addMenu("Help")
        help_menu.addAction("View Help")