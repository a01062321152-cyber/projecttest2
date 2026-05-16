"""project.py — 메인 앱 진입점"""

import streamlit as st
import streamlit.components.v1 as components

from auth           import render_auth_page, render_my_page
from wishlist_page  import render_wishlist_page, validate_image_url
from essentials_page import render_essentials_popup
from user_store     import (initialize, get_lists, get_all_user_ids, get_list_type,
                             update_list_title, update_list_type, add_list_item,
                             update_list_item, delete_list_item, add_list, delete_list)
from notification_store import (get_notifications, get_unread_count,
                                 mark_all_read, clear_notifications)

# ── 초기화 ────────────────────────────────────────────────────────────────────
initialize()

st.set_page_config(page_title="원박스", layout="wide", initial_sidebar_state="collapsed")

for k, v in [("page","main"),("modal_item",None),("modal_type",None),
              ("show_notif",False),("ess_sub","main"),("ess_party_id",None),
              ("cvs_sub","list"),("cvs_party_id",None)]:
    if k not in st.session_state: st.session_state[k] = v

# ── 전역 CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── 기본 배경 ── */
html,body,[data-testid="stAppViewContainer"]{
  background:#F0F4FF;font-family:'DM Sans',sans-serif;color:#0F172A;}
[data-testid="stHeader"]{display:none;}
[data-testid="stSidebar"]{display:none;}
.main .block-container{max-width:1100px;padding:0 2rem 6rem 2rem;margin:0 auto;}

/* ── 상단 헤더 ── */
.top-header{display:flex;align-items:center;justify-content:space-between;
  padding:1.6rem 0 1.2rem 0;
  border-bottom:2px solid #2563EB;margin-bottom:2.4rem;
  background:transparent;}
.logo-text{font-family:'DM Serif Display',serif;font-size:2rem;
  color:#2563EB;letter-spacing:-.02em;}

/* ── 배지 ── */
.list-type-badge{display:inline-block;font-size:.7rem;font-weight:700;
  padding:.15rem .55rem;border-radius:20px;margin-left:.5rem;vertical-align:middle;}
.badge-essentials{background:#DBEAFE;color:#1D4ED8;}

/* ── 알림 패널 ── */
.notif-panel{background:#FFFFFF;border:1.5px solid #BFDBFE;border-radius:16px;
  padding:1rem 1.2rem;margin-bottom:1.2rem;
  box-shadow:0 8px 32px rgba(37,99,235,.08);}
.notif-item{padding:.6rem 0;border-bottom:1px solid #EFF6FF;
  font-size:.83rem;color:#1E3A5F;}
.notif-item:last-child{border-bottom:none;}
.notif-time{font-size:.7rem;color:#94A3B8;margin-top:.15rem;}

/* ── 카드 ── */
.card-img-wrap{width:100%;aspect-ratio:4/3;
  border-radius:12px 12px 0 0;overflow:hidden;position:relative;
  border:2px solid #BFDBFE;border-bottom:none;
  background:linear-gradient(135deg,#EFF6FF,#DBEAFE);}
.card-img-wrap img{width:100%;height:100%;object-fit:cover;display:block;}
.card-img-placeholder{width:100%;height:100%;
  display:flex;align-items:center;justify-content:center;font-size:2.5rem;}
.card-price-tag{position:absolute;top:8px;right:8px;font-size:.68rem;font-weight:700;
  color:#fff;background:#2563EB;padding:.15rem .55rem;border-radius:20px;}

/* ── 카드 하단 버튼 ── */
div[data-card-btn] > div > button{
  border-radius:0 0 12px 12px !important;
  border:2px solid #BFDBFE !important;border-top:none !important;
  background:#FFFFFF !important;color:#2563EB !important;
  font-weight:600 !important;font-size:.82rem !important;
  padding:.55rem .5rem !important;transition:all .15s !important;}
div[data-card-btn] > div > button:hover{
  background:#EFF6FF !important;border-color:#2563EB !important;}

/* ── Streamlit 기본 요소 화이트/블루 통일 ── */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] select,
textarea{
  background:#FFFFFF !important;
  border:1.5px solid #BFDBFE !important;
  border-radius:8px !important;
  color:#0F172A !important;}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus,
textarea:focus{
  border-color:#2563EB !important;
  box-shadow:0 0 0 3px rgba(37,99,235,.12) !important;}

/* 버튼 전체 스타일 */
div[data-testid="stButton"] > button{
  background:#FFFFFF !important;
  border:1.5px solid #BFDBFE !important;
  color:#2563EB !important;
  border-radius:10px !important;
  font-weight:600 !important;
  transition:all .15s !important;}
div[data-testid="stButton"] > button:hover{
  background:#EFF6FF !important;
  border-color:#2563EB !important;}
div[data-testid="stButton"] > button[kind="primary"]{
  background:#2563EB !important;
  border-color:#2563EB !important;
  color:#FFFFFF !important;}
div[data-testid="stButton"] > button[kind="primary"]:hover{
  background:#1D4ED8 !important;}

/* expander */
div[data-testid="stExpander"]{
  border:1.5px solid #BFDBFE !important;
  border-radius:12px !important;
  background:#FFFFFF !important;}

/* info/success/warning/error 박스 */
div[data-testid="stAlert"]{border-radius:10px !important;}

/* 탭 */
button[data-baseweb="tab"]{
  color:#64748B !important;font-weight:600 !important;}
button[data-baseweb="tab"][aria-selected="true"]{
  color:#2563EB !important;
  border-bottom:2px solid #2563EB !important;}

/* ── 하단 네비바 ── */
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"]{
  position:fixed !important;bottom:0 !important;left:0 !important;right:0 !important;
  width:100% !important;max-width:100% !important;
  padding:0 !important;margin:0 !important;gap:0 !important;
  background:#FFFFFF !important;
  border-top:2px solid #DBEAFE !important;
  box-shadow:0 -4px 20px rgba(37,99,235,.08) !important;
  z-index:9999 !important;display:flex !important;
  align-items:stretch !important;height:64px !important;}
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"]{flex:1 !important;padding:0 !important;min-width:0 !important;}
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"] button{
  width:100% !important;height:64px !important;
  background:transparent !important;border:none !important;
  border-radius:0 !important;box-shadow:none !important;
  font-size:1.5rem !important;cursor:pointer !important;
  transition:background .2s !important;
  color:#94A3B8 !important;padding:0 !important;
  display:flex !important;align-items:center !important;justify-content:center !important;}
section.main > div.block-container > div:last-child > div[data-testid="stHorizontalBlock"]
  button:hover{background:#EFF6FF !important;color:#2563EB !important;}
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
    st.markdown('<div class="top-header"><span class="logo-text">원박스</span></div>',
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
    type_icon = {"item_added":"🆕 신규 등록","item_deleted":"🗑️ 삭제","item_price_changed":"💰 가격 변경",
                 "pot_joined":"🛒 파티","pot_ended":"✅ 완료","pot_disbanded":"💔 해산"}
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
    badge_cls  = "badge-essentials"
    badge_txt  = ""
    btn_label  = "🧴 공동구매 신청"

    st.markdown(
        f'<p style="font-size:1rem;font-weight:600;color:#0F172A;'
        f'letter-spacing:.06em;text-transform:uppercase;margin-bottom:.6rem;">'
        f'{title}</p>',
        unsafe_allow_html=True)

    n = len(items)
    if n == 0:
        st.caption("항목이 없습니다.")
        return

    COLS_PER_ROW = 6
    # items를 6개씩 청크로 나눔
    chunks = [items[i:i+COLS_PER_ROW] for i in range(0, n, COLS_PER_ROW)]

    for chunk_idx, chunk in enumerate(chunks):
        cols = st.columns(len(chunk))
        for i, (col, item) in enumerate(zip(cols, chunk)):
            global_idx = chunk_idx * COLS_PER_ROW + i
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
                if st.button(f"{btn_label} {label}", key=f"card_{list_key}_{global_idx}",
                             use_container_width=True):
                    st.session_state.modal_item = item
                    st.session_state.modal_type = list_type
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # 행 사이 간격
        if chunk_idx < len(chunks) - 1:
            st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)


# ── 관리자 편집 패널 ──────────────────────────────────────────────────────────
def render_admin_editor(list_key: str, info: dict):
    with st.expander(f"⚙️ [{info.get('title',list_key)}] 편집", expanded=False):
        st.markdown('<p style="font-size:.72rem;font-weight:700;color:#B45309;'
                    'letter-spacing:.08em;text-transform:uppercase;">🛡️ 관리자 편집</p>',
                    unsafe_allow_html=True)

        new_title = st.text_input("리스트 제목", value=info["title"], key=f"title_{list_key}")
        if st.button("제목 저장", key=f"save_title_{list_key}"):
            update_list_title(list_key, new_title); st.success("저장"); st.rerun()

        # 리스트 타입 변경 (항상 essentials로 통일 가능)
        cur_type = info.get("type", "essentials")
        type_label = {"essentials": "🧴 생필품", "cvs": "🏪 편의점 (구버전)"}
        st.caption(f"현재 타입: {type_label.get(cur_type, cur_type)}")
        if cur_type != "essentials":
            if st.button("🔄 생필품 타입으로 변경", key=f"type_{list_key}"):
                update_list_type(list_key, "essentials")
                st.success("타입이 생필품으로 변경됐습니다."); st.rerun()

        st.divider()
        all_uids = get_all_user_ids()

        for i, item in enumerate(info["items"]):
            c1,c2,c3,c4 = st.columns([3,4,2,1])
            with c1: new_label = st.text_input(f"이름#{i+1}", value=item["label"], key=f"lbl_{list_key}_{i}")
            with c2: new_img   = st.text_input(f"URL#{i+1}", value=item.get("image_url",""), key=f"img_{list_key}_{i}", placeholder="https://example.com/img.jpg")
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
                img_err = validate_image_url(new_img)
                if img_err:
                    st.error(img_err)
                else:
                    from notification_store import push_all
                    update_list_item(list_key, i, new_label, new_img, new_p)
                    if new_p != old_p:
                        push_all(all_uids,"item_price_changed",
                                 f"'{new_label}' 가격이 {new_p:,}원으로 변경됐습니다.")
                    st.success("저장"); st.rerun()

        st.divider()
        a1,a2,a3 = st.columns([3,4,2])
        with a1: add_label = st.text_input("이름", key=f"add_lbl_{list_key}", placeholder="항목 이름")
        with a2: add_img   = st.text_input("URL",  key=f"add_img_{list_key}", placeholder="https://example.com/img.jpg")
        with a3: add_price = st.number_input("가격", min_value=0, step=100, key=f"add_price_{list_key}")
        if st.button("＋ 항목 추가", key=f"add_btn_{list_key}", use_container_width=True):
            if not add_label.strip():
                st.warning("이름을 입력해 주세요.")
            else:
                img_err = validate_image_url(add_img)
                if img_err:
                    st.error(img_err)
                else:
                    from notification_store import push_all
                    add_list_item(list_key, add_label, add_img, add_price)
                    push_all(get_all_user_ids(),"item_added",f"'{add_label}' 항목이 추가됐습니다.")
                    st.success("추가"); st.rerun()

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
    else:
        render_essentials_popup(st.session_state.modal_item)

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
                new_list_type = "essentials"  # 생필품 단일 타입
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
    if st.button("🎰", key="nav_wish", help="룰렛", use_container_width=True):
        st.session_state.modal_item=None; st.session_state.page="wishlist"; st.rerun()
with nc2:
    if st.button("🏠", key="nav_home", help="홈", use_container_width=True):
        st.session_state.modal_item=None; st.session_state.page="main"; st.rerun()
with nc3:
    icon = "🛡️" if is_admin else ("👤✓" if is_logged else "👤")
    if st.button(icon, key="nav_my", help="마이페이지", use_container_width=True):
        st.session_state.modal_item=None; st.session_state.page="my"; st.rerun()
