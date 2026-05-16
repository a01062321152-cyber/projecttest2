"""
rating_store.py
───────────────
팟 종료 후 참여자 평가(10점 만점) 및 매너 온도(0~100도) 관리.
ratings.json 구조:
  {
    "user_id": {
      "scores": [8, 9, 7, ...],   # 받은 점수들
      "temperature": 75.0          # 평균 × 10
    }
  }
"""

import json
from pathlib import Path

RATING_PATH = Path("ratings.json")


def _load() -> dict:
    if RATING_PATH.exists():
        return json.loads(RATING_PATH.read_text(encoding="utf-8"))
    return {}


def _save(data: dict) -> None:
    RATING_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_score(user_id: str, score: int) -> None:
    """평가 점수 추가 (1~10). 매너 온도 재계산."""
    score = max(1, min(10, score))
    data = _load()
    if user_id not in data:
        data[user_id] = {"scores": [], "temperature": 50.0}
    data[user_id]["scores"].append(score)
    avg = sum(data[user_id]["scores"]) / len(data[user_id]["scores"])
    data[user_id]["temperature"] = round(avg * 10, 1)   # 10점 → 100도
    _save(data)


def get_temperature(user_id: str) -> float:
    """매너 온도 반환 (기본 50.0)"""
    data = _load()
    return data.get(user_id, {}).get("temperature", 50.0)


def get_score_count(user_id: str) -> int:
    data = _load()
    return len(data.get(user_id, {}).get("scores", []))


def temp_color(temp: float) -> str:
    """온도에 따른 색상"""
    if temp >= 80:   return "#EF4444"   # 빨강 (뜨거움)
    elif temp >= 60: return "#F59E0B"   # 주황
    elif temp >= 40: return "#3B82F6"   # 파랑 (보통)
    else:            return "#6B7280"   # 회색 (낮음)


def temp_label(temp: float) -> str:
    if temp >= 80:   return "🔥 매너왕"
    elif temp >= 60: return "😊 좋아요"
    elif temp >= 40: return "😐 보통"
    else:            return "🥶 주의"
