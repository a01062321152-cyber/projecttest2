"""
user_store.py
─────────────
유저 데이터(JSON) + 메인 리스트 데이터(JSON) 관리.
앱 최초 실행 시 admin 계정과 기본 리스트를 자동 생성합니다.
"""

import json
import hashlib
from pathlib import Path

USER_DB_PATH  = Path("users.json")
LIST_DB_PATH  = Path("lists.json")

# ── 내부 유틸 ─────────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _load_users() -> dict:
    if USER_DB_PATH.exists():
        return json.loads(USER_DB_PATH.read_text(encoding="utf-8"))
    return {}

def _save_users(db: dict) -> None:
    USER_DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

def _load_lists() -> dict:
    if LIST_DB_PATH.exists():
        return json.loads(LIST_DB_PATH.read_text(encoding="utf-8"))
    return {}

def _save_lists(data: dict) -> None:
    LIST_DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 초기화: admin 계정 + 기본 리스트 ─────────────────────────────────────────

def initialize():
    """앱 시작 시 1회 호출. admin 계정과 기본 리스트를 없으면 생성."""
    # admin 계정
    db = _load_users()
    if "admin" not in db:
        db["admin"] = {
            "name": "admin",
            "user_id": "admin",
            "password_hash": _hash("admin"),
            "is_admin": True,
        }
        _save_users(db)

    # 기본 리스트 데이터
    lists = _load_lists()
    if not lists:
        lists = {
            "list1": {
                "title": "List 1 — Title",
                "items": [{"label": "Item 1", "image_url": ""}],
            },
            "list2": {
                "title": "List 2 — Title",
                "items": [{"label": "Item 1", "image_url": ""}],
            },
        }
        _save_lists(lists)

# ── 유저 API ──────────────────────────────────────────────────────────────────

def register_user(name: str, user_id: str, password: str) -> tuple[bool, str]:
    if not name.strip():
        return False, "이름을 입력해 주세요."
    if len(user_id.strip()) < 4:
        return False, "아이디는 4자 이상이어야 합니다."
    if len(password) < 6:
        return False, "비밀번호는 6자 이상이어야 합니다."
    if user_id.strip() == "admin":
        return False, "사용할 수 없는 아이디입니다."

    db = _load_users()
    if user_id in db:
        return False, "이미 사용 중인 아이디입니다."

    db[user_id] = {
        "name": name.strip(),
        "user_id": user_id.strip(),
        "password_hash": _hash(password),
        "is_admin": False,
    }
    _save_users(db)
    return True, "success"


def login_user(user_id: str, password: str) -> tuple[bool, str | dict]:
    if not user_id.strip() or not password:
        return False, "아이디와 비밀번호를 입력해 주세요."

    db = _load_users()
    user = db.get(user_id.strip())
    if user is None:
        return False, "존재하지 않는 아이디입니다."
    if user["password_hash"] != _hash(password):
        return False, "비밀번호가 올바르지 않습니다."

    return True, {k: v for k, v in user.items() if k != "password_hash"}

# ── 리스트 API ────────────────────────────────────────────────────────────────

def get_lists() -> dict:
    """list1, list2 전체 데이터 반환"""
    return _load_lists()


def update_list_title(list_key: str, new_title: str) -> None:
    """리스트 제목 수정 (list_key: 'list1' | 'list2')"""
    data = _load_lists()
    data[list_key]["title"] = new_title.strip()
    _save_lists(data)


def add_list_item(list_key: str, label: str, image_url: str = "") -> None:
    """리스트에 항목 추가"""
    data = _load_lists()
    data[list_key]["items"].append({"label": label.strip(), "image_url": image_url.strip()})
    _save_lists(data)


def update_list_item(list_key: str, idx: int, label: str, image_url: str) -> None:
    """리스트 항목 수정"""
    data = _load_lists()
    data[list_key]["items"][idx] = {"label": label.strip(), "image_url": image_url.strip()}
    _save_lists(data)


def delete_list_item(list_key: str, idx: int) -> None:
    """리스트 항목 삭제"""
    data = _load_lists()
    items = data[list_key]["items"]
    if len(items) > 1:          # 최소 1개 유지
        items.pop(idx)
    _save_lists(data)
