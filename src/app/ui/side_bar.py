import PySide6.QtWidgets as qt
from PySide6.QtCore import Qt

class SideBar(qt.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Options", parent)
        self.setFixedWidth(220)
        self.setup_ui()

    def setup_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addWidget(qt.QLabel("Filtering"))
        self.filter_check = qt.QCheckBox("Filter for single graphs")
        layout.addWidget(self.filter_check)

        layout.addWidget(qt.QLabel("Scale Selection"))
        self.check_linear = qt.QCheckBox("Linear")
        self.check_log = qt.QCheckBox("Log")
        
        self.check_linear.setChecked(True)
        self.scale_group = qt.QButtonGroup(self)
        self.scale_group.addButton(self.check_linear)
        self.scale_group.addButton(self.check_log)
        self.scale_group.setExclusive(True)

        layout.addWidget(self.check_linear)
        layout.addWidget(self.check_log)
        layout.addStretch()