"""project.py — 메인 앱 진입점"""

import streamlit as st
import streamlit.components.v1 as components

from auth     import render_auth_page, render_my_page
from pot_page import render_item_popup
from user_store import (
    initialize, get_lists, get_all_user_ids,
    add_list, delete_list,
    update_list_title, add_list_item, update_list_item, delete_list_item,
)
from pot_store          import disband_pots_for_item
from notification_store import push, push_all, get_notifications, get_unread_count, mark_all_read, clear_notifications

# ── 초기화 ────────────────────────────────────────────────────────────────────
initialize()

st.set_page_config(page_title="My App", layout="wide", initial_sidebar_state="collapsed")

for k, v in [("page","main"),("pot_modal_item",None),("pot_sub","main"),
              ("viewing_pot_id",None),("show_notif",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── 전역 CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html,body,[data-testid="stAppViewContainer"]{background:#F7F5F0;font-family:'DM Sans',sans-serif;}
[data-testid="stHeader"]{display:none;}
[data-testid="stSidebar"]{display:none;}
.main .block-container{max-width:1100px;padding:0 2rem 6rem 2rem;margin:0 auto;}

.top-header{display:flex;align-items:center;justify-content:space-between;
  padding:1.6rem 0 1.2rem 0;border-bottom:2px solid #1a1a1a;margin-bottom:2.4rem;}
.logo-text{font-family:'DM Serif Display',serif;font-size:2rem;color:#1a1a1a;}

.notif-panel{background:#fff;border:1.5px solid #E5E7EB;border-radius:16px;
  padding:1rem 1.2rem;margin-bottom:1.2rem;
  box-shadow:0 8px 32px rgba(0,0,0,.12);}
.notif-item{padding:.6rem 0;border-bottom:1px solid #F3F4F6;
  font-size:.83rem;color:#374151;}
.notif-item:last-child{border-bottom:none;}
.notif-time{font-size:.7rem;color:#9CA3AF;margin-top:.15rem;}

/* 하단 네비바 */
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"]{
  position:fixed !important;bottom:0 !important;left:0 !important;right:0 !important;
  width:100% !important;max-width:100% !important;
  padding:0 !important;margin:0 !important;gap:0 !important;
  background:#ffffff !important;border-top:1px solid #E5E7EB !important;
  box-shadow:0 -4px 20px rgba(0,0,0,.06) !important;
  z-index:9999 !important;display:flex !important;
  align-items:stretch !important;height:64px !important;}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{
  flex:1 !important;padding:0 !important;min-width:0 !important;}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] button{
  width:100% !important;height:64px !important;
  background:transparent !important;border:none !important;border-radius:0 !important;
  box-shadow:none !important;font-size:1.5rem !important;cursor:pointer !important;
  transition:background .2s !important;color:#6B7280 !important;padding:0 !important;
  display:flex !important;align-items:center !important;justify-content:center !important;}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] button:hover{
  background:#EFF6FF !important;color:#3B82F6 !important;}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] button p{display:none !important;}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] .stElementContainer{padding:0 !important;}
</style>
""", unsafe_allow_html=True)

# ── 현재 유저 정보 ────────────────────────────────────────────────────────────
is_logged_in = "user" in st.session_state
is_admin     = st.session_state.get("user", {}).get("is_admin", False)
uid          = st.session_state.get("user", {}).get("user_id", "")

# ── 상단 헤더 + 알림 아이콘 ──────────────────────────────────────────────────
notif_count = get_unread_count(uid) if is_logged_in else 0
notif_icon  = f"🔔({notif_count})" if notif_count > 0 else "🔔"

h_left, h_right = st.columns([9, 1])
with h_left:
    st.markdown('<div class="top-header"><span class="logo-text">My App</span></div>',
                unsafe_allow_html=True)
with h_right:
    st.markdown("<div style='height:1.3rem'></div>", unsafe_allow_html=True)
    if is_logged_in:
        if st.button(notif_icon, key="notif_btn", help="알림"):
            st.session_state.show_notif = not st.session_state.show_notif
            if st.session_state.show_notif:
                mark_all_read(uid)
            st.rerun()

# ── 알림 패널 ─────────────────────────────────────────────────────────────────
if st.session_state.show_notif and is_logged_in:
    notifs = get_notifications(uid)
    type_icon = {"item_added":"🆕","item_deleted":"🗑️","item_price_changed":"💰",
                 "pot_joined":"🛒","pot_ended":"✅","pot_disbanded":"💔"}
    st.markdown('<div class="notif-panel">', unsafe_allow_html=True)
    st.markdown("**🔔 알림**")
    if not notifs:
        st.caption("새 알림이 없습니다.")
    else:
        for n in notifs[:20]:
            icon = type_icon.get(n["type"], "📢")
            st.markdown(f"""
            <div class="notif-item">
              {icon} {n['message']}
              <div class="notif-time">{n['created_at']}</div>
            </div>""", unsafe_allow_html=True)
    pc1, pc2 = st.columns(2)
    with pc1:
        if st.button("✕ 닫기", key="close_notif", use_container_width=True):
            st.session_state.show_notif = False; st.rerun()
    with pc2:
        if st.button("전체 삭제", key="clear_notif", use_container_width=True):
            clear_notifications(uid)
            st.session_state.show_notif = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── 카드 섹션 렌더 ────────────────────────────────────────────────────────────
def render_card_section(title: str, items: list, list_key: str):
    """
    카드 썸네일(components.html) + 바로 아래 동일 너비 구메팟 버튼(Streamlit).
    카드와 버튼이 1:1로 같은 너비로 정렬됨.
    """
    st.markdown(
        f'<p style="font-size:1rem;font-weight:600;color:#1a1a1a;'
        f'letter-spacing:.06em;text-transform:uppercase;margin-bottom:.6rem;">{title}</p>',
        unsafe_allow_html=True)

    n = len(items)
    if n == 0:
        st.caption("항목이 없습니다.")
        return

    # ── 카드 썸네일 슬라이더 ──────────────────────────────────────────────
    cards_html = ""
    for item in items:
        label = item.get("label", "")
        img   = item.get("image_url", "")
        price = item.get("price", 0)
        bg    = f"url('{img}') center/cover no-repeat" if img else "linear-gradient(135deg,#EEF4FF,#DBEAFE)"
        ptag  = f'<span class="card-price">{price:,}원</span>' if price else ""
        cards_html += (f'<div class="card">'
                       f'<div class="card-img" style="background:{bg};"></div>'
                       f'{ptag}<span class="card-label">{label}</span></div>')

    components.html(f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:transparent;font-family:'DM Sans',sans-serif;padding:0 0 2px 0;}}
.card-row{{display:flex;gap:1.2rem;overflow-x:auto;background:#EDEBE5;
  border-radius:14px;padding:1.2rem;border:1.5px solid #D8D4CB;}}
.card-row::-webkit-scrollbar{{height:4px;}}
.card-row::-webkit-scrollbar-thumb{{background:#C2BEAF;border-radius:4px;}}
.card{{flex:0 0 200px;height:220px;border-radius:12px;border:2px solid #3B82F6;
  background:#fff;display:flex;flex-direction:column;align-items:center;
  justify-content:flex-end;padding-bottom:.8rem;position:relative;overflow:hidden;}}
.card-img{{position:absolute;inset:0;}}
.card-price{{position:absolute;top:8px;right:8px;font-size:.68rem;font-weight:700;
  color:#fff;background:rgba(59,130,246,.85);padding:.15rem .55rem;border-radius:20px;}}
.card-label{{position:relative;font-size:.78rem;font-weight:600;color:#3B82F6;
  letter-spacing:.04em;background:rgba(255,255,255,.88);
  padding:.25rem .7rem;border-radius:20px;}}
</style></head><body>
<div class="card-row">{cards_html}</div>
</body></html>""", height=265, scrolling=False)

    # ── 구메팟 버튼: 카드와 동일 너비, 바로 아래 ─────────────────────────
    # 카드가 200px 고정폭이므로 columns로 동일하게 나눔
    cols = st.columns(n)
    for i, (col, item) in enumerate(zip(cols, items)):
        with col:
            label = item.get("label", f"Item {i+1}")
            if st.button(f"🛒 {label}", key=f"card_{list_key}_{i}",
                         use_container_width=True):
                st.session_state.pot_modal_item = item
                st.session_state.pot_sub = "main"
                st.rerun()

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)


# ── 관리자 편집 패널 ──────────────────────────────────────────────────────────
def render_admin_editor(list_key: str, info: dict, can_delete_list: bool):
    with st.expander(f"⚙️ [{list_key.upper()}] 편집 패널", expanded=False):
        st.markdown(
            '<p style="font-size:.72rem;font-weight:700;color:#D97706;'
            'letter-spacing:.08em;text-transform:uppercase;">🛡️ 관리자 편집 모드</p>',
            unsafe_allow_html=True)

        # 리스트 전체 삭제 (list1·list2 제외)
        if can_delete_list:
            if st.button(f"🗑️ 이 리스트 전체 삭제 ({info['title']})",
                         key=f"del_list_{list_key}"):
                all_uids = get_all_user_ids()
                # 이 리스트의 모든 항목에 연결된 팟 해산
                for item in info.get("items", []):
                    affected = disband_pots_for_item(item["label"])
                    for pot in affected:
                        push_all(pot["members"], "pot_disbanded",
                                 f"'{item['label']}' 항목이 삭제되어 팟이 해산됐습니다.")
                push_all(all_uids, "item_deleted",
                         f"리스트 '{info['title']}'이 삭제됐습니다.")
                delete_list(list_key)
                st.success("리스트 삭제 완료"); st.rerun()
            st.divider()

        # 제목 수정
        new_title = st.text_input("리스트 제목", value=info["title"],
                                  key=f"title_{list_key}")
        if st.button("제목 저장", key=f"save_title_{list_key}"):
            update_list_title(list_key, new_title)
            st.success("저장 완료"); st.rerun()

        st.divider()
        st.markdown("**항목 관리**")
        all_uids = get_all_user_ids()

        for i, item in enumerate(info["items"]):
            c1, c2, c3, c4 = st.columns([3, 4, 2, 1])
            with c1:
                new_label = st.text_input(f"이름 #{i+1}", value=item["label"],
                                          key=f"lbl_{list_key}_{i}")
            with c2:
                new_img   = st.text_input(f"URL #{i+1}", value=item.get("image_url",""),
                                          key=f"img_{list_key}_{i}", placeholder="https://...")
            with c3:
                old_price = int(item.get("price", 0))
                new_price = st.number_input(f"가격 #{i+1}", value=old_price,
                                            min_value=0, step=100, key=f"price_{list_key}_{i}")
            with c4:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{list_key}_{i}"):
                    removed = delete_list_item(list_key, i)
                    if removed:
                        affected = disband_pots_for_item(removed["label"])
                        for pot in affected:
                            push_all(pot["members"], "pot_disbanded",
                                     f"'{removed['label']}' 항목 삭제로 팟이 해산됐습니다.")
                        push_all(all_uids, "item_deleted",
                                 f"'{removed['label']}' 항목이 삭제됐습니다.")
                        st.success("삭제 완료")
                    else:
                        st.warning("최소 1개 항목은 유지해야 합니다.")
                    st.rerun()

            if st.button(f"저장 #{i+1}", key=f"save_{list_key}_{i}"):
                price_changed = (new_price != old_price)
                update_list_item(list_key, i, new_label, new_img, new_price)
                if price_changed:
                    push_all(all_uids, "item_price_changed",
                             f"'{new_label}' 가격이 {new_price:,}원으로 변경됐습니다.")
                else:
                    push_all(all_uids, "item_added",
                             f"'{new_label}' 항목 정보가 업데이트됐습니다.")
                st.success(f"항목 {i+1} 저장"); st.rerun()

        st.divider()
        st.markdown("**새 항목 추가**")
        a1, a2, a3 = st.columns([3, 4, 2])
        with a1: add_label = st.text_input("이름", key=f"add_lbl_{list_key}",
                                            placeholder="항목 이름")
        with a2: add_img   = st.text_input("이미지 URL", key=f"add_img_{list_key}",
                                            placeholder="https://...")
        with a3: add_price = st.number_input("가격(원)", min_value=0, step=100,
                                              key=f"add_price_{list_key}")
        if st.button("＋ 항목 추가", key=f"add_btn_{list_key}", use_container_width=True):
            if add_label.strip():
                add_list_item(list_key, add_label, add_img, add_price)
                push_all(get_all_user_ids(), "item_added",
                         f"새 항목 '{add_label}'이 추가됐습니다.")
                st.success("추가 완료"); st.rerun()
            else:
                st.warning("이름을 입력해 주세요.")


# ── 팝업 / 페이지 콘텐츠 ─────────────────────────────────────────────────────
if st.session_state.pot_modal_item is not None:
    render_item_popup(st.session_state.pot_modal_item)

else:
    page = st.session_state.page

    if page == "main":
        lists = get_lists()

        for list_key, info in lists.items():
            can_delete = list_key not in ("list1", "list2")
            if is_admin:
                render_admin_editor(list_key, info, can_delete_list=can_delete)
            render_card_section(info.get("title", list_key), info.get("items", []), list_key)

        # 관리자: 새 리스트 추가 버튼
        if is_admin:
            st.markdown("---")
            st.markdown("**➕ 새 리스트 추가**")
            new_list_title = st.text_input("새 리스트 제목", key="new_list_title",
                                            placeholder="예: 인기 상품")
            if st.button("리스트 추가", key="add_list_btn"):
                if new_list_title.strip():
                    new_key = add_list(new_list_title)
                    push_all(get_all_user_ids(), "item_added",
                             f"새 리스트 '{new_list_title}'이 추가됐습니다.")
                    st.success(f"리스트 '{new_list_title}' 추가 완료!"); st.rerun()
                else:
                    st.warning("리스트 제목을 입력해 주세요.")

    elif page == "wishlist":
        st.markdown('<p style="font-size:1.05rem;font-weight:600;letter-spacing:.06em;'
                    'text-transform:uppercase;margin-bottom:1rem">❤️ Wishlist</p>',
                    unsafe_allow_html=True)
        st.info("위시리스트 페이지입니다.")

    elif page == "my":
        if is_logged_in: render_my_page()
        else:            render_auth_page()

# ── 하단 네비게이션 ───────────────────────────────────────────────────────────
nc1, nc2, nc3 = st.columns(3)
with nc1:
    if st.button("🍎", key="nav_wish", help="Wishlist", use_container_width=True):
        st.session_state.pot_modal_item = None
        st.session_state.page = "wishlist"; st.rerun()
with nc2:
    if st.button("🏠", key="nav_home", help="Home", use_container_width=True):
        st.session_state.pot_modal_item = None
        st.session_state.page = "main"; st.rerun()
with nc3:
    icon = "🛡️" if is_admin else ("👤✓" if is_logged_in else "👤")
    if st.button(icon, key="nav_my", help="My Page", use_container_width=True):
        st.session_state.pot_modal_item = None
        st.session_state.viewing_pot_id = None
        st.session_state.page = "my"; st.rerun()
