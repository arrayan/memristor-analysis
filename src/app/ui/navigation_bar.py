from pathlib import Path
import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt
from .plot_viewer import PlotViewer
from ..core import Mode 

class NavigationBar(qt.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Resolve paths to temp folders
        self.temp_root = Path(__file__).parent.parent / "temp"
        self.temp_device_dir = self.temp_root / "device"
        self.temp_stack_dir = self.temp_root / "stack"
        
        # Ensure directories exist
        self.temp_device_dir.mkdir(parents=True, exist_ok=True)
        self.temp_stack_dir.mkdir(parents=True, exist_ok=True)

        self.show_welcome_screen()

    def is_folder_empty(self, directory: Path):
        """Checks if a directory exists and contains any HTML files."""
        if not directory.exists():
            return True
        # Check recursively if any .html files exist in any subfolders
        return len(list(directory.rglob("*.html"))) == 0

    def show_welcome_screen(self):
        """Displays the startup information tab or 'Continue' buttons."""
        self.clear()

        welcome_widget = qt.QWidget()
        layout = qt.QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        device_data_exists = not self.is_folder_empty(self.temp_device_dir)
        stack_data_exists = not self.is_folder_empty(self.temp_stack_dir)

        if not device_data_exists and not stack_data_exists:
            # Scenario A: No data at all
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
            # Scenario B: Existing data found
            title = qt.QLabel("Existing analysis data found.")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ccc;")
            layout.addStretch()
            layout.addWidget(title, alignment=Qt.AlignCenter)

            if device_data_exists:
                # We import Mode locally here if needed, or use strings if you prefer
                dev_btn = qt.QPushButton("Continue Device Level Analysis")
                dev_btn.setFixedSize(300, 45)
                dev_btn.clicked.connect(lambda: self.show_analysis(Mode.DEVICE))
                layout.addWidget(dev_btn, alignment=Qt.AlignCenter)

            if stack_data_exists:                
                stack_btn = qt.QPushButton("Continue Stack Level Analysis")
                stack_btn.setFixedSize(300, 45)
                stack_btn.clicked.connect(lambda: self.show_analysis(Mode.STACK))
                layout.addWidget(stack_btn, alignment=Qt.AlignCenter)

            layout.addStretch()

        self.addTab(welcome_widget, "Start")

    def show_analysis(self, mode):
        """
        Clears the tabs and populates them based on the analysis mode.
        This is called by MainWindow.on_import_success.
        """
         # Local import to avoid circular dependencies
        self.clear()

        if mode == Mode.DEVICE:
            # Labels mapping for filenames
            param_labels = {
                "V_set": "V Set", "V_reset": "V Reset",
                "R_LRS": "R LRS", "R_HRS": "R HRS",
                "I_LRS": "I LRS", "I_HRS": "I HRS",
                "I_reset_max": "I Reset Max", "Memory_window": "Memory Window",
                "VSET": "V Set", "V_forming": "V Forming",
            }

            char_labels = {"AI": "Current (A)", "NORM_COND": "Conductance (S)"}

            corr_labels = {
                "V_set_vs_I_HRS": "Vset vs IHRS", "V_set_vs_R_HRS": "Vset vs RHRS",
                "V_reset_vs_I_LRS": "Vreset vs ILRS", "V_reset_vs_R_LRS": "Vreset vs RLRS",
                "V_reset_vs_I_reset_max": "Vreset vs Ireset", "V_set_vs_V_reset": "Vset vs Vreset",
            }

            # Build the nested tab groups for Device level
            self.addTab(self._create_nested_tab(self.temp_device_dir, "endurance_performance", param_labels), "Endurance Performance")
            self.addTab(self._create_nested_tab(self.temp_device_dir, "boxplots", param_labels), "Endurance Boxplots")
            self.addTab(self._create_nested_tab(self.temp_device_dir, "cdfs", param_labels), "Endurance CDF")
            self.addTab(self._create_nested_tab(self.temp_device_dir, "characteristic_plots", char_labels), "Characteristic Plots")
            self.addTab(self._create_nested_tab(self.temp_device_dir, "correlation_plots", corr_labels), "Device Correlation")

        elif mode == Mode.STACK:
            # Build the tabs for Stack level (Placeholder for now)
            viewer = PlotViewer()
            viewer.browser.setHtml(
                "<body style='background:#111; color:#eee; display:flex; justify-content:center; "
                "align-items:center; height:100vh; font-family:sans-serif;'>"
                "<h1>Stack Level Analysis: Under Construction</h1></body>"
            )
            self.addTab(viewer, "Stack Overview")

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
                "align-items:center; height:100vh; font-family:sans-serif;'><div>No data available in "
                f"{subfolder_name}.</div></body>"
            )
            sub_tab_widget.addTab(viewer, "Empty")

        return sub_tab_widget

    def get_current_viewer(self) -> PlotViewer:
        """Returns the active PlotViewer even if it is nested inside another TabWidget."""
        widget = self.currentWidget()
        if isinstance(widget, PlotViewer):
            return widget
        if isinstance(widget, qt.QTabWidget):
            sub_widget = widget.currentWidget()
            if isinstance(sub_widget, PlotViewer):
                return sub_widget
        return None

    def get_all_viewers(self) -> list[PlotViewer]:
        """Utility to get all PlotViewers currently instantiated."""
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