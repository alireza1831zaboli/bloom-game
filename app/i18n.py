# -*- coding: utf-8 -*-
# مترجم سبک: کلیدها => ترجمه‌ی fa/en
from dataclasses import dataclass


@dataclass(frozen=True)
class Lang:
    code: str  # 'fa' یا 'en'
    rtl: bool


FA = Lang("fa", True)
EN = Lang("en", False)

STRINGS = {
    # عمومی
    "app.title": {"fa": "Neural Bloom", "en": "Neural Bloom"},
    "tagline": {
        "fa": "Harness the flow. Bloom the signal.",
        "en": "Harness the flow. Bloom the signal.",
    },
    "back": {"fa": "↩ بازگشت به منو", "en": "↩ Back to Menu"},
    "apply": {"fa": "اعمال تنظیمات", "en": "Apply"},
    "close": {"fa": "بستن", "en": "Close"},
    # منو
    "menu.continue": {"fa": "ادامه مراحل", "en": "Continue"},
    "menu.new": {"fa": "مرحله جدید", "en": "New Stage"},
    "menu.endless": {"fa": "بینهایت", "en": "Endless"},
    "menu.settings": {"fa": "تنظیمات", "en": "Settings"},
    "menu.about": {"fa": "درباره ما", "en": "About"},
    "menu.quit": {"fa": "خروج", "en": "Quit"},
    # تنظیمات
    "settings.title": {"fa": "تنظیمات", "en": "Settings"},
    "settings.prefs": {"fa": "ترجیحات", "en": "Preferences"},
    "settings.control": {"fa": "حالت کنترل:", "en": "Control:"},
    "settings.sfx": {"fa": "صداها:", "en": "SFX:"},
    "settings.music": {"fa": "موسیقی:", "en": "Music:"},
    "settings.theme": {"fa": "تم:", "en": "Theme:"},
    "settings.lang": {"fa": "زبان:", "en": "Language:"},
    "settings.guide": {"fa": "راهنما", "en": "Guide"},
    "settings.hints": {
        "fa": "• Mouse: تعقیب نرم نشانگر.\n• Keys: حرکت روبه‌جلو ثابت + چرخش با چپ/راست.\n• تغییرات پس از زدن «اعمال تنظیمات» فعال می‌شوند.",
        "en": "• Mouse: Smooth cursor follow.\n• Keys: Constant forward, steer with Left/Right.\n• Changes take effect after pressing Apply.",
    },
    # درباره ما
    "about.title": {"fa": "درباره سازنده", "en": "About the Creator"},
    "about.card": {
        "fa": "این بازی توسط {name} ساخته شده است.\nایده: جریان، کمبو و واکنش سریع.\nتکنولوژی: Python (PySide6) + QPainter.\nبازخورد شما باعث بهتر شدن نسخه‌های بعدی می‌شود.",
        "en": "This game is created by {name}.\nIdea: flow, combos, fast reaction.\nTech: Python (PySide6) + QPainter.\nYour feedback helps improve the next versions.",
    },
    # بازی/نوار بالا
    "toolbar.back": {"fa": "بازگشت به منو", "en": "Back to Menu"},
    "toolbar.start": {"fa": "Start", "en": "Start"},
    "toolbar.pause": {"fa": "Pause", "en": "Pause"},
    "toolbar.reset": {"fa": "Reset", "en": "Reset"},
    "toolbar.score": {"fa": "امتیاز", "en": "Score"},
    "toolbar.time": {"fa": "زمان", "en": "Time"},
    "toolbar.best": {"fa": "بهترین", "en": "Best"},

    # --- منوی هاب
    "hub.classic": {"fa": "Classic", "en": "Classic"},
    "hub.weave": {"fa": "Flux Weave", "en": "Flux Weave"},
    "hub.arch": {"fa": "Signal Architect", "en": "Signal Architect"},
    "hub.mirror": {"fa": "Mirror Pulse", "en": "Mirror Pulse"},
    "hub.collapse": {"fa": "Neural Collapse", "en": "Neural Collapse"},
    "hub.phantom": {"fa": "Phantom Run", "en": "Phantom Run"},

    # توضیح کوتاه کارت‌ها (زیر عنوان در هاب)
    "desc.classic": {"fa": "هسته‌ی آرکید: جمع‌آوری نودها، فرار از گلیچ", "en": "Core arcade: collect nodes, dodge glitches"},
    "desc.weave": {"fa": "گره‌ها را به‌هم بباف؛ حلقه بساز", "en": "Weave nodes together; form loops"},
    "desc.flow": {"fa": "تکامل: رشد توانایی‌ها و دگرگونی جهان", "en": "Evolution: grow abilities and transform the world"},
    "desc.arch": {"fa": "پازل طراحی مسیر سیگنال بدون خطا", "en": "Puzzle: design signal paths without faults"},
    "desc.mirror": {"fa": "کنترل آینه‌ای؛ دو ذهن، یک حرکت", "en": "Mirrored control; two minds, one move"},
    "desc.collapse": {"fa": "بقا میان فروپاشی شبکه", "en": "Survive amidst network collapse"},
    "desc.phantom": {"fa": "میان دیوارهای نئونی؛ از شکاف‌های پویا عبور کن.", "en": "Dodge neon walls; thread dynamic gaps."},

    # منوی داخلی هر بازی
    "gm.play.endless": {"fa": "شروع حالت بینهایت", "en": "Start Endless"},
    "gm.play.story": {"fa": "شروع حالت مرحله‌ای", "en": "Start Story"},
    "gm.back": {"fa": "↩ بازگشت", "en": "↩ Back"},
    "gm.summary": {"fa": "توضیحات", "en": "Summary"},
    "gm.tips": {"fa": "راهنما", "en": "Tips"},


}


def tr(key: str, lang: str = "fa", **fmt) -> str:
    v = STRINGS.get(key, {})
    s = v.get(lang, v.get("en", key))
    try:
        return s.format(**fmt) if fmt else s
    except Exception:
        return s
