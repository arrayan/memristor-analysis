import sys
import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt

# Custom ToggleSwitch is no longer needed based on requirements

class MainWindow(qt.QMainWindow):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.setWindowTitle("Memristor Analysis Tool")
        
        self.resize(1200, 800) 
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        # 1. Action Bar (Top Menu)
        self.setup_menu_bar()

        # Main Central Widget
        central_widget = qt.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = qt.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 2. Navigation Row (Level Dropdown + Plot Bar)
        nav_row = qt.QHBoxLayout()
        
        # Level Selection Container
        level_container = qt.QFrame()
        level_container.setStyleSheet("background-color: #333; border: 1px solid #555; border-radius: 3px;")
        level_layout = qt.QHBoxLayout(level_container)
        level_layout.setContentsMargins(15, 5, 15, 5)
        level_layout.setSpacing(10)

        # --- UPDATED: DROPDOWN MENU ---
        level_label = qt.QLabel("Analysis Level:")
        level_label.setStyleSheet("font-weight: bold; border: none;")
        
        self.level_dropdown = qt.QComboBox()
        self.level_dropdown.addItems(["Device Level", "Stack Level"])
        self.level_dropdown.setFixedWidth(150)
        # Styling the dropdown for dark mode
        self.level_dropdown.setStyleSheet("""
            QComboBox { 
                background-color: #444; 
                color: white; 
                border: 1px solid #666; 
                padding: 2px 5px; 
            }
            QComboBox QAbstractItemView { 
                background-color: #333; 
                color: white; 
                selection-background-color: #FF9500; 
            }
        """)
        
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_dropdown)
        
        # Connect Dropdown Logic
        def on_level_change(text):
            print(f"Analysis Mode: {text}")

        self.level_dropdown.currentTextChanged.connect(on_level_change)
        
        # Plot Bar Section (Buttons)
        plot_bar = qt.QFrame()
        plot_bar.setStyleSheet("background-color: #333; border: 1px solid #555; border-radius: 3px;")
        plot_bar_layout = qt.QHBoxLayout(plot_bar)
        plot_bar_layout.setContentsMargins(5, 2, 5, 2)
        
        btn_plot1 = qt.QPushButton("Plot Current")
        btn_plot2 = qt.QPushButton("Plot Voltage")
        btn_plot1.setFixedWidth(100)
        btn_plot2.setFixedWidth(100)
        
        plot_bar_layout.addWidget(btn_plot1)
        plot_bar_layout.addWidget(btn_plot2)
        plot_bar_layout.addStretch()

        nav_row.addWidget(level_container) 
        nav_row.addWidget(plot_bar)
        
        main_layout.addLayout(nav_row)

        # 3. Main Body (Plot Area + Options Sidebar)
        body_layout = qt.QHBoxLayout()

        # Plot Canvas Placeholder
        self.plot_area = qt.QFrame()
        self.plot_area.setStyleSheet("background-color: #000; border: 2px solid #444; border-radius: 5px;")
        plot_layout = qt.QVBoxLayout(self.plot_area)
        plot_placeholder_label = qt.QLabel("Plot Canvas Area")
        plot_placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plot_layout.addWidget(plot_placeholder_label)

        # Options Sidebar
        options_sidebar = self.setup_options_sidebar()

        body_layout.addWidget(self.plot_area, stretch=4)
        body_layout.addWidget(options_sidebar, stretch=1)
        
        main_layout.addLayout(body_layout)

    def setup_menu_bar(self):
        bar = self.menuBar()
        bar.setStyleSheet("background-color: #333; color: white;")

        # File Menu
        file_menu = bar.addMenu("File")
        file_menu.addAction("Import Device")
        file_menu.addAction("Import Stack")
        file_menu.addSeparator()
        file_menu.addAction("Export All") 
        file_menu.addAction("Exit", self.close)
        
        # Help Menu
        help_menu = bar.addMenu("Help")
        help_menu.addAction("View Help")

    def setup_options_sidebar(self):
        container = qt.QGroupBox("Options")
        container.setFixedWidth(220)
        container.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
        """)
        
        layout = qt.QVBoxLayout(container)
        layout.setSpacing(15)

        layout.addWidget(qt.QLabel("Filtering"))
        self.filter_check = qt.QCheckBox("Filter for single graphs")
        layout.addWidget(self.filter_check)

        # --- UPDATED: EXCLUSIVE CHECKBOXES FOR SCALE ---
        layout.addWidget(qt.QLabel("Scale Selection"))
        
        self.check_linear = qt.QCheckBox("Linear")
        self.check_log = qt.QCheckBox("Log")
        
        # Default state
        self.check_linear.setChecked(True)

        # Use QButtonGroup to make them exclusive (only one can be checked)
        self.scale_group = qt.QButtonGroup(self)
        self.scale_group.addButton(self.check_linear)
        self.scale_group.addButton(self.check_log)
        self.scale_group.setExclusive(True)

        layout.addWidget(self.check_linear)
        layout.addWidget(self.check_log)

        # Signal handling
        self.scale_group.buttonClicked.connect(lambda b: print(f"Scale set to: {b.text()}"))

        layout.addStretch()
        return container


if __name__ == "__main__":
    app = qt.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())