import pytest

from app.ui.main_window import MainWindow
from app.core import MenuAction, Mode

#testing if the import button triggers a window
def test_import_device_action_triggers_handle_import(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    called = {}

    def fake_handle_import(*, mode):
        called["mode"] = mode

    monkeypatch.setattr(window, "handle_import", fake_handle_import)

    # Trigger the QAction like a user clicking the menu item
    window.menu_bar.menu_actions[MenuAction.IMPORT_DEVICE].trigger()

    assert called["mode"] == Mode.DEVICE


def test_import_stack_action_triggers_handle_import(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    called = {}

    def fake_handle_import(*, mode):
        called["mode"] = mode

    monkeypatch.setattr(window, "handle_import", fake_handle_import)

    window.menu_bar.menu_actions[MenuAction.IMPORT_STACK].trigger()

    assert called["mode"] == Mode.STACK
    
from app.ui.main_window import MainWindow


def test_import_success_refreshes_tabs(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    called = {"updated": False}

    # Fake ProgressDialog so .close() doesn't crash
    class FakePD:
        def close(self):
            pass

    window.pd = FakePD()

    # Detect NavigationBar refresh
    def fake_update(level):
        called["updated"] = True

    monkeypatch.setattr(
        window.nav_bar,
        "update_tabs_by_level",
        fake_update
    )

    # Prevent popup
    monkeypatch.setattr(
        "app.ui.main_window.qt.QMessageBox.information",
        lambda *a, **k: None
    )

    window.on_import_success()

    window.close()

    assert called["updated"] is True