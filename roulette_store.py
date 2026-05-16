"""
roulette_store.py — 룰렛 상품 데이터
"""
import json, uuid, random
from pathlib import Path
from datetime import datetime

DB = Path("roulette_items.json")
SPIN_LOG = Path("roulette_spins.json")

def _r():
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else {}

def _w(d):
    DB.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def _rl():
    return json.loads(SPIN_LOG.read_text(encoding="utf-8")) if SPIN_LOG.exists() else {}

def _wl(d):
    SPIN_LOG.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 상품 등록 ─────────────────────────────────────────────────────────────────
def register_item(owner_id: str, owner_name: str, owner_temp: float,
                  item_name: str, item_desc: str, contact: str,
                  image_url: str = "") -> str:
    d = _r()
    rid = str(uuid.uuid4())[:8]
    d[rid] = {
        "roulette_id": rid,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "owner_temp": owner_temp,
        "item_name": item_name,
        "item_desc": item_desc,
        "contact": contact,
        "image_url": image_url,
        "status": "active",       # active | won | removed
        "winner_id": None,
        "spin_count": 0,          # 총 시도 횟수
        "created_at": datetime.now().isoformat(),
    }
    _w(d)
    return rid

# ── 조회 ─────────────────────────────────────────────────────────────────────
def get_active_items(exclude_user_id: str = "") -> list:
    """본인 제외, active 상품만"""
    d = _r()
    return [v for v in d.values()
            if v["status"] == "active" and v["owner_id"] != exclude_user_id]

def get_my_items(owner_id: str) -> list:
    return [v for v in _r().values() if v["owner_id"] == owner_id]

def get_item(rid: str) -> dict | None:
    return _r().get(rid)

# ── 룰렛 돌리기 ───────────────────────────────────────────────────────────────
def spin(rid: str, user_id: str) -> tuple[bool, str]:
    """
    20개 중 1개 뽑기. 꽝이면 다음엔 19개 중 1개...
    spin_count 기반으로 확률 계산.
    Returns (is_win, message)
    """
    d = _r()
    item = d.get(rid)
    if not item:                    return False, "상품을 찾을 수 없습니다."
    if item["status"] != "active":  return False, "이미 당첨된 상품입니다."
    if item["owner_id"] == user_id: return False, "본인 상품은 참여할 수 없습니다."

    # 이미 이 상품에 참여했는지 확인
    log = _rl()
    user_spins = log.get(user_id, [])
    if rid in user_spins:           return False, "이미 참여한 상품입니다."

    # 확률: 20 - spin_count 중 1개 (최소 1/2)
    total = max(2, 20 - item["spin_count"])
    is_win = (random.randint(1, total) == 1)

    item["spin_count"] += 1

    if is_win:
        item["status"] = "won"
        item["winner_id"] = user_id

    _w(d)

    # 참여 기록
    if user_id not in log:
        log[user_id] = []
    log[user_id].append(rid)
    _wl(log)

    return is_win, "win" if is_win else f"꽝 (다음 확률: 1/{max(1, total-1)})"

def remove_item(rid: str, owner_id: str) -> bool:
    d = _r()
    item = d.get(rid)
    if item and item["owner_id"] == owner_id:
        item["status"] = "removed"
        _w(d)
        return True
    return False

def has_spun(rid: str, user_id: str) -> bool:
    return rid in _rl().get(user_id, [])
