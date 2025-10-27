from PySide6 import QtWidgets
from ..game_menu_base import GameMenuBase
from ..generic_game_menu import GenericGameMenu

class ClassicMenu(GenericGameMenu):
    def __init__(self, lang: str = 'fa', parent=None):
        super().__init__(key='classic', lang=lang, parent=parent)
