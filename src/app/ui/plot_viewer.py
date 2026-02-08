from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget, QCheckBox, QHBoxLayout, QPushButton, QFileDialog
import plotly.io as pio

class PlotViewer(QWidget):
    def __init__(self, figure=None):
        super().__init__()
        self.figure = figure
        self.main_layout = QVBoxLayout(self)

        # 1. The Browser
        self.browser = QWebEngineView()
        
        # 2. Controls (Log Scale & Export)
        controls = QHBoxLayout()
        self.log_checkbox = QCheckBox("Log Scale")
        self.log_checkbox.stateChanged.connect(self.update_scale)
        
        export_btn = QPushButton("Export PNG")
        export_btn.clicked.connect(self.export_image)
        
        controls.addWidget(self.log_checkbox)
        controls.addStretch()
        controls.addWidget(export_btn)

        self.main_layout.addLayout(controls)
        self.main_layout.addWidget(self.browser)

        if figure:
            self.render_plot()

    def render_plot(self):
        # 1. This "if" statement tells Pylance (and Python) 
        # that we only proceed if self.figure exists.
        if self.figure is not None:
            html = self.figure.to_html(include_plotlyjs='cdn', full_html=False)
            self.browser.setHtml(html)
        else:
            # Optional: Clear the browser or show a "No Data" message
            self.browser.setHtml("<html><body><p>No plot data available.</p></body></html>")

    def update_scale(self):
        if not self.figure: return
        scale = "log" if self.log_checkbox.isChecked() else "linear"
        self.figure.update_layout(yaxis_type=scale)
        self.render_plot()

    def export_image(self):
        # 1. This check tells Pylance: "If we get past this line, self.figure is NOT None"
        if self.figure is None:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG (*.png);;JPG (*.jpg);;PDF (*.pdf)")
        
        if path:
            # Pylance now knows write_image is safe to call
            self.figure.write_image(path)