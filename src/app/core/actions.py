from enum import Enum, auto
class MenuAction(Enum):
    # FILE MENU
    # IMPORT
    IMPORT_DEVICE = ("Device", "Ctrl+O", False)
    IMPORT_STACK = ("Stack", "Ctrl+Shift+O", False)

    # EXPORT
    EXPORT_ALL = ("All", "Ctrl+Shift+E", False)
    EXPORT_ALL_PNG = ("PNG", None, False)
    EXPORT_ALL_JPEG = ("JPEG", None, False)
    EXPORT_ALL_APS = ("APS", None, False)
    
    EXPORT_CURRENT = ("Current", "Ctrl+E", False)
    EXPORT_CURRENT_PNG = ("PNG", None, False)
    EXPORT_CURRENT_JPEG = ("JPEG", None, False)
    EXPORT_CURRENT_APS = ("APS", None, False)

    # EXIT
    EXIT = ("Exit", "Ctrl+Q", False)

    # OPTIONS MENU
    SCALE_LINEAR = ("linear", None, True)
    SCALE_LOG = ("log", None, True)
    
    # HELP MENU
    VIEW_HELP = ("View Help", "F1", False)
    ABOUT = ("About", None, False)

    def __init__(self, text, shortcut=None, checkable=False):
        self.text = text
        self.shortcut = shortcut
        self.checkable = checkable