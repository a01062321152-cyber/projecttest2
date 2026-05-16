"""auth.py — 로그인 / 회원가입 / 마이페이지"""

import streamlit as st

from user_store         import register_user, login_user
from rating_store       import get_temperature, get_score_count, temp_color, temp_label
from notification_store import push_all
from essentials_store   import get_all_parties as ess_all
from cvs_store          import get_parties_by_user as cvs_by_user, get_all_parties as cvs_all

AUTH_CSS = """
<style>
.auth-card{background:#fff;border-radius:20px;padding:2.6rem 2.4rem 2.2rem;
  max-width:440px;margin:3rem auto 0;
  box-shadow:0 4px 32px rgba(0,0,0,.08);border:1px solid #E5E7EB;}
.auth-title{font-family:'DM Serif Display',serif;font-size:1.7rem;color:#1a1a1a;margin-bottom:.3rem;}
.auth-sub{font-size:.85rem;color:#9CA3AF;margin-bottom:1.8rem;}
.profile-card{background:#fff;border-radius:20px;padding:2rem 2.4rem;
  margin-bottom:1.2rem;box-shadow:0 4px 24px rgba(0,0,0,.06);border:1px solid #E5E7EB;
  display:flex;align-items:center;gap:1.6rem;}
.profile-avatar{width:72px;height:72px;border-radius:50%;
  background:linear-gradient(135deg,#DBEAFE,#EEF4FF);
  display:flex;align-items:center;justify-content:center;
  font-size:2rem;flex-shrink:0;border:2px solid #3B82F6;}
.admin-badge{display:inline-block;background:#FEF3C7;color:#D97706;
  font-size:.7rem;font-weight:700;padding:.1rem .5rem;border-radius:20px;margin-left:.4rem;}
.profile-name{font-family:'DM Serif Display',serif;font-size:1.4rem;color:#1a1a1a;margin-bottom:.2rem;}
.profile-id{font-size:.82rem;color:#9CA3AF;font-weight:500;}
.mypage-section-title{font-size:.9rem;font-weight:600;color:#1a1a1a;
  letter-spacing:.06em;text-transform:uppercase;margin:1.6rem 0 .8rem;}
.temp-bar-wrap{background:#F3F4F6;border-radius:20px;height:12px;margin:.4rem 0 .2rem;overflow:hidden;}
.temp-bar{height:100%;border-radius:20px;transition:width .4s;}
.admin-pot-card{border:1.5px solid #E5E7EB;border-radius:12px;
  padding:.8rem 1rem;margin-bottom:.6rem;background:#FAFAFA;}
</style>
"""

# ── 비로그인 ──────────────────────────────────────────────────────────────────

