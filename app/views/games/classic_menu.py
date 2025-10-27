from PySide6 import QtWidgets
from ..game_menu_base import GameMenuBase


class ClassicMenu(GameMenuBase):
    def __init__(self, lang: str = "fa", parent=None):
        super().__init__(
            key="classic",
            title_fa="Classic",
            title_en="Classic",
            summary_fa="هسته‌ی آرکید: نودها را جمع کن، از گلیچ‌ها دوری کن. پاورآپ‌ها را برای زنده‌ماندن و امتیاز بیشتر بگیر.",
            summary_en="Core arcade: collect nodes, dodge glitches. Grab power-ups to survive and score bigger.",
            tips_fa="حالت Mouse یا Keys را از تنظیمات انتخاب کن. Combo را نگه دار تا امتیاز چند برابر شود.",
            tips_en="Choose Mouse or Keys in Settings. Keep your combo alive for multiplied scores.",
            lang=lang,
            parent=parent,
        )
