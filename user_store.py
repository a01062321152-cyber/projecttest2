"""user_store.py — 유저 + 리스트 데이터 관리"""

import json, hashlib
from pathlib import Path

USER_DB_PATH = Path("users.json")
LIST_DB_PATH = Path("lists.json")


def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def _load_users():
    if USER_DB_PATH.exists():
        return json.loads(USER_DB_PATH.read_text(encoding="utf-8"))
    return {}

def _save_users(db):
    USER_DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

def _load_lists():
    if LIST_DB_PATH.exists():
        return json.loads(LIST_DB_PATH.read_text(encoding="utf-8"))
    return {}

def _save_lists(data):
    LIST_DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 초기화 ────────────────────────────────────────────────────────────────────

def initialize():
    db = _load_users()
    if "admin" not in db:
        db["admin"] = {"name": "admin", "user_id": "admin",
                       "password_hash": _hash("admin"), "is_admin": True}
        _save_users(db)

    lists = _load_lists()
    if not lists:
        lists = {
            "list1": {"title": "List 1 — Title",
                      "items": [{"label": "Item 1", "image_url": "", "price": 0}]},
            "list2": {"title": "List 2 — Title",
                      "items": [{"label": "Item 1", "image_url": "", "price": 0}]},
        }
        _save_lists(lists)
    else:
        changed = False
        for lk in lists:
            for item in lists[lk].get("items", []):
                if "price" not in item:
                    item["price"] = 0
                    changed = True
        if changed:
            _save_lists(lists)


# ── 유저 API ──────────────────────────────────────────────────────────────────

def register_user(name, user_id, password):
    if not name.strip():            return False, "이름을 입력해 주세요."
    if len(user_id.strip()) < 4:   return False, "아이디는 4자 이상이어야 합니다."
    if len(password) < 6:          return False, "비밀번호는 6자 이상이어야 합니다."
    if user_id.strip() == "admin": return False, "사용할 수 없는 아이디입니다."
    db = _load_users()
    if user_id in db:              return False, "이미 사용 중인 아이디입니다."
    db[user_id] = {"name": name.strip(), "user_id": user_id.strip(),
                   "password_hash": _hash(password), "is_admin": False}
    _save_users(db)
    return True, "success"

def login_user(user_id, password):
    if not user_id.strip() or not password: return False, "아이디와 비밀번호를 입력해 주세요."
    db   = _load_users()
    user = db.get(user_id.strip())
    if user is None:                         return False, "존재하지 않는 아이디입니다."
    if user["password_hash"] != _hash(password): return False, "비밀번호가 올바르지 않습니다."
    return True, {k: v for k, v in user.items() if k != "password_hash"}

def get_all_user_ids():
    return list(_load_users().keys())


# ── 리스트 API ────────────────────────────────────────────────────────────────

def get_lists() -> dict:
    return _load_lists()

def get_list_keys() -> list:
    """현재 존재하는 리스트 키 목록 (순서 보존)"""
    return list(_load_lists().keys())

def add_list(title: str) -> str:
    """
    새 리스트 추가. 자동으로 list3, list4... 키 생성.
    생성된 list_key 반환.
    """
    data = _load_lists()
    # 기존 키 중 listN 패턴의 최대 N을 찾아 +1
    existing_nums = []
    for k in data:
        if k.startswith("list"):
            try:
                existing_nums.append(int(k[4:]))
            except ValueError:
                pass
    next_num = max(existing_nums, default=0) + 1
    new_key  = f"list{next_num}"
    data[new_key] = {
        "title": title.strip() or f"List {next_num} — Title",
        "items": [{"label": "Item 1", "image_url": "", "price": 0}],
    }
    _save_lists(data)
    return new_key

def delete_list(list_key: str) -> bool:
    """리스트 전체 삭제. list1·list2는 삭제 불가(기본 리스트 보호). True/False 반환."""
    if list_key in ("list1", "list2"):
        return False
    data = _load_lists()
    if list_key not in data:
        return False
    del data[list_key]
    _save_lists(data)
    return True

def update_list_title(list_key, new_title):
    data = _load_lists()
    data[list_key]["title"] = new_title.strip()
    _save_lists(data)

def add_list_item(list_key, label, image_url="", price=0):
    data = _load_lists()
    data[list_key]["items"].append(
        {"label": label.strip(), "image_url": image_url.strip(), "price": int(price)})
    _save_lists(data)

def update_list_item(list_key, idx, label, image_url, price):
    data = _load_lists()
    data[list_key]["items"][idx] = {
        "label": label.strip(), "image_url": image_url.strip(), "price": int(price)}
    _save_lists(data)

def delete_list_item(list_key, idx) -> dict | None:
    """항목 삭제. 삭제된 항목 dict 반환. 최소 1개 유지."""
    data  = _load_lists()
    items = data[list_key]["items"]
    if len(items) <= 1:
        return None
    removed = items.pop(idx)
    _save_lists(data)
    return removed

