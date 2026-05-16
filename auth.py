"""
auth.py  —  로그인 / 회원가입 / 마이페이지 UI
"""

import streamlit as st
import streamlit.components.v1 as components
from user_store import register_user, login_user, get_lists
from pot_store  import get_pots_by_user, calc_dday, price_per_person

AUTH_CSS = """
<style>
.auth-card {
    background:#fff; border-radius:20px; padding:2.6rem 2.4rem 2.2rem;
    max-width:440px; margin:3rem auto 0;
    box-shadow:0 4px 32px rgba(0,0,0,0.08); border:1px solid #E5E7EB;
}
.auth-title { font-family:'DM Serif Display',serif; font-size:1.7rem; color:#1a1a1a; margin-bottom:0.3rem; }
.auth-sub   { font-size:0.85rem; color:#9CA3AF; margin-bottom:1.8rem; }
.profile-card {
    background:#fff; border-radius:20px; padding:2rem 2.4rem; margin-bottom:1.2rem;
    box-shadow:0 4px 24px rgba(0,0,0,0.06); border:1px solid #E5E7EB;
    display:flex; align-items:center; gap:1.6rem;
}
.profile-avatar {
    width:72px; height:72px; border-radius:50%;
    background:linear-gradient(135deg,#DBEAFE,#EEF4FF);
    display:flex; align-items:center; justify-content:center;
    font-size:2rem; flex-shrink:0; border:2px solid #3B82F6;
}
.admin-badge {
    display:inline-block; background:#FEF3C7; color:#D97706;
    font-size:0.7rem; font-weight:700; padding:0.1rem 0.5rem;
    border-radius:20px; letter-spacing:0.05em; margin-left:0.4rem;
}
.profile-name { font-family:'DM Serif Display',serif; font-size:1.4rem; color:#1a1a1a; margin-bottom:0.2rem; }
.profile-id   { font-size:0.82rem; color:#9CA3AF; font-weight:500; }
.mypage-section-title {
    font-size:0.9rem; font-weight:600; color:#1a1a1a;
    letter-spacing:0.06em; text-transform:uppercase; margin:1.6rem 0 0.8rem;
}
/* 팟 카드 (마이페이지용) */
.my-pot-card {
    border:1.5px solid #DBEAFE; border-radius:14px;
    padding:1rem 1.2rem; margin-bottom:0.8rem;
    background:#F0F7FF; position:relative;
}
.my-pot-dday {
    position:absolute; top:0.7rem; right:0.9rem;
    font-size:0.68rem; font-weight:800; color:#EF4444;
    background:#FEE2E2; padding:0.15rem 0.55rem; border-radius:20px;
    letter-spacing:0.04em;
}
.my-pot-item  { font-weight:700; color:#1a1a1a; font-size:0.95rem; margin-bottom:0.25rem; }
.my-pot-meta  { font-size:0.78rem; color:#6B7280; }
.my-pot-price { font-weight:700; color:#3B82F6; font-size:0.9rem; margin-top:0.25rem; }
</style>
"""


