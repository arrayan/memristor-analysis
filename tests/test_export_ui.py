from app.ui.main_window import MainWindow
from app.ui.plot_viewer import PlotViewer


# Dummy figure with write_image stub
class DummyFigure:
    def write_image(self, path, format):
        # Simulate successful image writing
        return True


def test_export_current_png_triggers_export(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    called = {}

    class FakeViewer:
        html_path = "plot.html"

        def export_image(self, path, fmt):
            called["path"] = path
            called["fmt"] = fmt
            return True

    monkeypatch.setattr(window.nav_bar, "get_current_viewer", lambda: FakeViewer())
    monkeypatch.setattr(
        "app.ui.main_window.qt.QFileDialog.getSaveFileName",
        lambda *a, **k: ("test.png", ""),
    )

    window.export_current("png")
    window.close()

    assert called["fmt"] == "png"
    assert called["path"] == "test.png"


def test_export_current_no_viewer_shows_warning(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    called = {"warning": False}
    monkeypatch.setattr(window.nav_bar, "get_current_viewer", lambda: None)

    def fake_warning(*args, **kwargs):
        called["warning"] = True

    monkeypatch.setattr("app.ui.main_window.qt.QMessageBox.warning", fake_warning)

    window.export_current("png")
    window.close()

    assert called["warning"] is True


def test_export_current_cancel_dialog_does_nothing(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    called = {"export": False}

    class FakeViewer:
        html_path = "plot.html"

        def export_image(self, path, fmt):
            called["export"] = True
            return True

    monkeypatch.setattr(window.nav_bar, "get_current_viewer", lambda: FakeViewer())
    monkeypatch.setattr(
        "app.ui.main_window.qt.QFileDialog.getSaveFileName", lambda *a, **k: ("", "")
    )

    window.export_current("png")
    window.close()

    assert called["export"] is False


def test_eps_export_svg2rlg_failure(monkeypatch, tmp_path):
    viewer = PlotViewer()
    viewer.figure = DummyFigure()

    # Force svg2rlg to fail (returns None)
    monkeypatch.setattr("app.ui.plot_viewer.svg2rlg", lambda path: None)

    out_file = tmp_path / "out.eps"
    result = viewer.export_image(str(out_file), "eps")

    # Should return False because svg2rlg returned None
    assert result is False
    assert not out_file.exists()


def test_eps_export_render_failure(monkeypatch, tmp_path):
    viewer = PlotViewer()
    viewer.figure = DummyFigure()

    # Fake RLG object with failing renderPS.drawToFile
    class FakeRLG:
        class renderPS:
            @staticmethod
            def drawToFile(path):
                raise RuntimeError("Render failed")

    monkeypatch.setattr("app.ui.plot_viewer.svg2rlg", lambda path: FakeRLG())

    out_file = tmp_path / "out.eps"
    result = viewer.export_image(str(out_file), "eps")

    assert result is False
    assert not out_file.exists()
