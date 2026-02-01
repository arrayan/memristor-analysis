from enum import Enum, auto
class MenuAction(Enum):
    # FILE MENU
    # IMPORT
    IMPORT_DEVICE = ("Device", "Ctrl+O")
    IMPORT_STACK = ("Stack", "Ctrl+Shift+O")

    # EXPORT
    EXPORT_ALL = ("All", "Ctrl+Shift+E")
    EXPORT_ALL_PNG = ("PNG", None)
    EXPORT_ALL_JPEG = ("JPEG", None)
    EXPORT_ALL_APS = ("APS", None)
    
    EXPORT_CURRENT = ("Current", "Ctrl+E")
    EXPORT_CURRENT_PNG = ("PNG", None)
    EXPORT_CURRENT_JPEG = ("JPEG", None)
    EXPORT_CURRENT_APS = ("APS", None)

    # EXIT
    EXIT = ("Exit", "Ctrl+Q")
    
    # HELP MENU
    VIEW_HELP = ("View Help", "F1")
    ABOUT = ("About", None)

    def __init__(self, text, shortcut=None):
        self.text = text
        self.shortcut = shortcut