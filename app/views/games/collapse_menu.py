from ..game_menu_base import GameMenuBase


class CollapseMenu(GameMenuBase):
    def __init__(self, lang: str = "fa", parent=None):
        super().__init__(
            key="collapse",
            title_fa="Neural Collapse",
            title_en="Neural Collapse",
            summary_fa="شبکه در حال فروپاشی است؛ تا می‌توانی زنده بمان.",
            summary_en="The network is collapsing; survive as long as you can.",
            tips_fa="پاورآپ Shield و Slowmo را برای مواقع بحرانی نگه دار.",
            tips_en="Save Shield and Slowmo for critical moments.",
            lang=lang,
            parent=parent,
        )
