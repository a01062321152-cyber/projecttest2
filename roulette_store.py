"""
roulette_store.py — 룰렛 상품 데이터
참여 시 5크래딧 소모, spin_count 기반 누적 확률
"""
import json, uuid, random
from pathlib import Path
from datetime import datetime

DB       = Path("roulette_items.json")
SPIN_LOG = Path("roulette_spins.json")

SPIN_CREDIT_COST = 5  # 룰렛 1회 참여 크래딧 비용

def _r():
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else {}

def _w(d):
    DB.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def _rl():
    return json.loads(SPIN_LOG.read_text(encoding="utf-8")) if SPIN_LOG.exists() else {}

def _wl(d):
    SPIN_LOG.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def register_item(owner_id, owner_name, owner_temp,
                  item_name, item_desc, contact, image_url=""):
    d   = _r()
    rid = str(uuid.uuid4())[:8]
    d[rid] = {
        "roulette_id": rid,
        "owner_id":    owner_id,
        "owner_name":  owner_name,
        "owner_temp":  owner_temp,
        "item_name":   item_name,
        "item_desc":   item_desc,
        "contact":     contact,
        "image_url":   image_url,
        "status":      "active",   # active | won | removed
        "winner_id":   None,
        "spin_count":  0,
        "created_at":  datetime.now().isoformat(),
    }
    _w(d)
    return rid


def get_active_items(exclude_user_id=""):
    d = _r()
    return [v for v in d.values()
            if v["status"] == "active" and v["owner_id"] != exclude_user_id]

def get_my_items(owner_id):
    return [v for v in _r().values() if v["owner_id"] == owner_id]

def get_item(rid):
    return _r().get(rid)


def spin(rid: str, user_id: str) -> tuple[bool, str]:
    """
    크래딧 차감은 호출부(wishlist_page)에서 먼저 처리.
    Returns (is_win, message)
    """
    d    = _r()
    item = d.get(rid)
    if not item:                    return False, "상품을 찾을 수 없습니다."
    if item["status"] != "active":  return False, "이미 당첨된 상품입니다."
    if item["owner_id"] == user_id: return False, "본인 상품은 참여할 수 없습니다."

    log        = _rl()
    user_spins = log.get(user_id, [])
    if rid in user_spins:           return False, "이미 참여한 상품입니다."

    # 누적 확률: 20 - spin_count (최소 2)
    total  = max(2, 20 - item["spin_count"])
    is_win = (random.randint(1, total) == 1)

    item["spin_count"] += 1
    if is_win:
        item["status"]    = "won"
        item["winner_id"] = user_id
    _w(d)

    # 참여 기록
    log.setdefault(user_id, []).append(rid)
    _wl(log)

    return is_win, "win" if is_win else f"꽝 (다음 확률: 1/{max(1, total - 1)})"


def remove_item(rid, owner_id):
    d    = _r()
    item = d.get(rid)
    if item and item["owner_id"] == owner_id:
        item["status"] = "removed"
        _w(d)
        return True
    return False

def admin_remove_item(rid: str) -> bool:
    """관리자 강제 삭제"""
    d    = _r()
    item = d.get(rid)
    if item:
        item["status"] = "removed"
        _w(d)
        return True
    return False

def get_all_items() -> list:
    """관리자용: 전체 상품 목록"""
    return list(_r().values())

def has_spun(rid, user_id):
    return rid in _rl().get(user_id, [])
