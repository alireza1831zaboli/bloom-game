import json, os, threading, requests
from .settings import LOCAL_LB_PATH, API_URL


class LocalLeaderboard:
    def __init__(self, path: str = LOCAL_LB_PATH):
        self.path = path
        if not os.path.exists(self.path):
            self._save([])

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, items):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(items[:10], f, ensure_ascii=False, indent=2)

    def add(self, name: str, score: int, mode: str):
        items = self._load()
        items.append({"name": name, "score": score, "mode": mode})
        items.sort(key=lambda x: x["score"], reverse=True)
        self._save(items)


class OnlineLeaderboard:
    def submit(self, name, score, mode):
        if not API_URL:
            return

        def _do():
            try:
                requests.post(
                    f"{API_URL}/leaderboard",
                    json={"name": name, "score": score, "mode": mode},
                    timeout=5,
                )
            except Exception:
                pass

        threading.Thread(target=_do, daemon=True).start()
