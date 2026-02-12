from pathlib import Path
import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt
from .plot_viewer import PlotViewer

class NavigationBar(qt.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        # Initial population of tabs
        self.update_tabs_by_level("Device Level")

    def setup_ui(self):
        """Sets up the dropdown in the corner of the tab row."""
        # 1. Create a container for the 'Analysis Level' label and dropdown
        self.corner_container = qt.QWidget()
        self.corner_layout = qt.QHBoxLayout(self.corner_container)
        self.corner_layout.setContentsMargins(10, 2, 20, 2) # Padding for the row
        
        level_label = qt.QLabel("Analysis Level:")
        self.level_dropdown = qt.QComboBox()
        self.level_dropdown.addItems(["Device Level", "Stack Level"])
        self.level_dropdown.setFixedWidth(150)
        self.level_dropdown.currentTextChanged.connect(self.update_tabs_by_level)
        
        self.corner_layout.addWidget(level_label)
        self.corner_layout.addWidget(self.level_dropdown)

        # 2. Key Step: Move this container into the Tab Bar's row
        self.setCornerWidget(self.corner_container, Qt.TopLeftCorner)

        # 3. Tab Bar Styling
        self.setTabsClosable(False)
        self.setMovable(False)
        # Optional: Make tabs look cleaner
        self.setStyleSheet("QTabBar::tab { height: 30px; padding: 0 20px; }")

    def update_tabs_by_level(self, level_text):
        """Switches the fixed set of tabs based on selection."""
        self.clear()
        root_dir = Path.cwd()

        if level_text == "Device Level":
            device_tabs = {
                "Endurance Performance": "endurance_performance.html",
                "Endurance CDF": "endurance_cdf.html",
                "Endurance Boxplots": "endurance_boxplots.html",
                "Characteristic Plots": "characteristic_plots.html",
                "Device Correlation": "device_correlation_scatter.html"
            }
            
            for label, filename in device_tabs.items():
                viewer = PlotViewer()
                file_path = root_dir / filename
                
                if file_path.exists():
                    viewer.load_html_file(str(file_path))
                else:
                    viewer.browser.setHtml(f"<body style='background:#222; color:#888; display:flex; "
                                           f"justify-content:center; align-items:center; height:100vh; "
                                           f"font-family:sans-serif;'><div>File not found: {filename}</div></body>")
                
                self.addTab(viewer, label)

        elif level_text == "Stack Level":
            viewer = PlotViewer()
            viewer.browser.setHtml("<body style='background:#222; color:#eee; display:flex; "
                                   "justify-content:center; align-items:center; height:100vh; "
                                   "font-family:sans-serif;'><h1>Currently under construction</h1></body>")
            self.addTab(viewer, "Status")

    def get_current_viewer(self) -> PlotViewer:
        """Returns the viewer in the active tab."""
        return self.currentWidget()