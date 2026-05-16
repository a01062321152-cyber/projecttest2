"""
user_store.py
─────────────
유저 데이터를 JSON 파일로 로컬에 저장·관리합니다.
Streamlit Cloud 환경에서는 재시작 시 초기화되므로,
실제 서비스라면 DB(SQLite, Supabase 등)로 교체하세요.
"""

import json
import hashlib
import os
from pathlib import Path

# 유저 데이터 저장 경로
USER_DB_PATH = Path("users.json")


def _load_db() -> dict:
    """JSON 파일에서 유저 DB 로드"""
    if USER_DB_PATH.exists():
        with open(USER_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_db(db: dict) -> None:
    """유저 DB를 JSON 파일에 저장"""
    with open(USER_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _hash_password(password: str) -> str:
    """비밀번호 SHA-256 해싱"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ── 공개 API ──────────────────────────────────────────────────────────────────

def register_user(name: str, user_id: str, password: str) -> tuple[bool, str]:
    """
    회원가입
    Returns:
        (True, "success")  → 성공
        (False, "reason")  → 실패 사유
    """
    if not name.strip():
        return False, "이름을 입력해 주세요."
    if not user_id.strip():
        return False, "아이디를 입력해 주세요."
    if len(user_id) < 4:
        return False, "아이디는 4자 이상이어야 합니다."
    if len(password) < 6:
        return False, "비밀번호는 6자 이상이어야 합니다."

    db = _load_db()
    if user_id in db:
        return False, "이미 사용 중인 아이디입니다."

    db[user_id] = {
        "name": name.strip(),
        "user_id": user_id.strip(),
        "password_hash": _hash_password(password),
    }
    _save_db(db)
    return True, "success"


def login_user(user_id: str, password: str) -> tuple[bool, str | dict]:
    """
    로그인
    Returns:
        (True, user_dict)   → 성공, 유저 정보 반환
        (False, "reason")   → 실패 사유
    """
    if not user_id.strip() or not password:
        return False, "아이디와 비밀번호를 입력해 주세요."

    db = _load_db()
    user = db.get(user_id.strip())
    if user is None:
        return False, "존재하지 않는 아이디입니다."
    if user["password_hash"] != _hash_password(password):
        return False, "비밀번호가 올바르지 않습니다."

    # 비밀번호 해시 제외하고 반환
    return True, {k: v for k, v in user.items() if k != "password_hash"}


def get_user(user_id: str) -> dict | None:
    """유저 정보 조회 (비밀번호 해시 제외)"""
    db = _load_db()
    user = db.get(user_id)
    if user is None:
        return None
    return {k: v for k, v in user.items() if k != "password_hash"}
