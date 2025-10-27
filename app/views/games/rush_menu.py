from ..game_menu_base import GameMenuBase


class RushMenu(GameMenuBase):
    def __init__(self, lang: str = "fa", parent=None):
        super().__init__(
            key="rush",  # کلید درست برای Signal Rush
            title_fa="Signal Rush",
            title_en="Signal Rush",
            summary_fa="روی شبکه جریان بگیر؛ نودها را جمع کن و از گلیچ‌ها با Phase Dash عبور کن.",
            summary_en="Ride the network; collect nodes and slip past glitches with Phase Dash.",
            tips_fa="با ماوس حرکت افقی نرم داری؛ Space/کلیک برای Dash. سرعت کم‌کم بالا می‌رود.",
            tips_en="Smooth horizontal move; press Space/Click to Phase Dash. Speed ramps up gradually.",
            lang=lang,
            parent=parent,
        )
