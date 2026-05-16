"""
pot_page.py
───────────
카드 클릭 → 팝업 (이미지 + 구메팟 생성 / 찾기)
"""

import streamlit as st
import streamlit.components.v1 as components
from pot_store import (
    create_pot, get_pots_for_item, join_pot,
    calc_dday, price_per_person,
)

# ── CSS ───────────────────────────────────────────────────────────────────────
POT_CSS = """
<style>
/* 팝업 오버레이 */
.pot-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.45);
    z-index: 10000;
    display: flex; align-items: center; justify-content: center;
}
.pot-modal {
    background: #fff;
    border-radius: 24px;
    padding: 2rem 2.2rem 1.6rem;
    width: min(520px, 92vw);
    max-height: 85vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.25);
    position: relative;
}
.pot-modal-img {
    width: 100%; height: 200px;
    object-fit: cover; border-radius: 14px;
    margin-bottom: 1.2rem;
    background: linear-gradient(135deg,#EEF4FF,#DBEAFE);
}
.pot-modal-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem; color: #1a1a1a; margin-bottom: 1.2rem;
}
/* 팟 카드 */
.pot-card {
    border: 1.5px solid #E5E7EB;
    border-radius: 14px; padding: 1rem 1.2rem;
    margin-bottom: 0.8rem; background: #FAFAFA;
}
.pot-card-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem; }
.pot-creator { font-weight:700; color:#1a1a1a; font-size:0.95rem; }
.pot-meta    { font-size:0.8rem; color:#6B7280; }
.pot-price   { font-weight:700; color:#3B82F6; font-size:1rem; }
.pot-dday    { font-size:0.72rem; font-weight:700; color:#EF4444; background:#FEE2E2; padding:0.15rem 0.5rem; border-radius:20px; }
.pot-full    { font-size:0.72rem; color:#9CA3AF; background:#F3F4F6; padding:0.15rem 0.5rem; border-radius:20px; }
</style>
"""


def _map_picker_html(lat: float = 37.5665, lng: float = 126.9780) -> str:
    """Leaflet 지도 — 클릭하면 좌표+이름을 부모 window로 postMessage"""
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body,#map {{ margin:0;padding:0;width:100%;height:100%; }}
  #info {{ position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
           background:rgba(0,0,0,0.65);color:#fff;font-size:0.75rem;
           padding:4px 12px;border-radius:20px;z-index:999;white-space:nowrap; }}
</style>
</head><body>
<div id="map"></div>
<div id="info">지도를 클릭해 위치를 선택하세요</div>
<script>
  var map = L.map('map').setView([{lat},{lng}], 13);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
    {{attribution:'© OpenStreetMap'}}).addTo(map);
  var marker = null;
  map.on('click', function(e){{
    var lat = e.latlng.lat.toFixed(6);
    var lng = e.latlng.lng.toFixed(6);
    if(marker) map.removeLayer(marker);
    marker = L.marker([lat,lng]).addTo(map);
    var name = '위도 '+lat+', 경도 '+lng;
    document.getElementById('info').innerText = name;
    // 부모 Streamlit 앱에 postMessage
    window.parent.postMessage({{type:'MAP_PICK', lat:parseFloat(lat), lng:parseFloat(lng), name:name}}, '*');
  }});
