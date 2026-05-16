"""
essentials_store.py — 생필품 정기구메 파티 데이터
상태: open | closed | rated (평가완료)
"""
import json, uuid
from pathlib import Path
from datetime import datetime

DB = Path("essentials_parties.json")

def _r():
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else {}

def _w(d):
    DB.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 파티 생성 (관리자만) ─────────────────────────────────────────────────────
def create_party(item_label: str, item_image: str, admin_id: str) -> str:
    d = _r()
    pid = str(uuid.uuid4())[:8]
    from datetime import timedelta
    deadline = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    d[pid] = {
        "party_id": pid,
        "item_label": item_label,
        "item_image": item_image,
        "admin_id": admin_id,
        "status": "open",
        "applicants": [],
        "price_per_unit": 0,
        "payment_dest": "",
        "deadline": deadline,
        "ratings": {},
        "credits_given": [],
        "created_at": datetime.now().isoformat(),
    }
    _w(d)
    return pid

# ── 조회 ─────────────────────────────────────────────────────────────────────
def _migrate(p: dict) -> dict:
    p.setdefault("ratings", {})
    p.setdefault("credits_given", [])
    if "deadline" not in p:
        # 기존 파티는 생성일 기준 7일 후
        try:
            from datetime import timedelta
            created = datetime.fromisoformat(p["created_at"])
            p["deadline"] = (created + timedelta(days=7)).strftime("%Y-%m-%d")
        except Exception:
            p["deadline"] = ""
    return p

def get_open_parties(item_label: str) -> list:
    return [_migrate(p) for p in _r().values()
            if p["item_label"] == item_label and p["status"] == "open"]

def get_party(pid: str) -> dict | None:
    p = _r().get(pid)
    return _migrate(p) if p else None

def get_all_parties() -> list:
    return [_migrate(p) for p in _r().values()]

# ── 신청 ─────────────────────────────────────────────────────────────────────
def apply_party(pid: str, user_id: str, name: str,
                contact: str, qty: int) -> tuple[bool, str]:
    d = _r()
    p = d.get(pid)
    if not p:                       return False, "파티를 찾을 수 없습니다."
    if p["status"] != "open":       return False, "마감된 파티입니다."
    for a in p["applicants"]:
        if a["user_id"] == user_id: return False, "이미 신청한 파티입니다."
    p["applicants"].append({
        "user_id": user_id, "name": name,
        "contact": contact, "qty": int(qty),
    })
    _w(d)
    return True, "success"

def cancel_apply(pid: str, user_id: str) -> bool:
    d = _r()
    p = d.get(pid)
    if not p: return False
    p["applicants"] = [a for a in p["applicants"] if a["user_id"] != user_id]
    _w(d)
    return True

# ── 마감 (관리자) ────────────────────────────────────────────────────────────
def close_party(pid: str, price_per_unit: int, payment_dest: str) -> dict | None:
    d = _r()
    p = d.get(pid)
    if not p: return None
    p["status"] = "closed"
    p["price_per_unit"] = price_per_unit
    p["payment_dest"] = payment_dest
    _w(d)
    return p

# ── 평가 저장 (관리자) ────────────────────────────────────────────────────────
def save_ratings(pid: str, ratings: dict) -> bool:
    """ratings: {user_id: score(1~5)}"""
    d = _r()
    p = d.get(pid)
    if not p: return False
    p["ratings"] = ratings
    p["status"] = "rated"
    _w(d)
    return True

# ── 크래딧 지급 기록 ─────────────────────────────────────────────────────────
def mark_credit_given(pid: str, user_id: str):
    d = _r()
    p = d.get(pid)
    if p:
        p.setdefault("credits_given", [])
        if user_id not in p["credits_given"]:
            p["credits_given"].append(user_id)
        _w(d)

def is_credit_given(pid: str, user_id: str) -> bool:
    p = get_party(pid)
    return p is not None and user_id in p.get("credits_given", [])

# ── 삭제 ─────────────────────────────────────────────────────────────────────
def delete_party(pid: str) -> bool:
    d = _r()
    if pid in d:
        del d[pid]
        _w(d)
        return True
    return False
