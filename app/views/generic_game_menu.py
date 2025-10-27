# -*- coding: utf-8 -*-
"""Generic menu that populates fields from GAME_META registry.
No behavioral/UI changes compared to per-mode menus."""
from PySide6 import QtWidgets
from .game_menu_base import GameMenuBase
from .game_registry import GAME_META

class GenericGameMenu(GameMenuBase):
    def __init__(self, key: str, lang: str = "fa", parent=None):
        meta = GAME_META[key]
        super().__init__(
            key=key,
            title_fa=meta["title_fa"],
            title_en=meta["title_en"],
            summary_fa=meta["summary_fa"],
            summary_en=meta["summary_en"],
            tips_fa=meta["tips_fa"],
            tips_en=meta["tips_en"],
            lang=lang,
            parent=parent,
        )
