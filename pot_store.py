"""
pot_store.py  —  구메팟 데이터 관리
상태: active | ended | disbanded
"""

import json, uuid
from pathlib import Path
from datetime import datetime

POT_DB_PATH = Path("pots.json")


def _load() -> dict:
    if POT_DB_PATH.exists():
        return json.loads(POT_DB_PATH.read_text(encoding="utf-8"))
    return {}

def _save(data: dict) -> None:
    POT_DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 생성 ─────────────────────────────────────────────────────────────────────

def create_pot(
    item_label: str, item_image: str,
    creator_id: str, creator_name: str,
    total_people: int, buy_date: str,
    location_name: str, location_lat: float, location_lng: float,
    price_total: int,
    contact: str = "",          # ← 연락처
) -> str:
    data   = _load()
    pot_id = str(uuid.uuid4())[:8]
    data[pot_id] = {
        "pot_id": pot_id,
        "item_label": item_label,
        "item_image": item_image,
        "creator_id": creator_id,
        "creator_name": creator_name,
        "total_people": total_people,
        "buy_date": buy_date,
        "location_name": location_name,
        "location_lat": location_lat,
        "location_lng": location_lng,
        "price_total": price_total,
        "contact": contact,
        "members": [creator_id],
        "status": "active",          # active | ended | disbanded
        "rated_by": [],              # 이미 평가를 제출한 user_id 목록
        "created_at": datetime.now().isoformat(),
    }
    _save(data)
    return pot_id


# ── 조회 ─────────────────────────────────────────────────────────────────────

def get_all_pots() -> list[dict]:
    return list(_load().values())

def get_pots_for_item(item_label: str) -> list[dict]:
    data = _load()
    result = [p for p in data.values()
              if p["item_label"] == item_label and p.get("status") == "active"]
    return sorted(result, key=lambda x: x["created_at"], reverse=True)

def get_pots_by_user(user_id: str) -> list[dict]:
    """내가 멤버인 팟 (active + ended 포함, disbanded 제외)"""
    data = _load()
    return [p for p in data.values()
            if user_id in p.get("members", []) and p.get("status") != "disbanded"]

def get_pot(pot_id: str) -> dict | None:
    return _load().get(pot_id)


# ── 참여 ─────────────────────────────────────────────────────────────────────

def join_pot(pot_id: str, user_id: str) -> tuple[bool, str]:
    data = _load()
    pot  = data.get(pot_id)
    if pot is None:                          return False, "팟을 찾을 수 없습니다."
    if pot.get("status") != "active":        return False, "진행 중인 팟이 아닙니다."
    if user_id in pot["members"]:            return False, "이미 참여 중인 팟입니다."
    if len(pot["members"]) >= pot["total_people"]: return False, "팟이 이미 꽉 찼습니다."
    pot["members"].append(user_id)
    _save(data)
    return True, "success"


# ── 종료 / 해산 ───────────────────────────────────────────────────────────────

def end_pot(pot_id: str) -> bool:
    """팟 종료 (평가 단계 진입)"""
    data = _load()
    pot  = data.get(pot_id)
    if pot and pot.get("status") == "active":
        pot["status"] = "ended"
        _save(data)
        return True
    return False

def disband_pot(pot_id: str) -> bool:
    """팟 해산 (즉시 삭제 처리)"""
    data = _load()
    pot  = data.get(pot_id)
    if pot and pot.get("status") == "active":
        pot["status"] = "disbanded"
        _save(data)
        return True
    return False

def admin_delete_pot(pot_id: str) -> bool:
    """관리자 팟 강제 삭제"""
    data = _load()
    if pot_id in data:
        del data[pot_id]
        _save(data)
        return True
    return False

def mark_rated(pot_id: str, user_id: str) -> None:
    """평가 완료 표시"""
    data = _load()
    pot  = data.get(pot_id)
    if pot and user_id not in pot.get("rated_by", []):
        pot.setdefault("rated_by", []).append(user_id)
        _save(data)


# ── 아이템 삭제 연동 ─────────────────────────────────────────────────────────

def disband_pots_for_item(item_label: str) -> list[dict]:
    """특정 아이템 레이블의 active 팟을 모두 disbanded 처리. 해당 팟 목록 반환."""
    data   = _load()
    affected = []
    for pot in data.values():
        if pot["item_label"] == item_label and pot.get("status") == "active":
            pot["status"] = "disbanded"
            affected.append(pot)
    _save(data)
    return affected


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def calc_dday(buy_date_str: str) -> str:
    try:
        from datetime import date
        diff = (datetime.strptime(buy_date_str, "%Y-%m-%d").date() - datetime.now().date()).days
        if diff > 0:   return f"D-{diff}"
        elif diff == 0: return "D-Day"
        else:           return f"D+{abs(diff)}"
    except Exception:
        return ""

def price_per_person(pot: dict) -> int:
    n = pot.get("total_people", 1)
    return pot.get("price_total", 0) // max(n, 1)
