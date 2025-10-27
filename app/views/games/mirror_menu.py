from ..game_menu_base import GameMenuBase

from ..generic_game_menu import GenericGameMenu

class MirrorMenu(GenericGameMenu):
    def __init__(self, lang: str = 'fa', parent=None):
        super().__init__(key='mirror', lang=lang, parent=parent)
