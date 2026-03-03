from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtCore import QUrl
from pathlib import Path
import plotly.io as pio
import os
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPS
import tempfile


class PlotViewer(QWidget):
    def __init__(self, figure=None):
        super().__init__()
        self.figure = figure
        self.html_path: str | None = None
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
            # storing path
            self.html_path = file_path
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

    def export_image(self, out_path: str, fmt: str) -> bool:
        fmt = fmt.lower().strip()

        if self.figure is not None:
            if fmt == "eps":
                with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
                    svg_path = tmp.name
                try:
                    self.figure.write_image(svg_path, format="svg")

                    drawing = svg2rlg(svg_path)
                    if drawing is None:
                        print("EPS export failed: SVG parsing returned None")
                        return False

                    renderPS.drawToFile(drawing, out_path)
                    return True

                except Exception as e:
                    print(f"EPS export error: {e}")
                    return False

                finally:
                    if os.path.exists(svg_path):
                        os.remove(svg_path)

            # Non-EPS live figure
            try:
                self.figure.write_image(out_path, format=fmt)
                return True
            except Exception as e:
                print(f"Export error: {e}")
                return False

        # Otherwise export from sidecar JSON next to the loaded HTML
        if not self.html_path:
            return False

        json_path = Path(self.html_path).with_suffix(".json")
        if not json_path.exists():
            return False

        fig = pio.from_json(json_path.read_text(encoding="utf-8"))

        if fmt == "eps":
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
                svg_path = tmp.name
            try:
                fig.write_image(svg_path, format="svg")

                drawing = svg2rlg(svg_path)
                if drawing is None:
                    print("EPS export failed: SVG parsing returned None")
                    return False

                renderPS.drawToFile(drawing, out_path)
                return True

            except Exception as e:
                print(f"EPS export error: {e}")
                return False

            finally:
                if os.path.exists(svg_path):
                    os.remove(svg_path)

        # Normal formats (PNG/SVG/PDF)
        fig.write_image(out_path, format=fmt)
        return True
