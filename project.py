import streamlit as st
import streamlit.components.v1 as components

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Main Page",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 전역 CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
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
        justify-content: space-between;
        padding: 1.6rem 0 1.2rem 0;
        border-bottom: 2px solid #1a1a1a;
        margin-bottom: 2.4rem;
    }
    .logo-text {
        font-family: 'DM Serif Display', serif;
        font-size: 2rem;
        color: #1a1a1a;
        letter-spacing: -0.5px;
    }

    /* 하단 네비게이션 바 */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: #ffffff;
        border-top: 1px solid #E5E7EB;
        display: flex;
        align-items: center;
        justify-content: space-around;
        z-index: 9999;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.06);
    }
    .nav-item {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 56px;
        height: 56px;
        cursor: pointer;
    }
    .nav-item a {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border-radius: 12px;
        border: none;
        background: transparent;
        font-size: 1.45rem;
        text-decoration: none;
        transition: background 0.2s ease, transform 0.2s ease;
    }
    .nav-item a:hover {
        background: #EFF6FF;
        transform: translateY(-2px);
    }
    .nav-tooltip {
        position: absolute;
        bottom: calc(100% + 10px);
        left: 50%;
        transform: translateX(-50%) translateY(6px);
        background: #1a1a1a;
        color: #fff;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        white-space: nowrap;
        padding: 0.35rem 0.75rem;
        border-radius: 8px;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.18s ease, transform 0.18s ease;
    }
    .nav-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 5px solid transparent;
        border-top-color: #1a1a1a;
    }
    .nav-item:hover .nav-tooltip {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── 페이지 상태 ───────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "main"

# 쿼리 파라미터 → session_state 동기화
params = st.query_params
if "page" in params and params["page"] != st.session_state.page:
    st.session_state.page = params["page"]
    st.rerun()

page = st.session_state.page

# ── 상단 헤더 ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="top-header"><span class="logo-text">My App</span></div>',
    unsafe_allow_html=True,
)


# ── 카드 섹션 렌더링 함수 (components.html 사용) ──────────────────────────────
def render_card_section(title: str, items: list, height: int = 310):
    """
    Streamlit의 마크다운 파서가 div 태그를 코드블록으로 잘못 렌더링하는 문제를
    components.html을 사용해 완전한 HTML 문서로 렌더링하여 해결합니다.
    """
    cards_inner = ""
    for item in items:
        label = item["label"]
        cards_inner += f"""
        <div class="card">
          <div class="card-img"></div>
          <span class="card-label">{label}</span>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    font-family: 'DM Sans', sans-serif;
    padding: 0 0 4px 0;
  }}
  .section-title {{
    font-size: 1.0rem;
    font-weight: 600;
    color: #1a1a1a;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 0.9rem;
  }}
  .card-row {{
    display: flex;
    gap: 1.2rem;
    overflow-x: auto;
    background: #EDEBE5;
    border-radius: 14px;
    padding: 1.2rem;
    border: 1.5px solid #D8D4CB;
  }}
  .card-row::-webkit-scrollbar {{ height: 4px; }}
  .card-row::-webkit-scrollbar-thumb {{ background: #C2BEAF; border-radius: 4px; }}
  .card {{
    flex: 0 0 200px;
    height: 220px;
    border-radius: 12px;
    border: 2px solid #3B82F6;
    background: #fff;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    padding-bottom: 1rem;
    cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    position: relative;
    overflow: hidden;
  }}
  .card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 28px rgba(59,130,246,0.18);
  }}
  .card-img {{
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #EEF4FF 0%, #DBEAFE 100%);
  }}
  .card-label {{
    position: relative;
    font-size: 0.78rem;
    font-weight: 600;
    color: #3B82F6;
    letter-spacing: 0.04em;
    background: rgba(255,255,255,0.85);
    padding: 0.25rem 0.7rem;
    border-radius: 20px;
  }}
</style>
</head>
<body>
  <div class="section-title">{title}</div>
  <div class="card-row">
    {cards_inner}
  </div>
</body>
</html>"""

    components.html(html, height=height, scrolling=False)


# ── 페이지 라우팅 ─────────────────────────────────────────────────────────────
if page == "main":
    list1_items = [
        {"label": "Item A"},
        {"label": "Item B"},
        {"label": "Item C"},
        {"label": "Item D"},
        {"label": "Item E"},
    ]
    render_card_section("List 1 — Title", list1_items)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    list2_items = [
        {"label": "Item 1"},
        {"label": "Item 2"},
        {"label": "Item 3"},
        {"label": "Item 4"},
    ]
    render_card_section("List 2 — Title", list2_items)

elif page == "wishlist":
    st.markdown('<p style="font-size:1.05rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;">❤️ Wishlist</p>', unsafe_allow_html=True)
    st.info("위시리스트 페이지입니다. 원하는 항목을 추가해 보세요.")

elif page == "my":
    st.markdown('<p style="font-size:1.05rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;">👤 My Page</p>', unsafe_allow_html=True)
    st.info("마이페이지입니다. 프로필 정보를 확인하세요.")

# ── 하단 네비게이션 바 ────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="bottom-nav">
      <div class="nav-item">
        <a href="?page=wishlist">🍎</a>
        <div class="nav-tooltip">Wishlist</div>
      </div>
      <div class="nav-item">
        <a href="?page=main">🏠</a>
        <div class="nav-tooltip">Home</div>
      </div>
      <div class="nav-item">
        <a href="?page=my">👤</a>
        <div class="nav-tooltip">My Page</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
