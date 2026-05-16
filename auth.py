"""auth.py — 로그인 / 회원가입 / 마이페이지"""

import streamlit as st
from user_store import (register_user, login_user, get_all_users,
                         delete_user, get_credits, add_credits,
                         set_credits, SCHOOLS)
from rating_store import get_temperature, get_score_count, temp_color, temp_label, set_temperature
from notification_store import push_all
from essentials_store import get_all_parties as ess_all

AUTH_CSS = """
<style>
.auth-card{background:#FFFFFF;border-radius:20px;padding:2.6rem 2.4rem 2.2rem;
  max-width:440px;margin:3rem auto 0;
  box-shadow:0 4px 32px rgba(37,99,235,.10);border:1.5px solid #BFDBFE;}
.auth-title{font-family:'DM Serif Display',serif;font-size:1.7rem;
  color:#0F172A;margin-bottom:.3rem;}
.auth-sub{font-size:.85rem;color:#94A3B8;margin-bottom:1.8rem;}
.profile-card{background:#FFFFFF;border-radius:20px;padding:2rem 2.4rem;
  margin-bottom:1.2rem;box-shadow:0 4px 24px rgba(37,99,235,.08);
  border:1.5px solid #BFDBFE;display:flex;align-items:center;gap:1.6rem;}
.profile-avatar{width:72px;height:72px;border-radius:50%;
  background:linear-gradient(135deg,#DBEAFE,#EFF6FF);
  display:flex;align-items:center;justify-content:center;
  font-size:2rem;flex-shrink:0;border:2px solid #2563EB;}
.admin-badge{display:inline-block;background:#DBEAFE;color:#1D4ED8;
  font-size:.7rem;font-weight:700;padding:.1rem .5rem;
  border-radius:20px;margin-left:.4rem;}
.profile-name{font-family:'DM Serif Display',serif;font-size:1.4rem;
  color:#0F172A;margin-bottom:.2rem;}
.profile-id{font-size:.82rem;color:#94A3B8;font-weight:500;}
.mypage-section-title{font-size:.9rem;font-weight:700;color:#1D4ED8;
  letter-spacing:.06em;text-transform:uppercase;
  margin:1.6rem 0 .8rem;padding-bottom:.4rem;
  border-bottom:2px solid #DBEAFE;}
.temp-bar-wrap{background:#DBEAFE;border-radius:20px;height:12px;
  margin:.4rem 0 .2rem;overflow:hidden;}
.temp-bar{height:100%;border-radius:20px;transition:width .4s;}
.admin-pot-card{border:1.5px solid #BFDBFE;border-radius:12px;
  padding:.8rem 1rem;margin-bottom:.6rem;background:#F8FBFF;}
.admin-pot-card:hover{border-color:#2563EB;background:#EFF6FF;}
.user-card{border:1.5px solid #BFDBFE;border-radius:12px;
  padding:.8rem 1rem;margin-bottom:.6rem;background:#F8FBFF;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;}
.credit-badge{display:inline-block;background:#FEF9C3;color:#B45309;
  font-size:.72rem;font-weight:700;padding:.15rem .55rem;border-radius:20px;}
</style>
"""


