import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Theme:
    name: str
    bgA: int
    bgB: int
    node: str
    playerA: str
    playerB: str
    powerSlow: str
    powerShield: str
    powerBurst: str


THEMES = {
    # Lightness و اشباع کمی بالاتر شده تا همه‌چیز واضح‌تر باشه
    "Aurora": Theme(
        "Aurora",
        210,
        260,
        "#93c5fd",
        "#60a5fa",
        "#c084fc",
        "#67e8f9",
        "#86efac",
        "#fde68a",
    ),
    "Ember": Theme(
        "Ember",
        20,
        45,
        "#fb923c",
        "#f97316",
        "#ef4444",
        "#f9a8d4",
        "#fde68a",
        "#fdba74",
    ),
    "Ocean": Theme(
        "Ocean",
        195,
        225,
        "#38bdf8",
        "#22d3ee",
        "#34d399",
        "#93c5fd",
        "#6ee7b7",
        "#facc15",
    ),
}

BRAND_NAME = "Neural Bloom"
TAGLINE = "Harness the flow. Bloom the signal."

INITIAL_TIME_ENDLESS = 120
RAMP_DURATION = 80
MAX_PHASE = 6
RAMP_RATE = 0.03

# ... سایر import ها ...
LANG_DEFAULT = "fa"  # 'fa' یا 'en'

# مسیر ذخیرهٔ تنظیمات کاربر (اگر قبلاً داری، همین را اضافه کن)


def user_data_path():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    p = Path(base) / "NeuralBloom"
    p.mkdir(parents=True, exist_ok=True)
    return p


SETTINGS_PATH = str(user_data_path() / "settings.json")


# 50 مرحله‌ی از پیش‌تعریف‌شده (از آسان به سخت)
# هر مرحله می‌تونه modifiers داشته باشه: spawnMul, glitchSpeedMul, powerFreq, theme
STORY_LEVELS = []
for i in range(1, 51):
    # تدریجی سخت‌تر: اسپاون، سرعت گلیچ کمی بالا می‌ره؛ هر 10 مرحله تم عوض می‌کنیم
    theme = "Aurora" if i <= 20 else ("Ocean" if i <= 35 else "Ember")
    spawnMul = 1.0 + (i - 1) * 0.02  # تا ~1.98
    glitchSpeedMul = 1.0 + (i - 1) * 0.015  # تا ~1.735
    powerFreq = max(4.0, 10.0 - i * 0.08)  # کمی سریع‌تر شدن پاورآپ‌ها
    # اهداف پایه: جمع‌آوری/امتیاز/دوام، هر چند مرحله یک تنوع
    if i % 10 == 0:
        obj = {"score": 600 + i * 8}
        desc = f"به امتیاز {obj['score']} برس."
        t = 80
    elif i % 7 == 0:
        obj = {"collect": 25 + (i // 2), "nohit": True}
        desc = f"{obj['collect']} نود بدون برخورد جمع کن."
        t = 75
    elif i % 5 == 0:
        obj = {"survive": 60 + (i // 2)}
        desc = f"{obj['survive']} ثانیه دوام بیار."
        t = obj["survive"]
    else:
        obj = {"collect": 15 + i}
        desc = f"{obj['collect']} نود جمع کن."
        t = 70
    STORY_LEVELS.append(
        {
            "id": i,
            "title": f"Stage {i}",
            "objective": obj,
            "time": t,
            "desc": desc,
            "mods": {
                "spawnMul": round(spawnMul, 3),
                "glitchSpeedMul": round(glitchSpeedMul, 3),
                "powerFreq": round(powerFreq, 3),
                "theme": theme,
            },
        }
    )

API_URL = ""  # e.g. "https://your-worker.example.com" (empty = offline)
LOCAL_LB_PATH = "leaderboard_local.json"
PROGRESS_PATH = "progress.json"  # ذخیره‌ی مرحله‌ی باز/جاری
