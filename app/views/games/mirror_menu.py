from ..game_menu_base import GameMenuBase


class MirrorMenu(GameMenuBase):
    def __init__(self, lang: str = "fa", parent=None):
        super().__init__(
            key="mirror",
            title_fa="Mirror Pulse",
            title_en="Mirror Pulse",
            summary_fa="کنترل آینه‌ای: در دو نیمه‌ی صفحه هم‌زمان بازی کن.",
            summary_en="Mirrored control: play both halves of the screen at once.",
            tips_fa="حواست به محور تقارن باشد؛ حرکاتت را متقارن برنامه‌ریزی کن.",
            tips_en="Respect the axis of symmetry; plan mirrored moves.",
            lang=lang,
            parent=parent,
        )