def render_auth_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    if "auth_step" not in st.session_state:
        st.session_state.auth_step = "choice"
    step = st.session_state.auth_step

    if step == "choice":
        st.markdown("""
        <div style="text-align:center;margin-top:2.5rem;">
          <p style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:#0F172A;margin-bottom:.3rem">마이페이지</p>
          <p style="font-size:.85rem;color:#94A3B8;">로그인하거나 새 계정을 만들어 보세요</p>
        </div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔑\n\n로그인", use_container_width=True, key="go_login"):
                st.session_state.auth_step = "login"; st.rerun()
        with c2:
            if st.button("✏️\n\n회원가입", use_container_width=True, key="go_register"):
                st.session_state.auth_step = "register"; st.rerun()
        st.markdown("""<style>
        div[data-testid="stHorizontalBlock"]:not(:last-child) button{
          height:120px !important;font-size:1rem !important;border-radius:16px !important;
          border:2px solid #BFDBFE !important;background:#FFFFFF !important;
          color:#0F172A !important;font-weight:600 !important;white-space:pre-line !important;}
        div[data-testid="stHorizontalBlock"]:not(:last-child) button:hover{
          border-color:#2563EB !important;background:#EFF6FF !important;}
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
                st.session_state.user      = result
                st.session_state.auth_step = "choice"
                st.session_state.page      = "my"
                st.rerun()
            else:
                st.error(result)
        if st.button("← 뒤로", key="back_login"):
            st.session_state.auth_step = "choice"; st.rerun()

    elif step == "register":
        st.markdown("""<div class="auth-card">
          <div class="auth-title">회원가입</div>
          <div class="auth-sub">기본 정보를 입력하고 계정을 만드세요</div></div>""",
                    unsafe_allow_html=True)
        with st.form("register_form"):
            name   = st.text_input("이름")
            uid    = st.text_input("아이디", placeholder="4자 이상")
            pw     = st.text_input("비밀번호", type="password", placeholder="6자 이상")
            school = st.selectbox("학교", ["학교 선택"] + SCHOOLS)
            ok_btn = st.form_submit_button("계정 만들기", use_container_width=True)
        if ok_btn:
            sel_school = "" if school == "학교 선택" else school
            ok, msg = register_user(name, uid, pw, sel_school)
            if ok:
                st.success("회원가입 완료!")
                st.session_state.auth_step = "login"; st.rerun()
            else:
                st.error(msg)
        if st.button("← 뒤로", key="back_register"):
            st.session_state.auth_step = "choice"; st.rerun()


def render_my_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    user     = st.session_state.get("user", {})
    name     = user.get("name", "사용자")
    uid      = user.get("user_id", "")
    is_admin = user.get("is_admin", False)
    school   = user.get("school", "")
    credits  = get_credits(uid)

    badge = '<span class="admin-badge">ADMIN</span>' if is_admin else ""
    st.markdown(f"""
    <div class="profile-card">
      <div class="profile-avatar">{"🛡️" if is_admin else "👤"}</div>
      <div>
        <div class="profile-name">{name}{badge}</div>
        <div class="profile-id">@{uid}{f" · {school}" if school else ""}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # 매너온도 + 크래딧 (일반 유저)
    if not is_admin:
        temp  = get_temperature(uid)
        cnt   = get_score_count(uid)
        color = temp_color(temp)
        lt    = temp_label(temp)
        st.markdown(f"""
        <div style="margin-bottom:.8rem;">
          <div style="font-size:.8rem;color:#64748B;margin-bottom:.3rem;">
            🌡️ 매너 온도 &nbsp;
            <span style="font-weight:700;color:{color};font-size:1rem;">{temp}°</span>
            &nbsp;{lt}&nbsp;
            <span style="font-size:.72rem;color:#94A3B8;">(평가 {cnt}회)</span>
          </div>
          <div class="temp-bar-wrap">
            <div class="temp-bar" style="width:{temp}%;background:{color};"></div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f'<div style="margin-bottom:1.2rem;">'
                    f'🪙 <b>보유 크래딧: {credits}</b></div>',
                    unsafe_allow_html=True)

    if st.button("로그아웃", key="logout_btn"):
        st.session_state.pop("user", None)
        st.session_state.page = "my"
        st.session_state.auth_step = "choice"
        st.rerun()

    # ── 관리자 전용 ───────────────────────────────────────────────────────
    if is_admin:
        admin_tab1, admin_tab2 = st.tabs(["🧴 공동구매 현황", "👥 회원 관리"])

        with admin_tab1:
            st.markdown('<div class="mypage-section-title">🧴 공동구매 파티 전체 현황</div>',
                        unsafe_allow_html=True)
            status_map = {"open": "🟢 모집중", "closed": "🟡 마감됨", "rated": "🟣 평가완료"}
            for p in sorted(ess_all(), key=lambda x: x["created_at"], reverse=True):
                s = status_map.get(p["status"], p["status"])
                st.markdown(f"""
                <div class="admin-pot-card">
                  <b>{p['item_label']}</b> {s} | 신청자 {len(p['applicants'])}명<br>
                  <span style="font-size:.78rem;color:#64748B;">
                    개당 {p['price_per_unit']:,}원 | {p['created_at'][:10]}
                  </span>
                </div>""", unsafe_allow_html=True)
                if p["status"] in ("open",):
                    if st.button("🗑️ 삭제", key=f"admin_ess_del_{p['party_id']}"):
                        from essentials_store import delete_party
                        delete_party(p["party_id"]); st.rerun()

        with admin_tab2:
            st.markdown('<div class="mypage-section-title">👥 회원 관리</div>',
                        unsafe_allow_html=True)
            all_users = [u for u in get_all_users() if not u.get("is_admin")]

            if not all_users:
                st.info("가입된 회원이 없습니다.")
            else:
                for u in all_users:
                    u_id     = u["user_id"]
                    u_name   = u["name"]
                    u_school = u.get("school", "")
                    u_cred   = u.get("credits", 0)
                    u_temp   = get_temperature(u_id)
                    u_cnt    = get_score_count(u_id)

                    with st.expander(
                        f"👤 {u_name} (@{u_id}) | {u_school} | "
                        f"🌡️{u_temp}° | 🪙{u_cred}",
                        expanded=False):

                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**매너 온도:** {u_temp}° ({u_cnt}회 평가)")
                        with c2:
                            st.markdown(f"**보유 크래딧:** {u_cred}")

                        # 매너 온도 조정
                        st.markdown("**매너 온도 조정**")
                        temp_cols = st.columns([3, 1, 1])
                        with temp_cols[0]:
                            new_temp = st.number_input(
                                "새 매너 온도 (0~100)", min_value=0.0, max_value=100.0,
                                value=float(u_temp), step=0.5,
                                key=f"temp_{u_id}")
                        with temp_cols[1]:
                            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                            if st.button("저장", key=f"temp_save_{u_id}"):
                                set_temperature(u_id, new_temp)
                                st.success("매너 온도 저장됨"); st.rerun()
                        with temp_cols[2]:
                            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                            if st.button("초기화", key=f"temp_reset_{u_id}",
                                         help="50°로 초기화"):
                                set_temperature(u_id, 50.0)
                                st.rerun()

                        # 크래딧 직접 조정
                        st.markdown("**크래딧 조정**")
                        adj_cols = st.columns([3, 1, 1])
                        with adj_cols[0]:
                            new_cr = st.number_input("새 크래딧 값", min_value=0,
                                                      value=u_cred, step=10,
                                                      key=f"cr_{u_id}")
                        with adj_cols[1]:
                            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                            if st.button("저장", key=f"cr_save_{u_id}"):
                                set_credits(u_id, new_cr)
                                st.success("크래딧 저장됨"); st.rerun()
                        with adj_cols[2]:
                            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                            if st.button("➕10", key=f"cr_add_{u_id}"):
                                add_credits(u_id, 10)
                                st.rerun()

                        # 탈퇴 처리
                        st.markdown("---")
                        if st.button(f"🗑️ {u_name} 탈퇴 처리",
                                     key=f"del_user_{u_id}",
                                     type="secondary"):
                            delete_user(u_id)
                            push_all([u_id], "pot_disbanded",
                                     "관리자에 의해 계정이 탈퇴 처리됐습니다.")
                            st.success(f"@{u_id} 탈퇴 처리 완료"); st.rerun()

        return  # 관리자 마이페이지 끝

    # ── 일반 유저: 내 생필품 신청 내역 ───────────────────────────────────
    st.markdown('<div class="mypage-section-title">🧴 내 공동구매 신청</div>',
                unsafe_allow_html=True)
    my_ess = [p for p in ess_all()
              if any(a["user_id"] == uid for a in p["applicants"])]
    if not my_ess:
        st.info("신청한 공동구매 파티가 없습니다.")
    else:
        status_map = {"open": "🟢 모집중", "closed": "🟡 마감됨", "rated": "🟣 완료"}
        for p in my_ess:
            my_app = next(a for a in p["applicants"] if a["user_id"] == uid)
            s = status_map.get(p["status"], p["status"])
            pay_txt = ""
            if p["status"] in ("closed", "rated") and p.get("price_per_unit", 0) > 0:
                amount = my_app["qty"] * p["price_per_unit"]
                pay_txt = f"| 납부: {amount:,}원 → {p.get('payment_dest', '')}"
            st.markdown(f"""
            <div class="admin-pot-card">
              <b>{p['item_label']}</b> {s} | 내 신청: {my_app['qty']}개 {pay_txt}
              {f"| 📅 마감: {p['deadline']}" if p.get('deadline') else ""}
            </div>""", unsafe_allow_html=True)
