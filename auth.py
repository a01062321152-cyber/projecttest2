"""
auth.py
───────
로그인 / 회원가입 / 마이페이지 화면을 렌더링합니다.
project.py에서 render_auth_page() 또는 render_my_page()를 호출해 사용합니다.
"""

import streamlit as st
from user_store import register_user, login_user
import streamlit.components.v1 as components


# ── 공통 CSS (auth 전용) ──────────────────────────────────────────────────────
AUTH_CSS = """
<style>
/* 카드 박스 */
.auth-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 2.6rem 2.4rem 2.2rem;
    max-width: 440px;
    margin: 3rem auto 0;
    box-shadow: 0 4px 32px rgba(0,0,0,0.08);
    border: 1px solid #E5E7EB;
}
.auth-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.7rem;
    color: #1a1a1a;
    margin-bottom: 0.3rem;
}
.auth-sub {
    font-size: 0.85rem;
    color: #9CA3AF;
    margin-bottom: 1.8rem;
}

/* 선택 화면 버튼 */
.choice-row {
    display: flex;
    gap: 1rem;
    max-width: 440px;
    margin: 3rem auto 0;
}
.choice-btn {
    flex: 1;
    padding: 2rem 1rem;
    border-radius: 16px;
    border: 2px solid #E5E7EB;
    background: #fff;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;
    font-family: 'DM Sans', sans-serif;
}
.choice-btn:hover {
    border-color: #3B82F6;
    box-shadow: 0 4px 16px rgba(59,130,246,0.12);
}
.choice-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.choice-label { font-size: 0.95rem; font-weight: 600; color: #1a1a1a; }

/* 프로필 카드 */
.profile-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 2rem 2.4rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    border: 1px solid #E5E7EB;
    display: flex;
    align-items: center;
    gap: 1.6rem;
}
.profile-avatar {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: linear-gradient(135deg, #DBEAFE, #EEF4FF);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    flex-shrink: 0;
    border: 2px solid #3B82F6;
}
.profile-name {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    color: #1a1a1a;
    margin-bottom: 0.2rem;
}
.profile-id {
    font-size: 0.82rem;
    color: #9CA3AF;
    font-weight: 500;
}
.mypage-section-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1a1a1a;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin: 1.6rem 0 0.8rem;
}
</style>
"""


def _card_section_html(title: str, items: list) -> str:
    """마이페이지용 카드 섹션 HTML (components.html로 렌더링)"""
    cards_inner = ""
    for item in items:
        cards_inner += f"""
        <div class="card">
          <div class="card-img"></div>
          <span class="card-label">{item['label']}</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'DM Sans', sans-serif; padding: 0 0 4px 0; }}
  .section-title {{
    font-size: 0.9rem; font-weight: 600; color: #1a1a1a;
    letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.9rem;
  }}
  .card-row {{
    display: flex; gap: 1rem; overflow-x: auto;
    background: #EDEBE5; border-radius: 14px;
    padding: 1rem; border: 1.5px solid #D8D4CB;
  }}
  .card-row::-webkit-scrollbar {{ height: 4px; }}
  .card-row::-webkit-scrollbar-thumb {{ background: #C2BEAF; border-radius: 4px; }}
  .card {{
    flex: 0 0 160px; height: 180px; border-radius: 12px;
    border: 2px solid #3B82F6; background: #fff;
    display: flex; flex-direction: column;
    align-items: center; justify-content: flex-end;
    padding-bottom: 0.8rem; cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    position: relative; overflow: hidden;
  }}
  .card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(59,130,246,0.18); }}
  .card-img {{ position: absolute; inset: 0; background: linear-gradient(135deg, #EEF4FF 0%, #DBEAFE 100%); }}
  .card-label {{
    position: relative; font-size: 0.75rem; font-weight: 600;
    color: #3B82F6; letter-spacing: 0.04em;
    background: rgba(255,255,255,0.85); padding: 0.2rem 0.6rem; border-radius: 20px;
  }}
</style>
</head>
<body>
  <div class="section-title">{title}</div>
  <div class="card-row">{cards_inner}</div>
</body></html>"""


# ── 공개 렌더링 함수 ──────────────────────────────────────────────────────────

