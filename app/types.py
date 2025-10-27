# -*- coding: utf-8 -*-
from typing import TypedDict

class ScoreEntry(TypedDict, total=False):
    name: str
    score: int
    mode: str
    ts: float  # optional timestamp
