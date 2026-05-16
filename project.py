import streamlit as st

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

    /* 전체 배경 */
    html, body, [data-testid="stAppViewContainer"] {
        background: #F7F5F0;
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid="stHeader"] { display: none; }
    [data-testid="stSidebar"] { display: none; }

    /* 콘텐츠 최대 너비 */
    .main .block-container {
        max-width: 1100px;
        padding: 0 2rem 6rem 2rem;
        margin: 0 auto;
    }

    /* ── 상단 헤더 ── */
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

    /* ── 섹션 타이틀 ── */
    .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1a1a1a;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    /* ── 카드 슬라이더 래퍼 ── */
    .card-row {
        display: flex;
        gap: 1.2rem;
        overflow-x: auto;
        padding-bottom: 0.6rem;
        margin-bottom: 2.8rem;
        background: #EDEBE5;
        border-radius: 14px;
        padding: 1.2rem;
        border: 1.5px solid #D8D4CB;
    }
    .card-row::-webkit-scrollbar { height: 4px; }
    .card-row::-webkit-scrollbar-thumb { background: #C2BEAF; border-radius: 4px; }

    /* ── 카드 ── */
    .card {
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
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 28px rgba(59,130,246,0.18);
    }
    .card-img {
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, #EEF4FF 0%, #DBEAFE 100%);
    }
    .card-label {
        position: relative;
        font-size: 0.78rem;
        font-weight: 600;
        color: #3B82F6;
        letter-spacing: 0.04em;
        background: rgba(255,255,255,0.85);
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
    }

    /* ── 하단 네비게이션 바 ── */
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

    /* 각 버튼 래퍼 — tooltip 기준점 */
    .nav-item {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 56px;
        height: 56px;
        cursor: pointer;
    }

    /* 아이콘 링크 */
    .nav-item a {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border-radius: 12px;
        border: none;
        background: transparent;
        color: #9CA3AF;
        font-size: 1.45rem;
        text-decoration: none;
        transition: color 0.2s ease, background 0.2s ease, transform 0.2s ease;
    }
    .nav-item a:hover {
        color: #3B82F6;
        background: #EFF6FF;
        transform: translateY(-2px);
    }

    /* 툴팁 */
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
    /* 툴팁 아래 꼬리 */
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

# ── 현재 페이지 상태 ──────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "main"

# ── 상단 헤더 ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="top-header">
        <span class="logo-text">My App</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 페이지 라우팅 ─────────────────────────────────────────────────────────────
page = st.session_state.page

# ────────────────────────────────────────
# MAIN PAGE
# ────────────────────────────────────────
if page == "main":

    # List 1
    st.markdown('<div class="section-title">List 1 — Title</div>', unsafe_allow_html=True)

    list1_items = [
        {"label": "Item A"},
        {"label": "Item B"},
        {"label": "Item C"},
        {"label": "Item D"},
        {"label": "Item E"},
    ]

    cards_html = '<div class="card-row">'
    for item in list1_items:
        cards_html += f"""
        <div class="card">
            <div class="card-img"></div>
            <span class="card-label">{item['label']}</span>
        </div>
        """
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # List 2
    st.markdown('<div class="section-title">List 2 — Title</div>', unsafe_allow_html=True)

    list2_items = [
        {"label": "Item 1"},
        {"label": "Item 2"},
        {"label": "Item 3"},
        {"label": "Item 4"},
    ]

    cards2_html = '<div class="card-row">'
    for item in list2_items:
        cards2_html += f"""
        <div class="card">
            <div class="card-img"></div>
            <span class="card-label">{item['label']}</span>
        </div>
        """
    cards2_html += "</div>"
    st.markdown(cards2_html, unsafe_allow_html=True)

# ────────────────────────────────────────
# WISHLIST PAGE
# ────────────────────────────────────────
elif page == "wishlist":
    st.markdown('<div class="section-title">❤️ Wishlist</div>', unsafe_allow_html=True)
    st.info("위시리스트 페이지입니다. 원하는 항목을 추가해 보세요.")

# ────────────────────────────────────────
# MY PAGE
# ────────────────────────────────────────
elif page == "my":
    st.markdown('<div class="section-title">👤 My Page</div>', unsafe_allow_html=True)
    st.info("마이페이지입니다. 프로필 정보를 확인하세요.")

# ── 하단 네비게이션 바 (HTML 고정 바 + 툴팁) ────────────────────────────────
# ?page= 쿼리 파라미터로 페이지 전환 (JavaScript → Streamlit URL)
st.markdown(
    """
    <div class="bottom-nav">

        <div class="nav-item">
            <a href="?page=wishlist" title="">🍎</a>
            <div class="nav-tooltip">Wishlist</div>
        </div>

        <div class="nav-item">
            <a href="?page=main" title="">🏠</a>
            <div class="nav-tooltip">Home</div>
        </div>

        <div class="nav-item">
            <a href="?page=my" title="">👤</a>
            <div class="nav-tooltip">My Page</div>
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)

# ── 쿼리 파라미터로 페이지 상태 동기화 ──────────────────────────────────────
params = st.query_params
if "page" in params:
    queried = params["page"]
    if queried != st.session_state.page:
        st.session_state.page = queried
        st.rerun()
