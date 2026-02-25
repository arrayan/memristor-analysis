from app.ui.main_window import MainWindow
from app.core import MenuAction


def test_scale_switch_calls_set_scale(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    called = {"scale": None}

    class FakeViewer:
        def set_scale(self, scale):
            called["scale"] = scale

    monkeypatch.setattr(window.nav_bar, "get_current_viewer", lambda: FakeViewer())

    # trigger linear
    window.menu_bar.menu_actions[MenuAction.SCALE_LINEAR].trigger()

    assert called["scale"] == "linear"

    # trigger log
    window.menu_bar.menu_actions[MenuAction.SCALE_LOG].trigger()

    assert called["scale"] == "log"

    window.close()
