"""
auth.py  —  로그인 / 회원가입 / 마이페이지
"""

import streamlit as st
import streamlit.components.v1 as components
from user_store         import register_user, login_user, get_lists
from pot_store          import get_pots_by_user, get_all_pots, admin_delete_pot, calc_dday, price_per_person
from rating_store       import get_temperature, get_score_count, temp_color, temp_label
from notification_store import push_all

AUTH_CSS = """
<style>
.auth-card{background:#fff;border-radius:20px;padding:2.6rem 2.4rem 2.2rem;
  max-width:440px;margin:3rem auto 0;
  box-shadow:0 4px 32px rgba(0,0,0,.08);border:1px solid #E5E7EB;}
.auth-title{font-family:'DM Serif Display',serif;font-size:1.7rem;color:#1a1a1a;margin-bottom:.3rem;}
.auth-sub{font-size:.85rem;color:#9CA3AF;margin-bottom:1.8rem;}
.profile-card{background:#fff;border-radius:20px;padding:2rem 2.4rem;margin-bottom:1.2rem;
  box-shadow:0 4px 24px rgba(0,0,0,.06);border:1px solid #E5E7EB;
  display:flex;align-items:center;gap:1.6rem;}
.profile-avatar{width:72px;height:72px;border-radius:50%;
  background:linear-gradient(135deg,#DBEAFE,#EEF4FF);
  display:flex;align-items:center;justify-content:center;
  font-size:2rem;flex-shrink:0;border:2px solid #3B82F6;}
.admin-badge{display:inline-block;background:#FEF3C7;color:#D97706;
  font-size:.7rem;font-weight:700;padding:.1rem .5rem;border-radius:20px;
  letter-spacing:.05em;margin-left:.4rem;}
.profile-name{font-family:'DM Serif Display',serif;font-size:1.4rem;color:#1a1a1a;margin-bottom:.2rem;}
.profile-id{font-size:.82rem;color:#9CA3AF;font-weight:500;}
.mypage-section-title{font-size:.9rem;font-weight:600;color:#1a1a1a;
  letter-spacing:.06em;text-transform:uppercase;margin:1.6rem 0 .8rem;}
/* 매너 온도 */
.temp-bar-wrap{background:#F3F4F6;border-radius:20px;height:12px;margin:.4rem 0 .2rem;overflow:hidden;}
.temp-bar{height:100%;border-radius:20px;transition:width .4s;}
/* 내 팟 카드 */
.my-pot-card{border:1.5px solid #DBEAFE;border-radius:14px;
  padding:.9rem 1.1rem;margin-bottom:.7rem;background:#F0F7FF;
  position:relative;cursor:pointer;}
.my-pot-card:hover{border-color:#3B82F6;}
.my-pot-card.ended{background:#F0FFF4;border-color:#86EFAC;}
.my-pot-card.disbanded{background:#FFF7ED;border-color:#FCA5A5;opacity:.7;}
.my-pot-dday{position:absolute;top:.65rem;right:.9rem;
  font-size:.68rem;font-weight:800;color:#EF4444;
  background:#FEE2E2;padding:.12rem .5rem;border-radius:20px;}
.my-pot-item{font-weight:700;color:#1a1a1a;font-size:.92rem;margin-bottom:.2rem;}
.my-pot-meta{font-size:.77rem;color:#6B7280;}
.my-pot-price{font-weight:700;color:#3B82F6;font-size:.88rem;margin-top:.2rem;}
/* 관리자 팟 카드 */
.admin-pot-card{border:1.5px solid #E5E7EB;border-radius:12px;
  padding:.8rem 1rem;margin-bottom:.6rem;background:#FAFAFA;}
</style>
"""


