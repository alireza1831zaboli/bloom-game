import os, sys


def resource_path(rel_path: str) -> str:
    """مسیر فایل در حالت معمولی یا وقتی با PyInstaller بسته شده (داخل _MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)


# ---- Common math/geometry helpers (extracted for reuse) ----
def clamp(x: float, lo: float, hi: float) -> float:
    """Return x clamped to [lo, hi]."""
    return lo if x < lo else hi if x > hi else x

def distance_sq(x1: float, y1: float, x2: float, y2: float) -> float:
    """Squared Euclidean distance (avoids sqrt for performance)."""
    dx = x1 - x2
    dy = y1 - y2
    return dx*dx + dy*dy

def rect_intersects_circle(rx: float, ry: float, rw: float, rh: float, cx: float, cy: float, r: float) -> bool:
    """
    Axis-aligned rectangle vs circle intersection test.
    Equivalent to the earlier inline implementation used in phantom_run_widget.
    """
    nx = max(rx, min(cx, rx + rw))
    ny = max(ry, min(cy, ry + rh))
    dx = cx - nx
    dy = cy - ny
    return (dx * dx + dy * dy) <= (r * r)
