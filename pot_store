"""
pot_store.py
─────────────
구메팟 데이터를 JSON 파일로 관리합니다.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime

POT_DB_PATH = Path("pots.json")


def _load() -> dict:
    if POT_DB_PATH.exists():
        return json.loads(POT_DB_PATH.read_text(encoding="utf-8"))
    return {}


def _save(data: dict) -> None:
    POT_DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 팟 생성 ──────────────────────────────────────────────────────────────────

def create_pot(
    item_label: str,
    item_image: str,
    creator_id: str,
    creator_name: str,
    total_people: int,
    buy_date: str,          # "YYYY-MM-DD"
    location_name: str,
    location_lat: float,
    location_lng: float,
    price_total: int,       # 총 가격 (원)
) -> str:
    """팟 생성 후 pot_id 반환"""
    data = _load()
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
        "members": [creator_id],        # 생성자 자동 참여
        "created_at": datetime.now().isoformat(),
    }
    _save(data)
    return pot_id


# ── 팟 조회 ──────────────────────────────────────────────────────────────────

def get_pots_for_item(item_label: str) -> list[dict]:
    """특정 아이템의 팟 목록 반환 (최신순)"""
    data = _load()
    result = [p for p in data.values() if p["item_label"] == item_label]
    return sorted(result, key=lambda x: x["created_at"], reverse=True)


def get_pots_by_user(user_id: str) -> list[dict]:
    """내가 참여 중인 팟 목록 반환"""
    data = _load()
    return [p for p in data.values() if user_id in p.get("members", [])]


def get_pot(pot_id: str) -> dict | None:
    return _load().get(pot_id)


# ── 팟 참여 ──────────────────────────────────────────────────────────────────

def join_pot(pot_id: str, user_id: str) -> tuple[bool, str]:
    data = _load()
    pot = data.get(pot_id)
    if pot is None:
        return False, "팟을 찾을 수 없습니다."
    if user_id in pot["members"]:
        return False, "이미 참여 중인 팟입니다."
    if len(pot["members"]) >= pot["total_people"]:
        return False, "팟이 이미 꽉 찼습니다."
    pot["members"].append(user_id)
    _save(data)
    return True, "success"


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def calc_dday(buy_date_str: str) -> str:
    """D-day 문자열 반환 (예: D-3, D-Day, D+2)"""
    try:
        target = datetime.strptime(buy_date_str, "%Y-%m-%d").date()
        today  = datetime.now().date()
        diff   = (target - today).days
        if diff > 0:
            return f"D-{diff}"
        elif diff == 0:
            return "D-Day"
        else:
            return f"D+{abs(diff)}"
    except Exception:
        return ""


def price_per_person(pot: dict) -> int:
    """인당 가격"""
    n = pot.get("total_people", 1)
    return pot.get("price_total", 0) // max(n, 1)