def _general_card_html(items: list) -> str:
    """일반 카드 슬라이더 HTML"""
    cards = ""
    for item in items:
        label = item.get("label","")
        img   = item.get("image_url","")
        bg    = f"url('{img}') center/cover no-repeat" if img else "linear-gradient(135deg,#EEF4FF,#DBEAFE)"
        cards += f"""
        <div class="card">
          <div class="card-img" style="background:{bg};"></div>
          <span class="card-label">{label}</span>
        </div>"""

    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:transparent;font-family:'DM Sans',sans-serif;padding:0 0 4px 0;}}
  .card-row{{display:flex;gap:1rem;overflow-x:auto;background:#EDEBE5;
    border-radius:14px;padding:1rem;border:1.5px solid #D8D4CB;}}
  .card-row::-webkit-scrollbar{{height:4px;}}
  .card-row::-webkit-scrollbar-thumb{{background:#C2BEAF;border-radius:4px;}}
  .card{{flex:0 0 160px;height:180px;border-radius:12px;border:2px solid #3B82F6;
    background:#fff;display:flex;flex-direction:column;align-items:center;
    justify-content:flex-end;padding-bottom:0.8rem;cursor:pointer;
    transition:transform 0.18s,box-shadow 0.18s;position:relative;overflow:hidden;}}
  .card:hover{{transform:translateY(-4px);box-shadow:0 8px 24px rgba(59,130,246,0.18);}}
  .card-img{{position:absolute;inset:0;}}
  .card-label{{position:relative;font-size:0.75rem;font-weight:600;color:#3B82F6;
    letter-spacing:0.04em;background:rgba(255,255,255,0.85);
    padding:0.2rem 0.6rem;border-radius:20px;}}
</style></head><body>
  <div class="card-row">{cards}</div>
</body></html>"""


# ── 비로그인: 선택 / 로그인 / 회원가입 ───────────────────────────────────────

def render_auth_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    if "auth_step" not in st.session_state:
        st.session_state.auth_step = "choice"
    step = st.session_state.auth_step

    if step == "choice":
        st.markdown("""
        <div style="text-align:center;margin-top:2.5rem;">
          <p style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:#1a1a1a;margin-bottom:0.3rem">My Page</p>
          <p style="font-size:0.85rem;color:#9CA3AF;">로그인하거나 새 계정을 만들어 보세요</p>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑\n\n로그인", use_container_width=True, key="go_login"):
                st.session_state.auth_step = "login"; st.rerun()
        with col2:
            if st.button("✏️\n\n회원가입", use_container_width=True, key="go_register"):
                st.session_state.auth_step = "register"; st.rerun()

        st.markdown("""<style>
        div[data-testid="stHorizontalBlock"]:not(:last-child) button {
            height:120px !important;font-size:1rem !important;
            border-radius:16px !important;border:2px solid #E5E7EB !important;
            background:#fff !important;color:#1a1a1a !important;
            font-weight:600 !important;white-space:pre-line !important;
        }
        div[data-testid="stHorizontalBlock"]:not(:last-child) button:hover {
            border-color:#3B82F6 !important;
            box-shadow:0 4px 16px rgba(59,130,246,0.14) !important;
            background:#F0F7FF !important;
        }
        </style>""", unsafe_allow_html=True)

    elif step == "login":
        st.markdown("""<div class="auth-card">
          <div class="auth-title">로그인</div>
          <div class="auth-sub">아이디와 비밀번호를 입력하세요</div>
        </div>""", unsafe_allow_html=True)

        with st.form("login_form"):
            uid    = st.text_input("아이디", placeholder="아이디를 입력하세요")
            pw     = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            ok_btn = st.form_submit_button("로그인", use_container_width=True)

        if ok_btn:
            ok, result = login_user(uid, pw)
            if ok:
                st.session_state.user = result
                st.session_state.auth_step = "choice"
                st.session_state.page = "my"
                st.rerun()
            else:
                st.error(result)

        if st.button("← 뒤로", key="back_login"):
            st.session_state.auth_step = "choice"; st.rerun()

    elif step == "register":
        st.markdown("""<div class="auth-card">
          <div class="auth-title">회원가입</div>
          <div class="auth-sub">기본 정보를 입력하고 계정을 만드세요</div>
        </div>""", unsafe_allow_html=True)

        with st.form("register_form"):
            name   = st.text_input("이름", placeholder="홍길동")
            uid    = st.text_input("아이디", placeholder="4자 이상")
            pw     = st.text_input("비밀번호", type="password", placeholder="6자 이상")
            ok_btn = st.form_submit_button("계정 만들기", use_container_width=True)

        if ok_btn:
            ok, msg = register_user(name, uid, pw)
            if ok:
                st.success("회원가입 완료! 로그인해 주세요.")
                st.session_state.auth_step = "login"; st.rerun()
            else:
                st.error(msg)

        if st.button("← 뒤로", key="back_register"):
            st.session_state.auth_step = "choice"; st.rerun()


# ── 로그인 상태: 마이페이지 ───────────────────────────────────────────────────

def render_my_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    user     = st.session_state.get("user", {})
    name     = user.get("name", "사용자")
    user_id  = user.get("user_id", "")
    is_admin = user.get("is_admin", False)

    badge = '<span class="admin-badge">ADMIN</span>' if is_admin else ""
    st.markdown(f"""
    <div class="profile-card">
      <div class="profile-avatar">{"🛡️" if is_admin else "👤"}</div>
      <div>
        <div class="profile-name">{name}{badge}</div>
        <div class="profile-id">@{user_id}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    if st.button("로그아웃", key="logout_btn"):
        st.session_state.pop("user", None)
        st.session_state.page = "my"
        st.session_state.auth_step = "choice"
        st.rerun()

    # ── 내 팟 목록 (첫 번째 리스트) ──────────────────────────────────────
    st.markdown('<div class="mypage-section-title">🛒 내 구메팟</div>', unsafe_allow_html=True)
    my_pots = get_pots_by_user(user_id)

    if not my_pots:
        st.info("참여 중인 구메팟이 없습니다. 메인에서 팟을 찾거나 만들어 보세요!")
    else:
        for pot in my_pots:
            dday    = calc_dday(pot["buy_date"])
            ppp     = price_per_person(pot)
            members = len(pot["members"])
            total   = pot["total_people"]

            st.markdown(f"""
            <div class="my-pot-card">
              <div class="my-pot-dday">{dday}</div>
              <div class="my-pot-item">🛍️ {pot['item_label']}</div>
              <div class="my-pot-meta">👥 {members}/{total}명 · 📅 {pot['buy_date']} · 📍 {pot['location_name']}</div>
              <div class="my-pot-price">인당 {ppp:,}원</div>
            </div>
            """, unsafe_allow_html=True)

    # ── 두 번째 리스트 (list2) ────────────────────────────────────────────
    lists  = get_lists()
    list2  = lists.get("list2", {})
    title2 = list2.get("title", "List 2")
    items2 = list2.get("items", [])

    st.markdown(f'<div class="mypage-section-title">{title2}</div>', unsafe_allow_html=True)
    components.html(_general_card_html(items2), height=240, scrolling=False)
