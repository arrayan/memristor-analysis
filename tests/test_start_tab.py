import PySide6.QtWidgets as qt
from src.app.ui import NavigationBar


def test_welcome_screen_empty_dir(qtbot, tmp_path):
    """Verify the start screen shows instructions when no data is found."""
    # Create a dummy temp dir that is empty
    temp_dir = tmp_path / "temp" / "device"
    temp_dir.mkdir(parents=True)

    # Patch the directory in the widget
    widget = NavigationBar()
    widget.temp_device_dir = temp_dir
    widget.show_welcome_screen()

    # Check that the 'Start' tab is created
    assert widget.count() == 1
    assert widget.tabText(0) == "Start"

    # Check if the instruction label exists
    # (Finding by text is a great way to verify UI state)
    label = widget.findChild(qt.QLabel)
    assert "Please import data" in label.text()
