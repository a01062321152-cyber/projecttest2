"""
cvs_store.py — 편의점 파티 데이터
상태: waiting(출발대기) | departed(출발) | arrived(집합완료)
"""
import json, uuid
from pathlib import Path
from datetime import datetime

DB = Path("cvs_parties.json")

def _r():
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else {}

def _w(d):
    DB.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 파티 생성 (유저) ─────────────────────────────────────────────────────────
def create_party(creator_id: str, creator_name: str,
                 depart_time: str, contact: str, account: str,
                 visit_location: str = "", visit_lat: float = 0.0,
                 visit_lng: float = 0.0) -> str:
    d = _r()
    pid = str(uuid.uuid4())[:8]
    d[pid] = {
        "party_id": pid,
        "creator_id": creator_id,
        "creator_name": creator_name,
        "depart_time": depart_time,
        "contact": contact,
        "account": account,
        "visit_location": visit_location,   # 방문할 편의점 위치
        "visit_lat": visit_lat,
        "visit_lng": visit_lng,
        "status": "waiting",
        "orders": [],
        "gather_location": "",
        "gather_lat": 0.0,
        "gather_lng": 0.0,
        "created_at": datetime.now().isoformat(),
    }
    _w(d)
    return pid

# ── 조회 ─────────────────────────────────────────────────────────────────────
def get_waiting_parties() -> list:
    d = _r()
    result = [p for p in d.values() if p["status"] == "waiting"]
    # 출발 시간 오름차순
    return sorted(result, key=lambda x: x["depart_time"])

def get_party(pid: str) -> dict | None:
    return _r().get(pid)

def get_parties_by_user(user_id: str) -> list:
    """내가 파티장이거나 주문자인 파티"""
    d = _r()
    result = []
    for p in d.values():
        if p["creator_id"] == user_id:
            result.append(p); continue
        if any(o["user_id"] == user_id for o in p["orders"]):
            result.append(p)
    return result

def get_all_parties() -> list:
    return list(_r().values())

# ── 상품 신청 ─────────────────────────────────────────────────────────────────
def apply_order(pid: str, user_id: str, name: str,
                item_label: str, item_image: str,
                qty: int, price: int) -> tuple[bool, str]:
    d = _r()
    p = d.get(pid)
    if not p:                       return False, "파티를 찾을 수 없습니다."
    if p["status"] != "waiting":    return False, "출발 대기 중인 파티가 아닙니다."
    p["orders"].append({
        "user_id": user_id, "name": name,
        "item_label": item_label, "item_image": item_image,
        "qty": qty, "price": price,
        "paid": False,      # 입금 여부
        "confirmed": False, # 파티장 합류 확인
    })
    _w(d)
    return True, "success"

# ── 입금확인·합류 (파티장) ────────────────────────────────────────────────────
def confirm_order(pid: str, order_idx: int) -> bool:
    d = _r()
    p = d.get(pid)
    if not p: return False
    if 0 <= order_idx < len(p["orders"]):
        p["orders"][order_idx]["paid"] = True
        p["orders"][order_idx]["confirmed"] = True
        _w(d)
        return True
    return False

# ── 파티 출발 ────────────────────────────────────────────────────────────────
def depart_party(pid: str) -> bool:
    d = _r()
    p = d.get(pid)
    if p and p["status"] == "waiting":
        p["status"] = "departed"
        _w(d)
        return True
    return False

# ── 집합 위치 전송 ────────────────────────────────────────────────────────────
def set_gather_location(pid: str, location: str, lat: float, lng: float) -> bool:
    d = _r()
    p = d.get(pid)
    if not p: return False
    p["gather_location"] = location
    p["gather_lat"] = lat
    p["gather_lng"] = lng
    p["status"] = "arrived"
    _w(d)
    return True

def delete_party(pid: str) -> bool:
    d = _r()
    if pid in d:
        del d[pid]
        _w(d)
        return True
    return False
