import PySide6.QtWidgets as qt
from app.ui.navigation_bar import NavigationBar


def test_welcome_screen_empty_dir(qtbot, tmp_path, monkeypatch):
    # Force "empty" regardless of whatever default temp dir contains
    monkeypatch.setattr(NavigationBar, "is_device_folder_empty", lambda self: True)

    widget = NavigationBar()
    qtbot.addWidget(widget)

    widget.show_welcome_screen()

    assert widget.count() == 1
    assert widget.tabText(0) == "Start"

    # Find the title label that contains the instruction
    labels = widget.findChildren(qt.QLabel)
    assert any("Please import data" in lbl.text() for lbl in labels)
