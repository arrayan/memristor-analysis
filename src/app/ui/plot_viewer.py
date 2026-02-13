from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget, QFileDialog
from PySide6.QtCore import QUrl
import os


class PlotViewer(QWidget):
    def __init__(self, figure=None):
        super().__init__()
        self.figure = figure
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding

        self.browser = QWebEngineView()
        self.main_layout.addWidget(self.browser)

        if figure:
            self.render_plot()

    def render_plot(self):
        if self.figure is not None:
            # Note: include_plotlyjs='cdn' requires internet.
            # Use 'require' or True for offline use.
            html = self.figure.to_html(include_plotlyjs="cdn", full_html=False)
            self.browser.setHtml(html)
        else:
            self.browser.setHtml(
                "<html><body style='background:#111; color:#555; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;'><div>No plot data available.</div></body></html>"
            )

    def load_html_file(self, file_path: str):
        """
        Testing Method: Loads a local .html file directly into the browser.
        """
        if os.path.exists(file_path):
            # Convert absolute path to a URL format the browser understands
            local_url = QUrl.fromLocalFile(os.path.abspath(file_path))
            self.browser.load(local_url)
        else:
            print(f"Error: File not found at {file_path}")

    def set_scale(self, scale_type: str):
        """Sets the y-axis scale: 'log' or 'linear'"""
        if self.figure is not None:
            self.figure.update_layout(yaxis_type=scale_type)
            self.render_plot()

    def export_image(self):
        """Opens a dialog to save the current figure"""
        if self.figure is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "PNG (*.png);;JPG (*.jpg);;PDF (*.pdf)"
        )
        if path:
            self.figure.write_image(path)
