import os, sys


def resource_path(rel_path: str) -> str:
    """مسیر فایل در حالت معمولی یا وقتی با PyInstaller بسته شده (داخل _MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)
