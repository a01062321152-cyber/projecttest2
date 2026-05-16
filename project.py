"""
project.py  ─  메인 앱 진입점
"""

import streamlit as st
import streamlit.components.v1 as components
from auth import render_auth_page, render_my_page
from user_store import (
    initialize,
    get_lists,
    update_list_title,
    add_list_item,
    update_list_item,
    delete_list_item,
)

# ── 초기화 (admin 계정 + 기본 리스트) ────────────────────────────────────────
initialize()

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="My App", layout="wide", initial_sidebar_state="collapsed")

if "page" not in st.session_state:
    st.session_state.page = "main"

# ── 전역 CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #F7F5F0; font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }
.main .block-container { max-width: 1100px; padding: 0 2rem 6rem 2rem; margin: 0 auto; }

.top-header {
    display: flex; align-items: center;
    padding: 1.6rem 0 1.2rem 0;
    border-bottom: 2px solid #1a1a1a; margin-bottom: 2.4rem;
}
.logo-text { font-family:'DM Serif Display',serif; font-size:2rem; color:#1a1a1a; }

/* 관리자 편집 패널 */
.admin-panel {
    background: #FFFBEB;
    border: 1.5px dashed #F59E0B;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.6rem;
}
.admin-label {
    font-size: 0.72rem; font-weight: 700; color: #D97706;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.6rem;
}

/* 하단 네비바 */
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] {
    position: fixed !important; bottom:0 !important; left:0 !important; right:0 !important;
    width:100% !important; max-width:100% !important;
    padding:0 !important; margin:0 !important; gap:0 !important;
    background:#ffffff !important; border-top:1px solid #E5E7EB !important;
    box-shadow:0 -4px 20px rgba(0,0,0,0.06) !important;
    z-index:9999 !important; display:flex !important; align-items:stretch !important; height:64px !important;
}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    flex:1 !important; padding:0 !important; min-width:0 !important;
}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] button {
    width:100% !important; height:64px !important;
    background:transparent !important; border:none !important; border-radius:0 !important;
    box-shadow:none !important; font-size:1.5rem !important; cursor:pointer !important;
    transition:background 0.2s ease !important; color:#6B7280 !important; padding:0 !important;
    display:flex !important; align-items:center !important; justify-content:center !important;
}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] button:hover {
    background:#EFF6FF !important; color:#3B82F6 !important;
}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] button p { display:none !important; }
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] .stElementContainer { padding:0 !important; }
</style>
""", unsafe_allow_html=True)

# ── 상단 헤더 ─────────────────────────────────────────────────────────────────
st.markdown('<div class="top-header"><span class="logo-text">My App</span></div>', unsafe_allow_html=True)

# ── 카드 섹션 렌더링 (image_url 지원) ────────────────────────────────────────
def render_card_section(title: str, items: list, height: int = 310):
    cards_inner = ""
    for item in items:
        label     = item.get("label", "")
        image_url = item.get("image_url", "")
        if image_url:
            bg = f"url('{image_url}') center/cover no-repeat"
        else:
            bg = "linear-gradient(135deg, #EEF4FF 0%, #DBEAFE 100%)"
        cards_inner += f"""
        <div class="card">
          <div class="card-img" style="background:{bg};"></div>
          <span class="card-label">{label}</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:transparent; font-family:'DM Sans',sans-serif; padding:0 0 4px 0; }}
  .section-title {{
    font-size:1.0rem; font-weight:600; color:#1a1a1a;
    letter-spacing:0.06em; text-transform:uppercase; margin-bottom:0.9rem;
  }}
  .card-row {{
    display:flex; gap:1.2rem; overflow-x:auto;
    background:#EDEBE5; border-radius:14px;
    padding:1.2rem; border:1.5px solid #D8D4CB;
  }}
  .card-row::-webkit-scrollbar {{ height:4px; }}
  .card-row::-webkit-scrollbar-thumb {{ background:#C2BEAF; border-radius:4px; }}
  .card {{
    flex:0 0 200px; height:220px; border-radius:12px;
    border:2px solid #3B82F6; background:#fff;
    display:flex; flex-direction:column; align-items:center; justify-content:flex-end;
    padding-bottom:1rem; cursor:pointer;
    transition:transform 0.18s ease, box-shadow 0.18s ease;
    position:relative; overflow:hidden;
  }}
  .card:hover {{ transform:translateY(-4px); box-shadow:0 10px 28px rgba(59,130,246,0.18); }}
  .card-img {{ position:absolute; inset:0; }}
  .card-label {{
    position:relative; font-size:0.78rem; font-weight:600; color:#3B82F6;
    letter-spacing:0.04em; background:rgba(255,255,255,0.85);
    padding:0.25rem 0.7rem; border-radius:20px;
  }}
</style>
</head>
<body>
  <div class="section-title">{title}</div>
  <div class="card-row">{cards_inner}</div>
</body></html>"""

    components.html(html, height=height, scrolling=False)


# ── 관리자 리스트 편집 UI ─────────────────────────────────────────────────────
def render_admin_editor(list_key: str, info: dict):
    """관리자 전용 편집 패널: 제목 수정 + 항목 추가/수정/삭제"""
    title = info["title"]
    items = info["items"]

    with st.expander(f"⚙️ [{list_key.upper()}] 편집 패널", expanded=False):
        st.markdown('<div class="admin-label">🛡️ 관리자 편집 모드</div>', unsafe_allow_html=True)

        # ── 제목 수정 ──────────────────────────────────────────────────────
        st.markdown("**리스트 제목**")
        new_title = st.text_input("제목", value=title, key=f"title_{list_key}", label_visibility="collapsed")
        if st.button("제목 저장", key=f"save_title_{list_key}"):
            update_list_title(list_key, new_title)
            st.success("제목이 저장됐습니다.")
            st.rerun()

        st.divider()

        # ── 기존 항목 수정 / 삭제 ─────────────────────────────────────────
        st.markdown("**항목 관리**")
        for i, item in enumerate(items):
            with st.container():
                c1, c2, c3 = st.columns([3, 5, 1])
                with c1:
                    new_label = st.text_input(
                        f"이름 #{i+1}", value=item["label"],
                        key=f"lbl_{list_key}_{i}", label_visibility="visible"
                    )
                with c2:
                    new_img = st.text_input(
                        f"이미지 URL #{i+1}", value=item.get("image_url", ""),
                        key=f"img_{list_key}_{i}", label_visibility="visible",
                        placeholder="https://..."
                    )
                with c3:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{list_key}_{i}", help="삭제"):
                        delete_list_item(list_key, i)
                        st.rerun()

                if st.button(f"저장 #{i+1}", key=f"save_item_{list_key}_{i}"):
                    update_list_item(list_key, i, new_label, new_img)
                    st.success(f"항목 {i+1} 저장됨")
                    st.rerun()

        st.divider()

        # ── 항목 추가 (＋ 버튼) ───────────────────────────────────────────
        st.markdown("**새 항목 추가**")
        ac1, ac2 = st.columns([3, 5])
        with ac1:
            add_label = st.text_input("이름", key=f"add_lbl_{list_key}", placeholder="항목 이름")
        with ac2:
            add_img = st.text_input("이미지 URL", key=f"add_img_{list_key}", placeholder="https://...")
        if st.button("＋ 항목 추가", key=f"add_btn_{list_key}", use_container_width=True):
            if add_label.strip():
                add_list_item(list_key, add_label, add_img)
                st.success("항목이 추가됐습니다.")
                st.rerun()
            else:
                st.warning("이름을 입력해 주세요.")


# ── 페이지 콘텐츠 ─────────────────────────────────────────────────────────────
page        = st.session_state.page
is_logged_in = "user" in st.session_state
is_admin     = st.session_state.get("user", {}).get("is_admin", False)

if page == "main":
    lists = get_lists()

    for key in ("list1", "list2"):
        info  = lists.get(key, {})
        title = info.get("title", key)
        items = info.get("items", [])

        # 관리자: 편집 패널 먼저 표시
        if is_admin:
            render_admin_editor(key, info)

        # 카드 섹션 렌더링
        n_cards = len(items)
        card_h  = max(310, 260 + n_cards * 10)   # 항목 수에 따라 높이 조정
        render_card_section(title, items, height=card_h)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

elif page == "wishlist":
    st.markdown('<p style="font-size:1.05rem;font-weight:600;letter-spacing:0.06em;'
                'text-transform:uppercase;margin-bottom:1rem">❤️ Wishlist</p>', unsafe_allow_html=True)
    st.info("위시리스트 페이지입니다. 원하는 항목을 추가해 보세요.")

elif page == "my":
    if is_logged_in:
        render_my_page()
    else:
        render_auth_page()

# ── 하단 네비게이션 ───────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🍎", key="nav_wish", help="Wishlist", use_container_width=True):
        st.session_state.page = "wishlist"; st.rerun()
with col2:
    if st.button("🏠", key="nav_home", help="Home", use_container_width=True):
        st.session_state.page = "main"; st.rerun()
with col3:
    icon = "🛡️" if is_admin else ("👤✓" if is_logged_in else "👤")
    if st.button(icon, key="nav_my", help="My Page", use_container_width=True):
        st.session_state.page = "my"; st.rerun()
