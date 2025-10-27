from PySide6 import QtWidgets
from ..game_menu_base import GameMenuBase
from ..generic_game_menu import GenericGameMenu

class WeaveMenu(GenericGameMenu):
    def __init__(self, lang: str = 'fa', parent=None):
        super().__init__(key='weave', lang=lang, parent=parent)
