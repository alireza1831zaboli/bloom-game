from ..game_menu_base import GameMenuBase


class PhantomMenu(GameMenuBase):
    def __init__(self, lang: str = "fa", parent=None):
        super().__init__(
            key="phantom",
            title_fa="phantom",
            title_en="phantom",
            summary_fa="رانر نئونی بی‌انتها؛ از شکاف‌ها عبور کن. «Phase» اجازهٔ عبور کوتاه از دیوارها را می‌دهد.",
            summary_en="Endless neon runner. Pass the gaps. Phase lets you pass through walls briefly.",
            tips_fa="وسط بمان و آرام به‌سمت شکاف‌ها حرکت کن. Phase را برای الگوهای تنگ نگه‌دار. Wrap افقی کمک می‌کند.",
            tips_en="Keep center and drift into gaps. Save Phase for tight patterns. Wrapping helps for last-second escapes.",
            lang=lang,
            parent=parent,
        )
