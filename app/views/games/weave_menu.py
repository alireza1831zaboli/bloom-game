from PySide6 import QtWidgets
from ..game_menu_base import GameMenuBase


class WeaveMenu(GameMenuBase):
    def __init__(self, lang: str = "fa", parent=None):
        super().__init__(
            key="weave",
            title_fa="Flux Weave",
            title_en="Flux Weave",
            summary_fa="گره‌ها را به‌هم وصل کن و حلقه بساز. از برخورد مسیر با خودت یا گلیچ‌ها پرهیز کن.",
            summary_en="Connect nodes and form loops. Avoid crossing your own trail or hitting glitches.",
            tips_fa="با Slowmo دقت رسم خود را بالا ببر. حلقه‌ی بزرگ‌تر = امتیاز بیشتر.",
            tips_en="Use Slowmo for precision. Larger loops = higher score.",
            lang=lang,
            parent=parent,
        )