</script>
</body></html>"""


# ── 메인 렌더 함수 ────────────────────────────────────────────────────────────

def render_item_popup(item: dict):
    """
    카드 클릭 시 호출.
    item = {"label": str, "image_url": str}
    session_state.pot_modal_item 에 item이 세팅되어 있을 때 팝업 표시.
    """
    st.markdown(POT_CSS, unsafe_allow_html=True)

    label     = item.get("label", "")
    image_url = item.get("image_url", "")
    is_logged_in = "user" in st.session_state
    user = st.session_state.get("user", {})

    # ── 팝업 서브 상태 ────────────────────────────────────────────────────
    # pot_sub: "main" | "create" | "find"
    if "pot_sub" not in st.session_state:
        st.session_state.pot_sub = "main"

    sub = st.session_state.pot_sub

    # ── 닫기 버튼 (항상 상단) ─────────────────────────────────────────────
    close_col, _ = st.columns([1, 6])
    with close_col:
        if st.button("✕ 닫기", key="pot_close"):
            st.session_state.pot_modal_item = None
            st.session_state.pot_sub = "main"
            st.rerun()

    # ── 이미지 + 제목 ────────────────────────────────────────────────────
    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.markdown("""
        <div style="width:100%;height:180px;border-radius:14px;
             background:linear-gradient(135deg,#EEF4FF,#DBEAFE);
             display:flex;align-items:center;justify-content:center;
             font-size:3rem;margin-bottom:1rem;">🛍️</div>
        """, unsafe_allow_html=True)

    st.markdown(f"### {label}")
    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════
    # SUB: main — 두 버튼
    # ══════════════════════════════════════════════════════════════════════
    if sub == "main":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🛒 구메팟 생성", use_container_width=True, key="go_create"):
                if not is_logged_in:
                    st.warning("로그인이 필요합니다.")
                else:
                    st.session_state.pot_sub = "create"
                    st.rerun()
        with c2:
            if st.button("🔍 구메팟 찾기", use_container_width=True, key="go_find"):
                st.session_state.pot_sub = "find"
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # SUB: create — 팟 생성 폼
    # ══════════════════════════════════════════════════════════════════════
    elif sub == "create":
        st.markdown("#### 🛒 구메팟 생성")

        with st.form("create_pot_form"):
            total_people = st.number_input("몇 명이서 나눠 살까요?", min_value=2, max_value=20, value=2, step=1)
            buy_date     = st.date_input("언제 구매할까요?")
            price_total  = st.number_input("총 가격 (원)", min_value=0, step=1000, value=10000)

            st.markdown("**📍 수령 장소** — 지도를 클릭해 선택하세요")
            submitted = st.form_submit_button("팟 생성하기", use_container_width=True)

        # 지도 (폼 바깥 — components.html은 form 안에 못 넣음)
        st.markdown("**지도에서 수령 위치 클릭 →**")
        components.html(_map_picker_html(), height=320, scrolling=False)

        # postMessage로 받은 좌표 저장용 JS
        st.markdown("""
        <script>
        window.addEventListener('message', function(e){
            if(e.data && e.data.type === 'MAP_PICK'){
                window._mapLat  = e.data.lat;
                window._mapLng  = e.data.lng;
                window._mapName = e.data.name;
                var el = window.parent.document.getElementById('map_result');
                if(el) el.innerText = '선택: ' + e.data.name;
            }
        });
        </script>
        <p id="map_result" style="font-size:0.8rem;color:#3B82F6;margin-top:4px;">
            (아직 위치 미선택)
        </p>
        """, unsafe_allow_html=True)

        # 좌표는 session_state로 관리 (지도 클릭 → 별도 텍스트 입력으로 fallback)
        st.caption("지도 클릭이 안 될 경우 아래에 직접 입력하세요.")
        loc_name = st.text_input("수령 장소 이름", key="loc_name_input", placeholder="예: 서울시 강남구 역삼동")
        loc_lat  = st.number_input("위도", value=37.5665, format="%.4f", key="loc_lat_input")
        loc_lng  = st.number_input("경도", value=126.9780, format="%.4f", key="loc_lng_input")

        if submitted:
            if not loc_name.strip():
                st.warning("수령 장소를 입력해 주세요.")
            else:
                pot_id = create_pot(
                    item_label   = label,
                    item_image   = image_url,
                    creator_id   = user["user_id"],
                    creator_name = user["name"],
                    total_people = int(total_people),
                    buy_date     = str(buy_date),
                    location_name= loc_name,
                    location_lat = float(loc_lat),
                    location_lng = float(loc_lng),
                    price_total  = int(price_total),
                )
                st.success(f"✅ 팟이 생성됐습니다! (팟 ID: {pot_id})")
                st.session_state.pot_sub = "find"
                st.rerun()

        if st.button("← 뒤로", key="back_create"):
            st.session_state.pot_sub = "main"; st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # SUB: find — 팟 목록
    # ══════════════════════════════════════════════════════════════════════
    elif sub == "find":
        st.markdown("#### 🔍 구메팟 찾기")
        pots = get_pots_for_item(label)

        if not pots:
            st.info("아직 생성된 팟이 없습니다. 첫 번째로 팟을 만들어 보세요!")
        else:
            for pot in pots:
                pot_id      = pot["pot_id"]
                members_cnt = len(pot["members"])
                total       = pot["total_people"]
                dday        = calc_dday(pot["buy_date"])
                ppp         = price_per_person(pot)
                is_full     = members_cnt >= total
                already_in  = is_logged_in and user.get("user_id") in pot.get("members", [])

                with st.container():
                    st.markdown(f"""
                    <div class="pot-card">
                      <div class="pot-card-row">
                        <span class="pot-creator">👤 {pot['creator_name']}</span>
                        <span class="{'pot-full' if is_full else 'pot-dday'}">{
                            '마감' if is_full else dday
                        }</span>
                      </div>
                      <div class="pot-card-row">
                        <span class="pot-meta">👥 {members_cnt}/{total}명 모집 중</span>
                        <span class="pot-price">인당 {ppp:,}원</span>
                      </div>
                      <div class="pot-meta">📍 {pot['location_name']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if already_in:
                        st.success("✅ 참여 중인 팟", icon=None)
                    elif is_full:
                        st.button("마감됨", key=f"full_{pot_id}", disabled=True, use_container_width=True)
                    elif not is_logged_in:
                        st.warning("참여하려면 로그인이 필요합니다.")
                    else:
                        if st.button("참여하기", key=f"join_{pot_id}", use_container_width=True):
                            ok, msg = join_pot(pot_id, user["user_id"])
                            if ok:
                                st.success("팟에 참여했습니다! 마이페이지에서 확인하세요.")
                                st.rerun()
                            else:
                                st.error(msg)

        if st.button("← 뒤로", key="back_find"):
            st.session_state.pot_sub = "main"; st.rerun()