def render_auth_page():
    """
    비로그인 상태에서 마이페이지 클릭 시 표시되는 화면.
    session_state.auth_step 에 따라 선택 → 로그인 / 회원가입 화면 전환.
    """
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    # auth_step: "choice" | "login" | "register"
    if "auth_step" not in st.session_state:
        st.session_state.auth_step = "choice"

    step = st.session_state.auth_step

    # ── 선택 화면 ──────────────────────────────────────────────────────────
    if step == "choice":
        st.markdown("""
        <div style="text-align:center; margin-top:2.5rem;">
            <p style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:#1a1a1a;margin-bottom:0.3rem">
                My Page
            </p>
            <p style="font-size:0.85rem;color:#9CA3AF;margin-bottom:0;">
                로그인하거나 새 계정을 만들어 보세요
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑\n\n로그인", use_container_width=True, key="go_login"):
                st.session_state.auth_step = "login"
                st.rerun()
        with col2:
            if st.button("✏️\n\n회원가입", use_container_width=True, key="go_register"):
                st.session_state.auth_step = "register"
                st.rerun()

        # 선택 버튼 스타일
        st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"]:not(:last-child) button {
            height: 120px !important;
            font-size: 1rem !important;
            border-radius: 16px !important;
            border: 2px solid #E5E7EB !important;
            background: #fff !important;
            color: #1a1a1a !important;
            font-weight: 600 !important;
            white-space: pre-line !important;
        }
        div[data-testid="stHorizontalBlock"]:not(:last-child) button:hover {
            border-color: #3B82F6 !important;
            box-shadow: 0 4px 16px rgba(59,130,246,0.14) !important;
            background: #F0F7FF !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # ── 로그인 화면 ────────────────────────────────────────────────────────
    elif step == "login":
        st.markdown("""
        <div class="auth-card">
            <div class="auth-title">로그인</div>
            <div class="auth-sub">아이디와 비밀번호를 입력하세요</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            user_id = st.text_input("아이디", placeholder="아이디를 입력하세요")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            ok, result = login_user(user_id, password)
            if ok:
                st.session_state.user = result          # 유저 정보 저장
                st.session_state.auth_step = "choice"   # 초기화
                st.session_state.page = "my"
                st.success(f"환영합니다, {result['name']}님!")
                st.rerun()
            else:
                st.error(result)

        if st.button("← 뒤로", key="back_from_login"):
            st.session_state.auth_step = "choice"
            st.rerun()

    # ── 회원가입 화면 ──────────────────────────────────────────────────────
    elif step == "register":
        st.markdown("""
        <div class="auth-card">
            <div class="auth-title">회원가입</div>
            <div class="auth-sub">기본 정보를 입력하고 계정을 만드세요</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("register_form"):
            name     = st.text_input("이름", placeholder="홍길동")
            user_id  = st.text_input("아이디", placeholder="4자 이상")
            password = st.text_input("비밀번호", type="password", placeholder="6자 이상")
            submitted = st.form_submit_button("계정 만들기", use_container_width=True)

        if submitted:
            ok, msg = register_user(name, user_id, password)
            if ok:
                st.success("회원가입이 완료됐습니다! 로그인해 주세요.")
                st.session_state.auth_step = "login"
                st.rerun()
            else:
                st.error(msg)

        if st.button("← 뒤로", key="back_from_register"):
            st.session_state.auth_step = "choice"
            st.rerun()


def render_my_page():
    """
    로그인 상태에서 마이페이지 화면.
    프로필 정보 + 리스트 2개 + 로그아웃 버튼.
    """
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    user = st.session_state.get("user", {})
    name    = user.get("name", "사용자")
    user_id = user.get("user_id", "")

    # ── 프로필 카드 ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="profile-card">
        <div class="profile-avatar">👤</div>
        <div>
            <div class="profile-name">{name}</div>
            <div class="profile-id">@{user_id}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 로그아웃 버튼
    if st.button("로그아웃", key="logout_btn"):
        st.session_state.pop("user", None)
        st.session_state.page = "my"
        st.session_state.auth_step = "choice"
        st.rerun()

    # ── 내 리스트 1 ────────────────────────────────────────────────────────
    st.markdown('<div class="mypage-section-title">My List 1</div>', unsafe_allow_html=True)
    components.html(
        _card_section_html("", [
            {"label": "Item A"}, {"label": "Item B"},
            {"label": "Item C"}, {"label": "Item D"}, {"label": "Item E"},
        ]),
        height=250, scrolling=False,
    )

    # ── 내 리스트 2 ────────────────────────────────────────────────────────
    st.markdown('<div class="mypage-section-title">My List 2</div>', unsafe_allow_html=True)
    components.html(
        _card_section_html("", [
            {"label": "Item 1"}, {"label": "Item 2"},
            {"label": "Item 3"}, {"label": "Item 4"},
        ]),
        height=250, scrolling=False,
    )
