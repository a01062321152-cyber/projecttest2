import streamlit as st
import streamlit.components.v1 as components

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Main Page",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 페이지 상태 초기화 ────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "main"

# ── 전역 CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #F7F5F0;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }

.main .block-container {
    max-width: 1100px;
    padding: 0 2rem 6rem 2rem;
    margin: 0 auto;
}

/* 상단 헤더 */
.top-header {
    display: flex;
    align-items: center;
    padding: 1.6rem 0 1.2rem 0;
    border-bottom: 2px solid #1a1a1a;
    margin-bottom: 2.4rem;
}
.logo-text {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #1a1a1a;
}

/* ── 하단 네비바 컨테이너 ── */
/* Streamlit이 생성하는 버튼 3개를 감싸는 row를 고정 바로 만들기 */
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background: #ffffff !important;
    border-top: 1px solid #E5E7EB !important;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.06) !important;
    z-index: 9999 !important;
    display: flex !important;
    align-items: stretch !important;
    gap: 0 !important;
    height: 64px !important;
}

/* 각 column */
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"] {
    flex: 1 !important;
    padding: 0 !important;
    min-width: 0 !important;
}

/* 버튼 base */
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"]
  button {
    width: 100% !important;
    height: 64px !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    font-size: 1.5rem !important;
    line-height: 1 !important;
    cursor: pointer !important;
    transition: background 0.2s ease !important;
    color: #6B7280 !important;
    padding: 0 !important;
    /* 텍스트(레이블) 숨기기 — 이모지만 표시 */
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"]
  button:hover {
    background: #EFF6FF !important;
    color: #3B82F6 !important;
}

/* stMarkdown 툴팁 wrapper는 사용 안 하므로 숨김 */
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"]
  .stElementContainer { padding: 0 !important; }

/* 버튼 p 태그 (레이블 텍스트) 숨기기 */
section.main > div.block-container > div:last-child
  > div[data-testid="stHorizontalBlock"]
  button p { display: none !important; }

</style>
""", unsafe_allow_html=True)

# ── 상단 헤더 ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="top-header"><span class="logo-text">My App</span></div>',
    unsafe_allow_html=True,
)

# ── 카드 섹션 렌더링 함수 ─────────────────────────────────────────────────────
def render_card_section(title: str, items: list, height: int = 310):
    cards_inner = ""
    for item in items:
        cards_inner += f"""
        <div class="card">
          <div class="card-img"></div>
          <span class="card-label">{item['label']}</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'DM Sans', sans-serif; padding: 0 0 4px 0; }}
  .section-title {{
    font-size: 1.0rem; font-weight: 600; color: #1a1a1a;
    letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.9rem;
  }}
  .card-row {{
    display: flex; gap: 1.2rem; overflow-x: auto;
    background: #EDEBE5; border-radius: 14px;
    padding: 1.2rem; border: 1.5px solid #D8D4CB;
  }}
  .card-row::-webkit-scrollbar {{ height: 4px; }}
  .card-row::-webkit-scrollbar-thumb {{ background: #C2BEAF; border-radius: 4px; }}
  .card {{
    flex: 0 0 200px; height: 220px; border-radius: 12px;
    border: 2px solid #3B82F6; background: #fff;
    display: flex; flex-direction: column;
    align-items: center; justify-content: flex-end;
    padding-bottom: 1rem; cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    position: relative; overflow: hidden;
  }}
  .card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 28px rgba(59,130,246,0.18); }}
  .card-img {{ position: absolute; inset: 0; background: linear-gradient(135deg, #EEF4FF 0%, #DBEAFE 100%); }}
  .card-label {{
    position: relative; font-size: 0.78rem; font-weight: 600;
    color: #3B82F6; letter-spacing: 0.04em;
    background: rgba(255,255,255,0.85); padding: 0.25rem 0.7rem; border-radius: 20px;
  }}
</style>
</head>
<body>
  <div class="section-title">{title}</div>
  <div class="card-row">{cards_inner}</div>
</body></html>"""

    components.html(html, height=height, scrolling=False)


# ── 페이지 콘텐츠 ─────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "main":
    render_card_section("List 1 — Title", [
        {"label": "Item A"}, {"label": "Item B"}, {"label": "Item C"},
        {"label": "Item D"}, {"label": "Item E"},
    ])
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    render_card_section("List 2 — Title", [
        {"label": "Item 1"}, {"label": "Item 2"},
        {"label": "Item 3"}, {"label": "Item 4"},
    ])

elif page == "wishlist":
    st.markdown('<p style="font-size:1.05rem;font-weight:600;letter-spacing:0.06em;'
                'text-transform:uppercase;margin-bottom:1rem">❤️ Wishlist</p>',
                unsafe_allow_html=True)
    st.info("위시리스트 페이지입니다. 원하는 항목을 추가해 보세요.")

elif page == "my":
    st.markdown('<p style="font-size:1.05rem;font-weight:600;letter-spacing:0.06em;'
                'text-transform:uppercase;margin-bottom:1rem">👤 My Page</p>',
                unsafe_allow_html=True)
    st.info("마이페이지입니다. 프로필 정보를 확인하세요.")

# ── 하단 네비게이션 버튼 (Streamlit 네이티브 — CSS로 고정 바로 변환) ──────────
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🍎", key="nav_wish", help="Wishlist", use_container_width=True):
        st.session_state.page = "wishlist"
        st.rerun()

with col2:
    if st.button("🏠", key="nav_home", help="Home", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()

with col3:
    if st.button("👤", key="nav_my", help="My Page", use_container_width=True):
        st.session_state.page = "my"
        st.rerun()
        
