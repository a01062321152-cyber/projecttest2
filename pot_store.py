"""pot_store.py — 구메팟 데이터 관리"""

import json, uuid
from pathlib import Path
from datetime import datetime

POT_DB_PATH = Path("pots.json")


def _load():
    if POT_DB_PATH.exists():
        return json.loads(POT_DB_PATH.read_text(encoding="utf-8"))
    return {}

def _save(d):
    POT_DB_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 생성 ─────────────────────────────────────────────────────────────────────

def create_pot(item_label, item_image, creator_id, creator_name,
               total_people, buy_date, location_name, location_lat,
               location_lng, price_total, contact=""):
    d = _load()
    pot_id = str(uuid.uuid4())[:8]
    d[pot_id] = {
        "pot_id":        pot_id,
        "item_label":    item_label,
        "item_image":    item_image,
        "creator_id":    creator_id,
        "creator_name":  creator_name,
        "total_people":  total_people,
        "buy_date":      buy_date,
        "location_name": location_name,
        "location_lat":  location_lat,
        "location_lng":  location_lng,
        "price_total":   price_total,
        "contact":       contact,
        "members":       [creator_id],
        "status":        "active",   # active | ended | disbanded
        "rated_by":      [],
        "created_at":    datetime.now().isoformat(),
    }
    _save(d)
    return pot_id


# ── 조회 ─────────────────────────────────────────────────────────────────────

def get_all_pots() -> list:
    """관리자용: 전체 팟 (삭제된 것 제외)"""
    return list(_load().values())

def get_pots_for_item(item_label) -> list:
    """아이템별 active 팟 목록"""
    d = _load()
    result = [p for p in d.values()
              if p["item_label"] == item_label and p.get("status") == "active"]
    return sorted(result, key=lambda x: x["created_at"], reverse=True)

def get_active_pots_by_user(user_id) -> list:
    """마이페이지 표시용: active 팟만 (종료·해산 제외)"""
    d = _load()
    return [p for p in d.values()
            if user_id in p.get("members", []) and p.get("status") == "active"]

def get_pot_history_by_user(user_id) -> list:
    """
    추천 시스템 활용용: 종료(ended)·해산(disbanded) 팟 기록.
    마이페이지에는 표시하지 않지만 데이터는 보존.
    """
    d = _load()
    return [p for p in d.values()
            if user_id in p.get("members", [])
            and p.get("status") in ("ended", "disbanded")]

def get_pot(pot_id) -> dict | None:
    return _load().get(pot_id)


# ── 참여 ─────────────────────────────────────────────────────────────────────

def join_pot(pot_id, user_id):
    d   = _load()
    pot = d.get(pot_id)
    if pot is None:                               return False, "팟을 찾을 수 없습니다."
    if pot.get("status") != "active":            return False, "진행 중인 팟이 아닙니다."
    if user_id in pot["members"]:                return False, "이미 참여 중인 팟입니다."
    if len(pot["members"]) >= pot["total_people"]: return False, "팟이 이미 꽉 찼습니다."
    pot["members"].append(user_id)
    _save(d)
    return True, "success"


# ── 종료 / 해산 ───────────────────────────────────────────────────────────────

def end_pot(pot_id) -> bool:
    d   = _load()
    pot = d.get(pot_id)
    if pot and pot.get("status") == "active":
        pot["status"] = "ended"
        _save(d)
        return True
    return False

def disband_pot(pot_id) -> bool:
    d   = _load()
    pot = d.get(pot_id)
    if pot and pot.get("status") == "active":
        pot["status"] = "disbanded"
        _save(d)
        return True
    return False

def admin_delete_pot(pot_id) -> bool:
    """관리자 강제 삭제 (DB에서 완전 제거)"""
    d = _load()
    if pot_id in d:
        del d[pot_id]
        _save(d)
        return True
    return False

def mark_rated(pot_id, user_id):
    d   = _load()
    pot = d.get(pot_id)
    if pot and user_id not in pot.get("rated_by", []):
        pot.setdefault("rated_by", []).append(user_id)
        _save(d)

def disband_pots_for_item(item_label) -> list:
    """아이템 삭제 시 연관 active 팟 전부 해산. 해당 팟 목록 반환."""
    d        = _load()
    affected = []
    for pot in d.values():
        if pot["item_label"] == item_label and pot.get("status") == "active":
            pot["status"] = "disbanded"
            affected.append(pot)
    _save(d)
    return affected


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def calc_dday(buy_date_str) -> str:
    try:
        diff = (datetime.strptime(buy_date_str, "%Y-%m-%d").date()
                - datetime.now().date()).days
        if diff > 0:    return f"D-{diff}"
        elif diff == 0: return "D-Day"
        else:           return f"D+{abs(diff)}"
    except Exception:
        return ""

def price_per_person(pot) -> int:
    n = pot.get("total_people", 1)
    return pot.get("price_total", 0) // max(n, 1)
