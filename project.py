"""
project.py  —  메인 앱 진입점
"""

import streamlit as st
import streamlit.components.v1 as components
from auth     import render_auth_page, render_my_page
from pot_page import render_item_popup
from user_store import (
    initialize, get_lists,
    update_list_title, add_list_item, update_list_item, delete_list_item,
)

# ── 초기화 ────────────────────────────────────────────────────────────────────
initialize()

st.set_page_config(page_title="My App", layout="wide", initial_sidebar_state="collapsed")

if "page" not in st.session_state:
    st.session_state.page = "main"
if "pot_modal_item" not in st.session_state:
    st.session_state.pot_modal_item = None

# ── 전역 CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background:#F7F5F0; font-family:'DM Sans',sans-serif;
}
[data-testid="stHeader"] { display:none; }
[data-testid="stSidebar"] { display:none; }
.main .block-container { max-width:1100px; padding:0 2rem 6rem 2rem; margin:0 auto; }

.top-header {
    display:flex; align-items:center;
    padding:1.6rem 0 1.2rem 0; border-bottom:2px solid #1a1a1a; margin-bottom:2.4rem;
}
.logo-text { font-family:'DM Serif Display',serif; font-size:2rem; color:#1a1a1a; }

/* 관리자 편집 패널 */
.admin-label {
    font-size:0.72rem; font-weight:700; color:#D97706;
    letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.6rem;
}

/* 하단 네비바 */
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] {
    position:fixed !important; bottom:0 !important; left:0 !important; right:0 !important;
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
    transition:background 0.2s !important; color:#6B7280 !important; padding:0 !important;
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


# ── 카드 슬라이더 렌더 (클릭 가능 — 버튼 방식) ──────────────────────────────
def render_card_section(title: str, items: list, list_key: str):
    """
    카드를 Streamlit 버튼 그리드로 렌더링.
    클릭하면 pot_modal_item에 item을 저장하고 rerun → 팝업 표시.
    """
    # 제목
    st.markdown(f"""
    <p style="font-size:1.0rem;font-weight:600;color:#1a1a1a;
       letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.8rem;">
       {title}
    </p>""", unsafe_allow_html=True)

    # 카드를 가로 스크롤 미리보기로 보여주고, 아래에 클릭 버튼 나열
    # → components.html로 썸네일 + 버튼으로 각 카드 표현
    card_btns_html = ""
    for i, item in enumerate(items):
        label = item.get("label","")
        img   = item.get("image_url","")
        bg    = f"url('{img}') center/cover no-repeat" if img else "linear-gradient(135deg,#EEF4FF,#DBEAFE)"
        card_btns_html += f"""
        <div class="card" onclick="selectCard({i})" title="{label}">
          <div class="card-img" style="background:{bg};"></div>
          <span class="card-label">{label}</span>
        </div>"""

    # 선택 인덱스를 Streamlit에 전달하는 hidden input trick
    components.html(f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:transparent;font-family:'DM Sans',sans-serif;padding:0 0 6px 0;}}
  .card-row{{display:flex;gap:1.2rem;overflow-x:auto;background:#EDEBE5;
    border-radius:14px;padding:1.2rem;border:1.5px solid #D8D4CB;}}
  .card-row::-webkit-scrollbar{{height:4px;}}
  .card-row::-webkit-scrollbar-thumb{{background:#C2BEAF;border-radius:4px;}}
  .card{{flex:0 0 200px;height:220px;border-radius:12px;border:2px solid #3B82F6;
    background:#fff;display:flex;flex-direction:column;align-items:center;
    justify-content:flex-end;padding-bottom:1rem;cursor:pointer;
    transition:transform 0.18s,box-shadow 0.18s;position:relative;overflow:hidden;}}
  .card:hover{{transform:translateY(-4px);box-shadow:0 10px 28px rgba(59,130,246,0.18);border-color:#1D4ED8;}}
  .card-img{{position:absolute;inset:0;}}
  .card-label{{position:relative;font-size:0.78rem;font-weight:600;color:#3B82F6;
    letter-spacing:0.04em;background:rgba(255,255,255,0.85);
    padding:0.25rem 0.7rem;border-radius:20px;}}
</style></head><body>
<div class="card-row">{card_btns_html}</div>
<script>
  function selectCard(idx){{
    // 부모 window로 카드 인덱스 전달
    window.parent.postMessage({{type:'CARD_CLICK', listKey:'{list_key}', idx:idx}}, '*');
  }}
</script>
</body></html>""", height=290, scrolling=False)

    # postMessage를 받아 session_state에 저장하는 JS 브릿지
    st.markdown(f"""
    <script>
    (function(){{
      if(window._cardListenerAdded_{list_key}) return;
      window._cardListenerAdded_{list_key} = true;
      window.addEventListener('message', function(e){{
        if(e.data && e.data.type === 'CARD_CLICK' && e.data.listKey === '{list_key}'){{
          // Streamlit query param으로 선택 정보 전달 후 rerun
          var url = new URL(window.location.href);
          url.searchParams.set('card_list', e.data.listKey);
          url.searchParams.set('card_idx', e.data.idx);
          window.location.href = url.toString();
        }}
      }});
    }})();
    </script>
    """, unsafe_allow_html=True)


# ── 쿼리 파라미터로 카드 선택 처리 ──────────────────────────────────────────
params = st.query_params
if "card_list" in params and "card_idx" in params and st.session_state.pot_modal_item is None:
    try:
        sel_list = params["card_list"]
        sel_idx  = int(params["card_idx"])
        lists    = get_lists()
        items    = lists.get(sel_list, {}).get("items", [])
        if 0 <= sel_idx < len(items):
            st.session_state.pot_modal_item = items[sel_idx]
            # 파라미터 제거
            st.query_params.clear()
            st.rerun()
    except Exception:
        pass


# ── 관리자 편집 패널 ──────────────────────────────────────────────────────────
def render_admin_editor(list_key: str, info: dict):
    title = info["title"]
    items = info["items"]

    with st.expander(f"⚙️ [{list_key.upper()}] 편집 패널", expanded=False):
        st.markdown('<div class="admin-label">🛡️ 관리자 편집 모드</div>', unsafe_allow_html=True)

        st.markdown("**리스트 제목**")
        new_title = st.text_input("제목", value=title, key=f"title_{list_key}", label_visibility="collapsed")
        if st.button("제목 저장", key=f"save_title_{list_key}"):
            update_list_title(list_key, new_title)
            st.success("제목 저장 완료")
            st.rerun()

        st.divider()
        st.markdown("**항목 관리**")

        for i, item in enumerate(items):
            c1, c2, c3 = st.columns([3, 5, 1])
            with c1:
                new_label = st.text_input(f"이름 #{i+1}", value=item["label"], key=f"lbl_{list_key}_{i}")
            with c2:
                new_img = st.text_input(f"이미지 URL #{i+1}", value=item.get("image_url",""),
                                        key=f"img_{list_key}_{i}", placeholder="https://...")
            with c3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{list_key}_{i}"):
                    delete_list_item(list_key, i); st.rerun()
            if st.button(f"저장 #{i+1}", key=f"save_{list_key}_{i}"):
                update_list_item(list_key, i, new_label, new_img)
                st.success(f"항목 {i+1} 저장"); st.rerun()

        st.divider()
        st.markdown("**새 항목 추가**")
        ac1, ac2 = st.columns([3, 5])
        with ac1:
            add_label = st.text_input("이름", key=f"add_lbl_{list_key}", placeholder="항목 이름")
        with ac2:
            add_img = st.text_input("이미지 URL", key=f"add_img_{list_key}", placeholder="https://...")
        if st.button("＋ 항목 추가", key=f"add_btn_{list_key}", use_container_width=True):
            if add_label.strip():
                add_list_item(list_key, add_label, add_img); st.rerun()
            else:
                st.warning("이름을 입력해 주세요.")


# ── 팝업이 열려 있으면 팝업만 표시 ──────────────────────────────────────────
if st.session_state.pot_modal_item is not None:
    render_item_popup(st.session_state.pot_modal_item)

else:
    # ── 일반 페이지 콘텐츠 ────────────────────────────────────────────────
    page         = st.session_state.page
    is_logged_in = "user" in st.session_state
    is_admin     = st.session_state.get("user", {}).get("is_admin", False)

    if page == "main":
        lists = get_lists()
        for key in ("list1", "list2"):
            info  = lists.get(key, {})
            title = info.get("title", key)
            items = info.get("items", [])

            if is_admin:
                render_admin_editor(key, info)

            render_card_section(title, items, key)
            st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    elif page == "wishlist":
        st.markdown('<p style="font-size:1.05rem;font-weight:600;letter-spacing:0.06em;'
                    'text-transform:uppercase;margin-bottom:1rem">❤️ Wishlist</p>', unsafe_allow_html=True)
        st.info("위시리스트 페이지입니다.")

    elif page == "my":
        if is_logged_in:
            render_my_page()
        else:
            render_auth_page()

# ── 하단 네비게이션 ───────────────────────────────────────────────────────────
is_logged_in = "user" in st.session_state
is_admin     = st.session_state.get("user", {}).get("is_admin", False)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🍎", key="nav_wish", help="Wishlist", use_container_width=True):
        st.session_state.pot_modal_item = None
        st.session_state.page = "wishlist"; st.rerun()
with col2:
    if st.button("🏠", key="nav_home", help="Home", use_container_width=True):
        st.session_state.pot_modal_item = None
        st.session_state.page = "main"; st.rerun()
with col3:
    icon = "🛡️" if is_admin else ("👤✓" if is_logged_in else "👤")
    if st.button(icon, key="nav_my", help="My Page", use_container_width=True):
        st.session_state.pot_modal_item = None
        st.session_state.page = "my"; st.rerun()
