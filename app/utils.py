import os, sys


def resource_path(rel_path: str) -> str:
    """مسیر فایل در حالت معمولی یا وقتی با PyInstaller بسته شده (داخل _MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)


def clamp(x,lo,hi):
    return lo if x<lo else hi if x>hi else x

def distance_sq(x1,y1,x2,y2):
    dx=x1-x2; dy=y1-y2; return dx*dx+dy*dy

def rect_intersects_circle(rx,ry,rw,rh,cx,cy,r):
    nx = max(rx, min(cx, rx + rw))
    ny = max(ry, min(cy, ry + rh))
    dx = cx - nx; dy = cy - ny
    return (dx*dx + dy*dy) <= (r*r)