def _general_card_html(items):
    cards = ""
    for item in items:
        label = item.get("label","")
        img   = item.get("image_url","")
        bg    = f"url('{img}') center/cover no-repeat" if img else "linear-gradient(135deg,#EEF4FF,#DBEAFE)"
        cards += f"""<div class="card"><div class="card-img" style="background:{bg};"></div>
          <span class="card-label">{label}</span></div>"""
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:transparent;font-family:'DM Sans',sans-serif;padding:0 0 4px 0;}}
.card-row{{display:flex;gap:1rem;overflow-x:auto;background:#EDEBE5;
  border-radius:14px;padding:1rem;border:1.5px solid #D8D4CB;}}
.card-row::-webkit-scrollbar{{height:4px;}}
.card-row::-webkit-scrollbar-thumb{{background:#C2BEAF;border-radius:4px;}}
.card{{flex:0 0 150px;height:170px;border-radius:12px;border:2px solid #3B82F6;
  background:#fff;display:flex;flex-direction:column;align-items:center;
  justify-content:flex-end;padding-bottom:.7rem;
  position:relative;overflow:hidden;}}
.card-img{{position:absolute;inset:0;}}
.card-label{{position:relative;font-size:.72rem;font-weight:600;color:#3B82F6;
  letter-spacing:.04em;background:rgba(255,255,255,.88);
  padding:.2rem .55rem;border-radius:20px;}}</style>
</head><body><div class="card-row">{cards}</div></body></html>"""


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
        col1,col2 = st.columns(2)
        with col1:
            if st.button("🔑\n\n로그인",  use_container_width=True, key="go_login"):
                st.session_state.auth_step="login"; st.rerun()
        with col2:
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
          <div class="auth-sub">아이디와 비밀번호를 입력하세요</div></div>""", unsafe_allow_html=True)
        with st.form("login_form"):
            uid    = st.text_input("아이디", placeholder="아이디를 입력하세요")
            pw     = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            ok_btn = st.form_submit_button("로그인", use_container_width=True)
        if ok_btn:
            ok, result = login_user(uid, pw)
            if ok:
                st.session_state.user=result
                st.session_state.auth_step="choice"
                st.session_state.page="my"
                st.rerun()
            else: st.error(result)
        if st.button("← 뒤로", key="back_login"):
            st.session_state.auth_step="choice"; st.rerun()

    elif step == "register":
        st.markdown("""<div class="auth-card">
          <div class="auth-title">회원가입</div>
          <div class="auth-sub">기본 정보를 입력하고 계정을 만드세요</div></div>""", unsafe_allow_html=True)
        with st.form("register_form"):
            name   = st.text_input("이름", placeholder="홍길동")
            uid    = st.text_input("아이디", placeholder="4자 이상")
            pw     = st.text_input("비밀번호", type="password", placeholder="6자 이상")
            ok_btn = st.form_submit_button("계정 만들기", use_container_width=True)
        if ok_btn:
            ok, msg = register_user(name, uid, pw)
            if ok:
                st.success("회원가입 완료! 로그인해 주세요.")
                st.session_state.auth_step="login"; st.rerun()
            else: st.error(msg)
        if st.button("← 뒤로", key="back_register"):
            st.session_state.auth_step="choice"; st.rerun()


# ── 마이페이지 ────────────────────────────────────────────────────────────────

def render_my_page():
    from pot_page import render_pot_detail   # 순환 import 방지용 지연 import

    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    user     = st.session_state.get("user", {})
    name     = user.get("name","사용자")
    uid      = user.get("user_id","")
    is_admin = user.get("is_admin", False)

    # ── 팟 상세 보기 모드 ─────────────────────────────────────────────────
    if st.session_state.get("viewing_pot_id"):
        render_pot_detail(st.session_state["viewing_pot_id"])
        return

    # ── 프로필 카드 ───────────────────────────────────────────────────────
    badge = '<span class="admin-badge">ADMIN</span>' if is_admin else ""
    st.markdown(f"""
    <div class="profile-card">
      <div class="profile-avatar">{"🛡️" if is_admin else "👤"}</div>
      <div>
        <div class="profile-name">{name}{badge}</div>
        <div class="profile-id">@{uid}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # 매너 온도 (일반 유저만)
    if not is_admin:
        temp  = get_temperature(uid)
        cnt   = get_score_count(uid)
        color = temp_color(temp)
        label_t = temp_label(temp)
        st.markdown(f"""
        <div style="margin-bottom:1.2rem;">
          <div style="font-size:.8rem;color:#6B7280;margin-bottom:.3rem;">
            🌡️ 매너 온도 &nbsp;
            <span style="font-weight:700;color:{color};font-size:1rem;">{temp}°</span>
            &nbsp; {label_t} &nbsp;
            <span style="font-size:.72rem;color:#9CA3AF;">(평가 {cnt}회)</span>
          </div>
          <div class="temp-bar-wrap">
            <div class="temp-bar" style="width:{temp}%;background:{color};"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    if st.button("로그아웃", key="logout_btn"):
        st.session_state.pop("user", None)
        st.session_state.page="my"
        st.session_state.auth_step="choice"
        st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # 관리자: 전체 팟 내역
    # ══════════════════════════════════════════════════════════════════════
    if is_admin:
        st.markdown('<div class="mypage-section-title">🛡️ 전체 팟 내역</div>', unsafe_allow_html=True)
        all_pots = get_all_pots()
        if not all_pots:
            st.info("생성된 팟이 없습니다.")
        else:
            status_map = {"active":"🟢 진행 중","ended":"✅ 종료됨","disbanded":"🔴 해산됨"}
            for pot in sorted(all_pots, key=lambda x: x["created_at"], reverse=True):
                dday = calc_dday(pot["buy_date"])
                ppp  = price_per_person(pot)
                s    = pot.get("status","active")
                with st.container():
                    st.markdown(f"""
                    <div class="admin-pot-card">
                      <b>{pot['item_label']}</b> &nbsp;
                      <span style="font-size:.75rem;color:#6B7280;">{status_map.get(s,s)}</span><br>
                      <span style="font-size:.8rem;color:#6B7280;">
                        팟장: {pot['creator_name']} | 👥 {len(pot['members'])}/{pot['total_people']}명 |
                        인당 {ppp:,}원 | 📅 {pot['buy_date']} ({dday}) | 📍 {pot['location_name']}
                      </span>
                    </div>""", unsafe_allow_html=True)

                    if st.button("🗑️ 삭제", key=f"admin_del_{pot['pot_id']}"):
                        push_all(pot["members"], "pot_disbanded",
                                 f"관리자가 '{pot['item_label']}' 팟을 삭제했습니다.")
                        admin_delete_pot(pot["pot_id"])
                        st.success("팟이 삭제됐습니다."); st.rerun()
        return   # 관리자는 내 팟 / 리스트2 섹션 없음

    # ══════════════════════════════════════════════════════════════════════
    # 일반 유저: 내 구메팟
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="mypage-section-title">🛒 내 구메팟</div>', unsafe_allow_html=True)
    my_pots = get_pots_by_user(uid)

    if not my_pots:
        st.info("참여 중인 구메팟이 없습니다.")
    else:
        for pot in my_pots:
            dday   = calc_dday(pot["buy_date"])
            ppp    = price_per_person(pot)
            mem    = len(pot["members"])
            total  = pot["total_people"]
            status = pot.get("status","active")
            cls    = "ended" if status=="ended" else "disbanded" if status=="disbanded" else ""

            st.markdown(f"""
            <div class="my-pot-card {cls}">
              <div class="my-pot-dday">{dday}</div>
              <div class="my-pot-item">🛍️ {pot['item_label']}</div>
              <div class="my-pot-meta">👥 {mem}/{total}명 · 📅 {pot['buy_date']} · 📍 {pot['location_name']}</div>
              <div class="my-pot-price">인당 {ppp:,}원
                {'&nbsp; ✅ 종료' if status=='ended' else '&nbsp; 🔴 해산' if status=='disbanded' else ''}
              </div>
            </div>""", unsafe_allow_html=True)

            if st.button(f"상세 보기", key=f"view_pot_{pot['pot_id']}"):
                st.session_state.viewing_pot_id = pot["pot_id"]
                st.rerun()

    # ── 리스트 2 ─────────────────────────────────────────────────────────
    lists  = get_lists()
    list2  = lists.get("list2", {})
    title2 = list2.get("title","List 2")
    items2 = list2.get("items", [])
    st.markdown(f'<div class="mypage-section-title">{title2}</div>', unsafe_allow_html=True)
    components.html(_general_card_html(items2), height=230, scrolling=False)
