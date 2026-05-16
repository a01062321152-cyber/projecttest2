"""
notification_store.py
─────────────────────
개인별 알림을 notifications.json에 저장합니다.
알림 타입:
  item_added, item_deleted, item_price_changed,
  pot_joined, pot_ended, pot_disbanded
"""

import json
from pathlib import Path
from datetime import datetime

NOTIF_PATH = Path("notifications.json")


def _load() -> dict:
    if NOTIF_PATH.exists():
        return json.loads(NOTIF_PATH.read_text(encoding="utf-8"))
    return {}


def _save(data: dict) -> None:
    NOTIF_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def push(user_id: str, notif_type: str, message: str) -> None:
    """특정 유저에게 알림 추가"""
    data = _load()
    if user_id not in data:
        data[user_id] = []
    data[user_id].append({
        "type": notif_type,
        "message": message,
        "read": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(data)


def push_all(user_ids: list, notif_type: str, message: str) -> None:
    """여러 유저에게 동일 알림 전송"""
    for uid in user_ids:
        push(uid, notif_type, message)


def get_notifications(user_id: str) -> list:
    """유저의 알림 목록 (최신순)"""
    data = _load()
    return list(reversed(data.get(user_id, [])))


def get_unread_count(user_id: str) -> int:
    data = _load()
    return sum(1 for n in data.get(user_id, []) if not n["read"])


def mark_all_read(user_id: str) -> None:
    data = _load()
    for n in data.get(user_id, []):
        n["read"] = True
    _save(data)


def clear_notifications(user_id: str) -> None:
    data = _load()
    data[user_id] = []
    _save(data)
