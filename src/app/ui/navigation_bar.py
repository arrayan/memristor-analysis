from pathlib import Path
import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt
from .plot_viewer import PlotViewer


class NavigationBar(qt.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.temp_root = Path(__file__).parent.parent / "temp"
        self.temp_device_dir = self.temp_root / "device"
        self.temp_stack_dir = self.temp_root / "stack"

        self.temp_device_dir.mkdir(parents=True, exist_ok=True)
        self.temp_stack_dir.mkdir(parents=True, exist_ok=True)

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

        self.level_dropdown.activated.connect(self.handle_dropdown_change)

        self.corner_layout.addWidget(level_label)
        self.corner_layout.addWidget(self.level_dropdown)
        self.setCornerWidget(self.corner_container, Qt.TopLeftCorner)

    def is_folder_empty(self, directory: Path):
        """Checks if a directory exists and contains any HTML files."""
        if not directory.exists():
            return True
        return len(list(directory.rglob("*.html"))) == 0

    def show_welcome_screen(self):
        """Displays the startup information tab."""
        self.clear()

        welcome_widget = qt.QWidget()
        layout = qt.QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        device_data_exists = not self.is_folder_empty(self.temp_device_dir)
        stack_data_exists = not self.is_folder_empty(self.temp_stack_dir)

        if not device_data_exists and not stack_data_exists:
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
            title = qt.QLabel("Existing analysis data found.")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ccc;")
            layout.addStretch()
            layout.addWidget(title, alignment=Qt.AlignCenter)

            if device_data_exists:
                dev_btn = qt.QPushButton("Continue Device Level Analysis")
                dev_btn.setFixedSize(300, 45)
                dev_btn.clicked.connect(
                    lambda: self.update_tabs_by_level("Device Level")
                )
                layout.addWidget(dev_btn, alignment=Qt.AlignCenter)

            if stack_data_exists:
                stack_btn = qt.QPushButton("Continue Stack Level Analysis")
                stack_btn.setFixedSize(300, 45)
                stack_btn.clicked.connect(
                    lambda: self.update_tabs_by_level("Stack Level")
                )
                layout.addWidget(stack_btn, alignment=Qt.AlignCenter)

            layout.addStretch()

        self.addTab(welcome_widget, "Start")

    def handle_dropdown_change(self):
        self.update_tabs_by_level(self.level_dropdown.currentText())

    def update_tabs_by_level(self, level_text):
        self.clear()

        param_labels = {
            "V_set": "V Set",
            "V_reset": "V Reset",
            "R_LRS": "R LRS",
            "R_HRS": "R HRS",
            "I_LRS": "I LRS",
            "I_HRS": "I HRS",
            "I_reset_max": "I Reset Max",
            "Memory_window": "Memory Window",
            "VSET": "V Set",
            "V_forming": "V Forming",
        }

        corr_labels = {
            "V_set_vs_I_HRS": "Vset vs IHRS",
            "V_set_vs_R_HRS": "Vset vs RHRS",
            "V_reset_vs_I_LRS": "Vreset vs ILRS",
            "V_reset_vs_R_LRS": "Vreset vs RLRS",
            "V_reset_vs_I_reset_max": "Vreset vs Ireset",
            "V_set_vs_V_reset": "Vset vs Vreset",
        }

        if level_text == "Device Level":
            base_dir = self.temp_device_dir

            char_labels = {"AI": "Current (A)", "NORM_COND": "Conductance (S)"}

            self.addTab(
                self._create_nested_tab(base_dir, "endurance_performance", param_labels),
                "Endurance Performance",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "boxplots", param_labels),
                "Endurance Boxplots",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "cdfs", param_labels),
                "Endurance CDF",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "characteristic_plots", char_labels),
                "Characteristic Plots",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "correlation_plots", corr_labels),
                "Device Corr. Scatter",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "correlation_matrices", self._discover_labels(base_dir / "correlation_matrices")),
                "Device Matrix",
            )

        elif level_text == "Stack Level":
            base_dir = self.temp_stack_dir

            char_labels = {
                "AI": "Current (A)",
                "NORM_COND": "Conductance (S)",
                "butterfly_curve": "Butterfly",
            }

            self.addTab(
                self._create_nested_tab(base_dir, "characteristic_plots", char_labels),
                "Char. Plots",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "endurance_performance", param_labels),
                "Endurance",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "boxplots", param_labels),
                "Boxplots",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "boxplots_stack_level", param_labels),
                "Stack Boxplots",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "cdfs", param_labels),
                "CDF",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "cdfs_stack_level", param_labels),
                "Stack CDF",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "correlation_plots", corr_labels),
                "Corr. Scatter",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "correlation_plots_stack_level", corr_labels),
                "Stack Corr. Scatter",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "correlation_matrices", self._discover_labels(base_dir / "correlation_matrices")),
                "Matrix",
            )
            self.addTab(
                self._create_nested_tab(base_dir, "correlation_matrices_stack_level", self._discover_labels(base_dir / "correlation_matrices_stack_level")),
                "Stack Matrix",
            )

    def _discover_labels(self, folder: Path) -> dict:
        """Auto-discover HTML files in a folder and build a labels map from filenames."""
        if not folder.exists():
            return {}
        return {
            f.stem: f.stem.replace("corr_matrix_", "").replace("_", " ")
            for f in sorted(folder.glob("*.html"))
        }

    def _create_nested_tab(self, base_dir: Path, subfolder_name: str, labels_map: dict):
        """Helper to create a QTabWidget from a subfolder of HTML files."""
        sub_tab_widget = qt.QTabWidget()
        folder_path = base_dir / subfolder_name

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
                "<body style='background:#111; color:#555; display:flex; justify-content:center; "
                "align-items:center; height:100vh; font-family:sans-serif;'>"
                f"<div>No data available in {subfolder_name}.</div></body>"
            )
            sub_tab_widget.addTab(viewer, "Empty")

        return sub_tab_widget

    def get_current_viewer(self) -> PlotViewer:
        """Returns the active PlotViewer even if nested inside another TabWidget."""
        widget = self.currentWidget()
        if isinstance(widget, PlotViewer):
            return widget
        if isinstance(widget, qt.QTabWidget):
            sub_widget = widget.currentWidget()
            if isinstance(sub_widget, PlotViewer):
                return sub_widget
        return None

    def get_all_viewers(self) -> list[PlotViewer]:
        """Returns all PlotViewers currently instantiated."""
        viewers = []
        for i in range(self.count()):
            widget = self.widget(i)
            if isinstance(widget, PlotViewer):
                viewers.append(widget)
            elif isinstance(widget, qt.QTabWidget):
                for j in range(widget.count()):
                    sub_widget = widget.widget(j)
                    if isinstance(sub_widget, PlotViewer):
                        viewers.append(sub_widget)
        return viewers