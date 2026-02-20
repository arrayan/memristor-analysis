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
            instructions.setStyleSheet(
                "font-size: 14px; color: #888; line-height: 150%;"
            )

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
            continue_btn.clicked.connect(
                lambda: self.update_tabs_by_level("Device Level")
            )

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
            # 1. Standard Tabs
            viewer = PlotViewer()
            if (self.temp_device_dir / "endurance_performance.html").exists():
                viewer.load_html_file(str(self.temp_device_dir / "endurance_performance.html"))
            self.addTab(viewer, "Endurance Performance")

            # 2. Parameter Definitions for Nested Tabs
            param_labels = {
                "VSET": "V_set (V)", "V_reset": "V_reset (V)",
                "R_LRS": "R_LRS (Ω)", "R_HRS": "R_HRS (Ω)",
                "I_reset_max": "I_reset_max (A)", "V_forming": "V_forming (V)",
            }
            
            char_labels = {"AI": "Current (A)", "NORM_COND": "Conductance (S)"}

            # Map for Correlation Pairs
            corr_labels = {
                "V_set_vs_I_HRS": "Vset vs IHRS",
                "V_set_vs_R_HRS": "Vset vs RHRS",
                "V_reset_vs_I_LRS": "Vreset vs ILRS",
                "V_reset_vs_R_LRS": "Vreset vs RLRS",
                "V_reset_vs_I_reset_max": "Vreset vs Ireset",
                "V_set_vs_V_reset": "Vset vs Vreset",
            }

            # 3. Create All Nested Tab Groups
            self.addTab(self._create_nested_tab("boxplots", param_labels), "Endurance Boxplots")
            self.addTab(self._create_nested_tab("cdfs", param_labels), "Endurance CDF")
            self.addTab(self._create_nested_tab("characteristic_plots", char_labels), "Characteristic Plots")
            self.addTab(self._create_nested_tab("correlation_plots", corr_labels), "Device Correlation")

    def _create_nested_tab(self, subfolder_name, labels_map):
        """Helper to create a QTabWidget from a subfolder of HTML files."""
        sub_tab_widget = qt.QTabWidget()
        folder_path = self.temp_device_dir / subfolder_name

        found_any = False
        for param_id, label in labels_map.items():
            file_path = folder_path / f"{param_id}.html"
            if file_path.exists():
                viewer = PlotViewer()
                viewer.load_html_file(str(file_path))
                sub_tab_widget.addTab(viewer, label)
                found_any = True

        if not found_any:
            # Fallback if folder is empty or files missing
            viewer = PlotViewer()
            viewer.browser.setHtml(
                "<body style='background:#111; color:#555; display:flex; justify-content:center; align-items:center; height:100vh;'><div>No data available.</div></body>"
            )
            sub_tab_widget.addTab(viewer, "Empty")

        return sub_tab_widget

    def _create_nested_tab(self, subfolder_name, labels_map):
        """Helper to create a QTabWidget from a subfolder of HTML files."""
        sub_tab_widget = qt.QTabWidget()
        folder_path = self.temp_device_dir / subfolder_name

        found_any = False
        for param_id, label in labels_map.items():
            file_path = folder_path / f"{param_id}.html"
            if file_path.exists():
                viewer = PlotViewer()
                viewer.load_html_file(str(file_path))
                sub_tab_widget.addTab(viewer, label)
                found_any = True

        if not found_any:
            viewer = PlotViewer()
            viewer.browser.setHtml(
                "<body style='background:#111; color:#555;'><div>No data.</div></body>"
            )
            sub_tab_widget.addTab(viewer, "Empty")

        return sub_tab_widget

    def _set_missing_file_msg(self, viewer, filename):
        """Helper to set error message in browser."""
        viewer.browser.setHtml(
            f"<body style='background:#111; color:#555; display:flex; "
            f"justify-content:center; align-items:center; height:100vh; "
            f"font-family:sans-serif;'><div>File {filename} not yet generated.</div></body>"
        )

    def get_current_viewer(self) -> PlotViewer:
        widget = self.currentWidget()

        # If it's a direct PlotViewer (e.g., Endurance Performance)
        if isinstance(widget, PlotViewer):
            return widget

        # If it's the nested TabWidget (Boxplots)
        if isinstance(widget, qt.QTabWidget):
            sub_widget = widget.currentWidget()
            if isinstance(sub_widget, PlotViewer):
                return sub_widget

        return None
