"""project.py — 메인 앱 진입점"""

import streamlit as st
import streamlit.components.v1 as components

from auth           import render_auth_page, render_my_page
from wishlist_page  import render_wishlist_page
from essentials_page import render_essentials_popup
from cvs_page       import render_cvs_popup
from user_store     import (initialize, get_lists, get_all_user_ids, get_list_type,
                             update_list_title, add_list_item, update_list_item, delete_list_item,
                             add_list, delete_list)
from notification_store import (get_notifications, get_unread_count,
                                 mark_all_read, clear_notifications)

# ── 초기화 ────────────────────────────────────────────────────────────────────
initialize()

st.set_page_config(page_title="구메", layout="wide", initial_sidebar_state="collapsed")

for k, v in [("page","main"),("modal_item",None),("modal_type",None),
              ("show_notif",False),("ess_sub","main"),("ess_party_id",None),
              ("cvs_sub","list"),("cvs_party_id",None)]:
    if k not in st.session_state: st.session_state[k] = v

# ── 전역 CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
html,body,[data-testid="stAppViewContainer"]{background:#F7F5F0;font-family:'DM Sans',sans-serif;}
[data-testid="stHeader"]{display:none;}[data-testid="stSidebar"]{display:none;}
.main .block-container{max-width:1100px;padding:0 2rem 6rem 2rem;margin:0 auto;}
.top-header{display:flex;align-items:center;justify-content:space-between;
  padding:1.6rem 0 1.2rem 0;border-bottom:2px solid #1a1a1a;margin-bottom:2.4rem;}
.logo-text{font-family:'DM Serif Display',serif;font-size:2rem;color:#1a1a1a;}
.list-type-badge{display:inline-block;font-size:.7rem;font-weight:700;
  padding:.15rem .55rem;border-radius:20px;margin-left:.5rem;vertical-align:middle;}
.badge-essentials{background:#DCFCE7;color:#16A34A;}
.badge-cvs{background:#FEF3C7;color:#D97706;}
.notif-panel{background:#fff;border:1.5px solid #E5E7EB;border-radius:16px;
  padding:1rem 1.2rem;margin-bottom:1.2rem;box-shadow:0 8px 32px rgba(0,0,0,.12);}
.notif-item{padding:.6rem 0;border-bottom:1px solid #F3F4F6;font-size:.83rem;color:#374151;}
.notif-item:last-child{border-bottom:none;}
.notif-time{font-size:.7rem;color:#9CA3AF;margin-top:.15rem;}
/* 카드 이미지 래퍼 */
.card-img-wrap{width:100%;aspect-ratio:4/3;border-radius:12px 12px 0 0;overflow:hidden;
  position:relative;border:2px solid #3B82F6;border-bottom:none;
  background:linear-gradient(135deg,#EEF4FF,#DBEAFE);}
.card-img-wrap img{width:100%;height:100%;object-fit:cover;display:block;}
.card-img-placeholder{width:100%;height:100%;
  display:flex;align-items:center;justify-content:center;font-size:2.5rem;}
.card-price-tag{position:absolute;top:8px;right:8px;font-size:.68rem;font-weight:700;
  color:#fff;background:rgba(59,130,246,.88);padding:.15rem .55rem;border-radius:20px;}
/* 버튼 카드 하단 스타일 */
div[data-card-btn] > div > button{
  border-radius:0 0 12px 12px !important;border:2px solid #3B82F6 !important;
  border-top:none !important;background:#fff !important;color:#3B82F6 !important;
  font-weight:600 !important;font-size:.82rem !important;
  padding:.55rem .5rem !important;transition:background .15s !important;}
div[data-card-btn] > div > button:hover{background:#EFF6FF !important;}
/* 하단 네비바 */
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"]{
  position:fixed !important;bottom:0 !important;left:0 !important;right:0 !important;
  width:100% !important;max-width:100% !important;
  padding:0 !important;margin:0 !important;gap:0 !important;
  background:#ffffff !important;border-top:1px solid #E5E7EB !important;
  box-shadow:0 -4px 20px rgba(0,0,0,.06) !important;
  z-index:9999 !important;display:flex !important;align-items:stretch !important;height:64px !important;}
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"]{flex:1 !important;padding:0 !important;min-width:0 !important;}
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"] button{
  width:100% !important;height:64px !important;background:transparent !important;
  border:none !important;border-radius:0 !important;box-shadow:none !important;
  font-size:1.5rem !important;cursor:pointer !important;transition:background .2s !important;
  color:#6B7280 !important;padding:0 !important;
  display:flex !important;align-items:center !important;justify-content:center !important;}
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"]
  button:hover{background:#EFF6FF !important;color:#3B82F6 !important;}
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"]
  button p{display:none !important;}
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"]
  .stElementContainer{padding:0 !important;}
</style>
""", unsafe_allow_html=True)

# ── 유저 정보 ─────────────────────────────────────────────────────────────────
is_logged = "user" in st.session_state
is_admin  = st.session_state.get("user", {}).get("is_admin", False)
uid       = st.session_state.get("user", {}).get("user_id", "")

# ── 상단 헤더 + 알림 ──────────────────────────────────────────────────────────
notif_cnt  = get_unread_count(uid) if is_logged else 0
notif_icon = f"🔔({notif_cnt})" if notif_cnt > 0 else "🔔"

h1, h2 = st.columns([9,1])
with h1:
    st.markdown('<div class="top-header"><span class="logo-text">구메</span></div>',
                unsafe_allow_html=True)
with h2:
    st.markdown("<div style='height:1.3rem'></div>", unsafe_allow_html=True)
    if is_logged:
        if st.button(notif_icon, key="notif_btn", help="알림"):
            st.session_state.show_notif = not st.session_state.show_notif
            if st.session_state.show_notif: mark_all_read(uid)
            st.rerun()

# ── 알림 패널 ─────────────────────────────────────────────────────────────────
if st.session_state.show_notif and is_logged:
    notifs = get_notifications(uid)
    type_icon = {"item_added":"🆕","item_deleted":"🗑️","item_price_changed":"💰",
                 "pot_joined":"🛒","pot_ended":"✅","pot_disbanded":"💔"}
    st.markdown('<div class="notif-panel">', unsafe_allow_html=True)
    st.markdown("**🔔 알림**")
    if not notifs:
        st.caption("새 알림이 없습니다.")
    else:
        for n in notifs[:20]:
            icon = type_icon.get(n["type"],"📢")
            st.markdown(f'<div class="notif-item">{icon} {n["message"]}'
                        f'<div class="notif-time">{n["created_at"]}</div></div>',
                        unsafe_allow_html=True)
    pc1,pc2 = st.columns(2)
    with pc1:
        if st.button("✕ 닫기", key="close_notif", use_container_width=True):
            st.session_state.show_notif=False; st.rerun()
    with pc2:
        if st.button("전체 삭제", key="clear_notif", use_container_width=True):
            clear_notifications(uid); st.session_state.show_notif=False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── 카드 섹션 ─────────────────────────────────────────────────────────────────
def render_card_section(title: str, items: list, list_key: str, list_type: str):
    badge_cls  = "badge-essentials" if list_type=="essentials" else "badge-cvs"
    badge_txt  = "생필품" if list_type=="essentials" else "편의점"
    btn_label  = "🧴 구메 신청" if list_type=="essentials" else "🏪 파티 찾기"

    st.markdown(
        f'<p style="font-size:1rem;font-weight:600;color:#1a1a1a;'
        f'letter-spacing:.06em;text-transform:uppercase;margin-bottom:.6rem;">'
        f'{title} <span class="list-type-badge {badge_cls}">{badge_txt}</span></p>',
        unsafe_allow_html=True)

    n = len(items)
    if n == 0:
        st.caption("항목이 없습니다.")
        return

    cols = st.columns(n)
    for i, (col, item) in enumerate(zip(cols, items)):
        label = item.get("label","")
        img   = item.get("image_url","")
        price = item.get("price",0)
        ptag  = f'<div class="card-price-tag">{price:,}원</div>' if price else ""

        with col:
            if img:
                st.markdown(f'<div class="card-img-wrap"><img src="{img}" alt="{label}">{ptag}</div>',
                            unsafe_allow_html=True)
            else:
                icon = "🧴" if list_type=="essentials" else "🏪"
                st.markdown(f'<div class="card-img-wrap">'
                            f'<div class="card-img-placeholder">{icon}</div>{ptag}</div>',
                            unsafe_allow_html=True)

            st.markdown('<div data-card-btn="1">', unsafe_allow_html=True)
            if st.button(f"{btn_label} {label}", key=f"card_{list_key}_{i}",
                         use_container_width=True):
                st.session_state.modal_item = item
                st.session_state.modal_type = list_type
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)


# ── 관리자 편집 패널 ──────────────────────────────────────────────────────────
def render_admin_editor(list_key: str, info: dict):
    with st.expander(f"⚙️ [{info.get('title',list_key)}] 편집", expanded=False):
        st.markdown('<p style="font-size:.72rem;font-weight:700;color:#D97706;'
                    'letter-spacing:.08em;text-transform:uppercase;">🛡️ 관리자 편집</p>',
                    unsafe_allow_html=True)

        new_title = st.text_input("리스트 제목", value=info["title"], key=f"title_{list_key}")
        if st.button("제목 저장", key=f"save_title_{list_key}"):
            update_list_title(list_key, new_title); st.success("저장"); st.rerun()

        st.divider()
        all_uids = get_all_user_ids()

        for i, item in enumerate(info["items"]):
            c1,c2,c3,c4 = st.columns([3,4,2,1])
            with c1: new_label = st.text_input(f"이름#{i+1}", value=item["label"], key=f"lbl_{list_key}_{i}")
            with c2: new_img   = st.text_input(f"URL#{i+1}",  value=item.get("image_url",""), key=f"img_{list_key}_{i}", placeholder="https://...")
            with c3:
                old_p = int(item.get("price",0))
                new_p = st.number_input(f"가격#{i+1}", value=old_p, min_value=0, step=100, key=f"price_{list_key}_{i}")
            with c4:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{list_key}_{i}"):
                    removed = delete_list_item(list_key, i)
                    if removed:
                        from notification_store import push_all
                        push_all(all_uids,"item_deleted",f"'{removed['label']}' 항목이 삭제됐습니다.")
                    st.rerun()
            if st.button(f"저장#{i+1}", key=f"save_{list_key}_{i}"):
                from notification_store import push_all
                update_list_item(list_key, i, new_label, new_img, new_p)
                if new_p != old_p:
                    push_all(all_uids,"item_price_changed",
                             f"'{new_label}' 가격이 {new_p:,}원으로 변경됐습니다.")
                st.success("저장"); st.rerun()

        st.divider()
        a1,a2,a3 = st.columns([3,4,2])
        with a1: add_label = st.text_input("이름", key=f"add_lbl_{list_key}", placeholder="항목 이름")
        with a2: add_img   = st.text_input("URL",  key=f"add_img_{list_key}", placeholder="https://...")
        with a3: add_price = st.number_input("가격", min_value=0, step=100, key=f"add_price_{list_key}")
        if st.button("＋ 항목 추가", key=f"add_btn_{list_key}", use_container_width=True):
            if add_label.strip():
                from notification_store import push_all
                add_list_item(list_key, add_label, add_img, add_price)
                push_all(get_all_user_ids(),"item_added",f"'{add_label}' 항목이 추가됐습니다.")
                st.success("추가"); st.rerun()
            else: st.warning("이름을 입력해 주세요.")

        st.divider()
        if st.button(f"🗑️ 이 리스트 삭제 ({info.get('title',list_key)})",
                     key=f"del_list_{list_key}", type="secondary"):
            from notification_store import push_all
            push_all(get_all_user_ids(),"item_deleted",
                     f"리스트 '{info.get('title',list_key)}'이 삭제됐습니다.")
            delete_list(list_key)
            st.success("리스트 삭제 완료"); st.rerun()


# ── 모달 팝업 ─────────────────────────────────────────────────────────────────
if st.session_state.modal_item is not None:
    mtype = st.session_state.modal_type
    if mtype == "essentials":
        render_essentials_popup(st.session_state.modal_item)
    elif mtype == "cvs":
        render_cvs_popup(st.session_state.modal_item)

else:
    page = st.session_state.page

    if page == "main":
        lists = get_lists()
        for list_key, info in lists.items():
            ltype = info.get("type","essentials")
            if is_admin:
                render_admin_editor(list_key, info)
            render_card_section(info.get("title",list_key), info.get("items",[]),
                                 list_key, ltype)

        # 관리자: 새 리스트 추가
        if is_admin:
            st.markdown("---")
            with st.expander("➕ 새 리스트 추가", expanded=False):
                new_list_title = st.text_input("리스트 제목", key="new_list_title",
                                                placeholder="예: 냉동식품")
                new_list_type  = st.radio(
                    "리스트 타입",
                    options=["essentials", "cvs"],
                    format_func=lambda x: "🧴 생필품 (정기구메)" if x=="essentials" else "🏪 편의점",
                    horizontal=True,
                    key="new_list_type",
                )
                if st.button("➕ 리스트 추가", key="add_list_btn", use_container_width=True):
                    if new_list_title.strip():
                        new_key = add_list(new_list_title, new_list_type)
                        from notification_store import push_all
                        push_all(get_all_user_ids(), "item_added",
                                 f"새 리스트 '{new_list_title}'이 추가됐습니다.")
                        st.success(f"'{new_list_title}' 리스트 추가 완료!"); st.rerun()
                    else:
                        st.warning("제목을 입력해 주세요.")

    elif page == "wishlist":
        render_wishlist_page()

    elif page == "my":
        if is_logged: render_my_page()
        else:         render_auth_page()

# ── 하단 네비게이션 ───────────────────────────────────────────────────────────
nc1,nc2,nc3 = st.columns(3)
with nc1:
    if st.button("🏪", key="nav_wish", help="편의점파티·룰렛", use_container_width=True):
        st.session_state.modal_item=None; st.session_state.page="wishlist"; st.rerun()
with nc2:
    if st.button("🏠", key="nav_home", help="홈", use_container_width=True):
        st.session_state.modal_item=None; st.session_state.page="main"; st.rerun()
with nc3:
    icon = "🛡️" if is_admin else ("👤✓" if is_logged else "👤")
    if st.button(icon, key="nav_my", help="마이페이지", use_container_width=True):
        st.session_state.modal_item=None; st.session_state.page="my"; st.rerun()
      