def render_auth_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    if "auth_step" not in st.session_state:
        st.session_state.auth_step = "choice"
    step = st.session_state.auth_step

    if step == "choice":
        st.markdown("""
        <div style="text-align:center;margin-top:2.5rem;">
          <p style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:#1a1a1a;margin-bottom:.3rem">My Page</p>
          <p style="font-size:.85rem;color:#9CA3AF;">로그인하거나 새 계정을 만들어 보세요</p>
        </div>""", unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            if st.button("🔑\n\n로그인",  use_container_width=True, key="go_login"):
                st.session_state.auth_step="login"; st.rerun()
        with c2:
            if st.button("✏️\n\n회원가입", use_container_width=True, key="go_register"):
                st.session_state.auth_step="register"; st.rerun()
        st.markdown("""<style>
        div[data-testid="stHorizontalBlock"]:not(:last-child) button{
          height:120px !important;font-size:1rem !important;border-radius:16px !important;
          border:2px solid #E5E7EB !important;background:#fff !important;
          color:#1a1a1a !important;font-weight:600 !important;white-space:pre-line !important;}
        div[data-testid="stHorizontalBlock"]:not(:last-child) button:hover{
          border-color:#3B82F6 !important;background:#F0F7FF !important;}
        </style>""", unsafe_allow_html=True)

    elif step == "login":
        st.markdown("""<div class="auth-card">
          <div class="auth-title">로그인</div>
          <div class="auth-sub">아이디와 비밀번호를 입력하세요</div></div>""",
                    unsafe_allow_html=True)
        with st.form("login_form"):
            uid    = st.text_input("아이디")
            pw     = st.text_input("비밀번호", type="password")
            ok_btn = st.form_submit_button("로그인", use_container_width=True)
        if ok_btn:
            ok, result = login_user(uid, pw)
            if ok:
                st.session_state.user=result
                st.session_state.auth_step="choice"
                st.session_state.page="my"; st.rerun()
            else: st.error(result)
        if st.button("← 뒤로", key="back_login"):
            st.session_state.auth_step="choice"; st.rerun()

    elif step == "register":
        st.markdown("""<div class="auth-card">
          <div class="auth-title">회원가입</div>
          <div class="auth-sub">기본 정보를 입력하고 계정을 만드세요</div></div>""",
                    unsafe_allow_html=True)
        with st.form("register_form"):
            name   = st.text_input("이름")
            uid    = st.text_input("아이디", placeholder="4자 이상")
            pw     = st.text_input("비밀번호", type="password", placeholder="6자 이상")
            ok_btn = st.form_submit_button("계정 만들기", use_container_width=True)
        if ok_btn:
            ok, msg = register_user(name, uid, pw)
            if ok:
                st.success("회원가입 완료!"); st.session_state.auth_step="login"; st.rerun()
            else: st.error(msg)
        if st.button("← 뒤로", key="back_register"):
            st.session_state.auth_step="choice"; st.rerun()


# ── 마이페이지 ────────────────────────────────────────────────────────────────

def render_my_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    user     = st.session_state.get("user", {})
    name     = user.get("name","사용자")
    uid      = user.get("user_id","")
    is_admin = user.get("is_admin", False)

    badge = '<span class="admin-badge">ADMIN</span>' if is_admin else ""
    st.markdown(f"""
    <div class="profile-card">
      <div class="profile-avatar">{"🛡️" if is_admin else "👤"}</div>
      <div>
        <div class="profile-name">{name}{badge}</div>
        <div class="profile-id">@{uid}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # 매너 온도 (일반 유저)
    if not is_admin:
        temp  = get_temperature(uid)
        cnt   = get_score_count(uid)
        color = temp_color(temp)
        lt    = temp_label(temp)
        st.markdown(f"""
        <div style="margin-bottom:1.2rem;">
          <div style="font-size:.8rem;color:#6B7280;margin-bottom:.3rem;">
            🌡️ 매너 온도 &nbsp;
            <span style="font-weight:700;color:{color};font-size:1rem;">{temp}°</span>
            &nbsp;{lt}&nbsp;
            <span style="font-size:.72rem;color:#9CA3AF;">(평가 {cnt}회)</span>
          </div>
          <div class="temp-bar-wrap">
            <div class="temp-bar" style="width:{temp}%;background:{color};"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    if st.button("로그아웃", key="logout_btn"):
        st.session_state.pop("user", None)
        st.session_state.page="my"; st.session_state.auth_step="choice"; st.rerun()

    # ── 관리자 전체 파티 현황 ─────────────────────────────────────────────
    if is_admin:
        st.markdown('<div class="mypage-section-title">🧴 생필품 파티 전체 현황</div>',
                    unsafe_allow_html=True)
        for p in ess_all():
            s = "🟢 모집중" if p["status"]=="open" else "🔴 마감"
            st.markdown(f"""
            <div class="admin-pot-card">
              <b>{p['item_label']}</b> {s} | 신청자 {len(p['applicants'])}명<br>
              <span style="font-size:.78rem;color:#6B7280;">
                개당 {p['price_per_unit']:,}원 | {p['created_at'][:10]}
              </span>
            </div>""", unsafe_allow_html=True)
            if st.button("🗑️ 삭제", key=f"admin_ess_del_{p['party_id']}"):
                from essentials_store import delete_party
                delete_party(p["party_id"]); st.rerun()

        st.markdown('<div class="mypage-section-title">🏪 편의점 파티 전체 현황</div>',
                    unsafe_allow_html=True)
        status_map = {"waiting":"🟡 대기","departed":"🚀 출발","arrived":"📍 집합"}
        for p in cvs_all():
            s = status_map.get(p["status"], p["status"])
            st.markdown(f"""
            <div class="admin-pot-card">
              <b>{p['creator_name']}</b> {s} | 주문 {len(p['orders'])}건 |
              출발 {p['depart_time']}<br>
              <span style="font-size:.78rem;color:#6B7280;">{p['created_at'][:10]}</span>
            </div>""", unsafe_allow_html=True)
            if st.button("🗑️ 삭제", key=f"admin_cvs_del_{p['party_id']}"):
                from cvs_store import delete_party
                delete_party(p["party_id"]); st.rerun()
        return

    # ── 일반 유저: 내 생필품 신청 내역 ───────────────────────────────────
    st.markdown('<div class="mypage-section-title">🧴 내 생필품 신청</div>',
                unsafe_allow_html=True)
    my_ess = [p for p in ess_all()
              if any(a["user_id"]==uid for a in p["applicants"])]
    if not my_ess:
        st.info("신청한 생필품 파티가 없습니다.")
    else:
        for p in my_ess:
            my_app = next(a for a in p["applicants"] if a["user_id"]==uid)
            s = "🟢 모집중" if p["status"]=="open" else "✅ 마감"
            st.markdown(f"""
            <div class="admin-pot-card">
              <b>{p['item_label']}</b> {s} | 내 신청: {my_app['qty']}개
              {f"| 납부: {my_app['qty']*p['price_per_unit']:,}원" if p['status']=='closed' else ''}
              {f"| 송금처: {p['payment_dest']}" if p['status']=='closed' else ''}
            </div>""", unsafe_allow_html=True)

    # ── 내 편의점 파티 내역 ───────────────────────────────────────────────
    st.markdown('<div class="mypage-section-title">🏪 내 편의점 파티</div>',
                unsafe_allow_html=True)
    my_cvs = cvs_by_user(uid)
    if not my_cvs:
        st.info("참여 중인 편의점 파티가 없습니다.")
    else:
        for p in my_cvs:
            is_creator = p["creator_id"] == uid
            status_map2 = {"waiting":"🟡 대기중","departed":"🚀 출발","arrived":"📍 집합완료"}
            s = status_map2.get(p["status"], p["status"])
            my_orders = [o for o in p["orders"] if o["user_id"]==uid]
            order_txt = ", ".join(f"{o['item_label']}×{o['qty']}" for o in my_orders)
            st.markdown(f"""
            <div class="admin-pot-card">
              {'[파티장] ' if is_creator else ''}<b>{p['creator_name']}</b>의 파티 {s} |
              출발 {p['depart_time']}<br>
              {f"내 주문: {order_txt}" if order_txt else ""}
            </div>""", unsafe_allow_html=True)
