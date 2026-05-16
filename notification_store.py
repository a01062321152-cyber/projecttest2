"""notification_store.py — 개인 알림 관리"""

import json
from pathlib import Path
from datetime import datetime

NOTIF_PATH = Path("notifications.json")


def _load():
    if NOTIF_PATH.exists():
        return json.loads(NOTIF_PATH.read_text(encoding="utf-8"))
    return {}

def _save(d):
    NOTIF_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def push(user_id: str, notif_type: str, message: str):
    d = _load()
    if user_id not in d:
        d[user_id] = []
    d[user_id].append({
        "type": notif_type,
        "message": message,
        "read": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(d)

def push_all(user_ids: list, notif_type: str, message: str):
    for uid in user_ids:
        push(uid, notif_type, message)

def get_notifications(user_id: str) -> list:
    return list(reversed(_load().get(user_id, [])))

def get_unread_count(user_id: str) -> int:
    return sum(1 for n in _load().get(user_id, []) if not n["read"])

def mark_all_read(user_id: str):
    d = _load()
    for n in d.get(user_id, []):
        n["read"] = True
    _save(d)

def clear_notifications(user_id: str):
    d = _load()
    d[user_id] = []
    _save(d)
