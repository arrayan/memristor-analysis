import os
from pathlib import Path
import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt
from .plot_viewer import PlotViewer

class NavigationBar(qt.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Resolve the path to src/app/temp/device
        self.temp_device_dir = Path(__file__).parent.parent / "temp" / "device"
        self.temp_device_dir.mkdir(parents=True, exist_ok=True)

        self.setup_ui()
        self.show_welcome_screen()

    def setup_ui(self):
        """Sets up the dropdown in the corner."""
        self.corner_container = qt.QWidget()
        self.corner_layout = qt.QHBoxLayout(self.corner_container)
        self.corner_layout.setContentsMargins(10, 2, 20, 2)
        
        level_label = qt.QLabel("Analysis Level:")
        self.level_dropdown = qt.QComboBox()
        self.level_dropdown.addItems(["Device Level", "Stack Level"])
        self.level_dropdown.setFixedWidth(150)
        
        # Only switch tabs when user explicitly picks a level
        self.level_dropdown.activated.connect(self.handle_dropdown_change)
        
        self.corner_layout.addWidget(level_label)
        self.corner_layout.addWidget(self.level_dropdown)
        self.setCornerWidget(self.corner_container, Qt.TopLeftCorner)

    def is_device_folder_empty(self):
        """Checks for HTML files in temp folder."""
        if not self.temp_device_dir.exists():
            return True
        return len(list(self.temp_device_dir.glob("*.html"))) == 0

    def show_welcome_screen(self):
        """Displays the startup information tab."""
        self.clear()
        
        welcome_widget = qt.QWidget()
        layout = qt.QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        if self.is_device_folder_empty():
            # Scenario A: Folder is empty
            title = qt.QLabel("Please import data to start the analysis.")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ccc;")
            
            instructions = qt.QLabel(
                "Use the File menu or the following shortcuts:\n\n"
                "• Ctrl+O : Import Device Data\n"
                "• Ctrl+Shift+O : Import Stack Data"
            )
            instructions.setAlignment(Qt.AlignCenter)
            instructions.setStyleSheet("font-size: 14px; color: #888; line-height: 150%;")
            
            layout.addStretch()
            layout.addWidget(title, alignment=Qt.AlignCenter)
            layout.addWidget(instructions, alignment=Qt.AlignCenter)
            layout.addStretch()
        else:
            # Scenario B: Folder has data
            title = qt.QLabel("Existing analysis data found.")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ccc;")
            
            continue_btn = qt.QPushButton("Continue with last analysis")
            continue_btn.setFixedWidth(250)
            continue_btn.setFixedHeight(40)
            continue_btn.clicked.connect(lambda: self.update_tabs_by_level("Device Level"))
            
            layout.addStretch()
            layout.addWidget(title, alignment=Qt.AlignCenter)
            layout.addWidget(continue_btn, alignment=Qt.AlignCenter)
            layout.addStretch()

        self.addTab(welcome_widget, "Start")

    def handle_dropdown_change(self):
        self.update_tabs_by_level(self.level_dropdown.currentText())

    def update_tabs_by_level(self, level_text):
        self.clear()

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
                file_path = self.temp_device_dir / filename
                
                if file_path.exists():
                    viewer.load_html_file(str(file_path))
                else:
                    viewer.browser.setHtml(f"<body style='background:#111; color:#555; display:flex; "
                                           f"justify-content:center; align-items:center; height:100vh; "
                                           f"font-family:sans-serif;'><div>File {filename} not yet generated.</div></body>")
                self.addTab(viewer, label)

        elif level_text == "Stack Level":
            viewer = PlotViewer()
            viewer.browser.setHtml("<body style='background:#111; color:#eee; display:flex; justify-content:center; "
                                   "align-items:center; height:100vh; font-family:sans-serif;'>"
                                   "<h1>Stack Level: Currently under construction</h1></body>")
            self.addTab(viewer, "Status")

    def get_current_viewer(self) -> PlotViewer:
        # Check if the current widget is actually a PlotViewer (not the Start widget)
        widget = self.currentWidget()
        return widget if isinstance(widget, PlotViewer) else None