import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt

class NavigationBar(qt.QHBoxLayout):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Level Selection
        level_container = qt.QFrame()
        level_container.setObjectName("NavContainer")
        level_layout = qt.QHBoxLayout(level_container)
        
        level_label = qt.QLabel("Analysis Level:")
        self.level_dropdown = qt.QComboBox()
        self.level_dropdown.addItems(["Device Level", "Stack Level"])
        self.level_dropdown.setFixedWidth(150)
        
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_dropdown)

        # Plot Buttons Section
        plot_bar = qt.QFrame()
        plot_bar.setObjectName("NavContainer")
        plot_bar_layout = qt.QHBoxLayout(plot_bar)
        
        self.btn_plot_current = qt.QPushButton("Plot Current")
        self.btn_plot_voltage = qt.QPushButton("Plot Voltage")
        
        plot_bar_layout.addWidget(self.btn_plot_current)
        plot_bar_layout.addWidget(self.btn_plot_voltage)
        plot_bar_layout.addStretch()

        self.addWidget(level_container)
        self.addWidget(plot_bar)