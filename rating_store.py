"""rating_store.py — 매너 온도 / 평가 관리"""

import json
from pathlib import Path

RATING_PATH = Path("ratings.json")


def _load():
    if RATING_PATH.exists():
        return json.loads(RATING_PATH.read_text(encoding="utf-8"))
    return {}

def _save(d):
    RATING_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def add_score(user_id: str, score: int):
    score = max(1, min(10, score))
    d = _load()
    if user_id not in d:
        d[user_id] = {"scores": [], "temperature": 50.0}
    d[user_id]["scores"].append(score)
    avg = sum(d[user_id]["scores"]) / len(d[user_id]["scores"])
    d[user_id]["temperature"] = round(avg * 10, 1)
    _save(d)

def get_temperature(user_id: str) -> float:
    return _load().get(user_id, {}).get("temperature", 50.0)

def get_score_count(user_id: str) -> int:
    return len(_load().get(user_id, {}).get("scores", []))

def temp_color(temp: float) -> str:
    if temp >= 80:   return "#EF4444"
    elif temp >= 60: return "#F59E0B"
    elif temp >= 40: return "#3B82F6"
    else:            return "#6B7280"

def temp_label(temp: float) -> str:
    if temp >= 80:   return "🔥 매너왕"
    elif temp >= 60: return "😊 좋아요"
    elif temp >= 40: return "😐 보통"
    else:            return "🥶 주의"
