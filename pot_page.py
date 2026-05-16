"""
pot_page.py  —  구메팟 팝업 UI (생성 / 찾기 / 참여)
"""

import streamlit as st
import streamlit.components.v1 as components
from pot_store import (
    create_pot, get_pots_for_item, join_pot,
    calc_dday, price_per_person,
)

POT_CSS = """
<style>
.pot-item-img {
    width:100%; height:200px; object-fit:cover;
    border-radius:14px; margin-bottom:1.2rem;
}
.pot-img-placeholder {
    width:100%; height:180px; border-radius:14px;
    background:linear-gradient(135deg,#EEF4FF,#DBEAFE);
    display:flex; align-items:center; justify-content:center;
    font-size:3.5rem; margin-bottom:1rem;
}
.pot-card {
    border:1.5px solid #E5E7EB; border-radius:14px;
    padding:1rem 1.2rem; margin-bottom:0.8rem; background:#FAFAFA;
}
.pot-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem; }
.pot-creator { font-weight:700; color:#1a1a1a; font-size:0.95rem; }
.pot-meta    { font-size:0.8rem; color:#6B7280; }
.pot-price   { font-weight:700; color:#3B82F6; font-size:1rem; }
.pot-dday    { font-size:0.72rem; font-weight:700; color:#EF4444;
               background:#FEE2E2; padding:0.15rem 0.55rem; border-radius:20px; }
.pot-full-badge { font-size:0.72rem; color:#9CA3AF;
               background:#F3F4F6; padding:0.15rem 0.55rem; border-radius:20px; }
.item-price-badge {
    display:inline-block; background:#EFF6FF; color:#3B82F6;
    font-size:0.82rem; font-weight:700; padding:0.25rem 0.8rem;
    border-radius:20px; margin-bottom:1rem;
}
</style>
"""


def _map_html(lat: float = 37.5665, lng: float = 126.9780) -> str:
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body,#map{{margin:0;padding:0;width:100%;height:320px;}}
  #info{{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
         background:rgba(0,0,0,0.65);color:#fff;font-size:0.75rem;
         padding:4px 14px;border-radius:20px;z-index:999;white-space:nowrap;}}
</style></head><body>
<div id="map"></div>
<div id="info">지도를 클릭해 위치를 선택하세요</div>
<script>
  var map = L.map('map').setView([{lat},{lng}],13);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
    {{attribution:'© OpenStreetMap'}}).addTo(map);
  var marker=null;
  map.on('click',function(e){{
    var la=e.latlng.lat.toFixed(5), lo=e.latlng.lng.toFixed(5);
    if(marker) map.removeLayer(marker);
    marker=L.marker([la,lo]).addTo(map);
    document.getElementById('info').innerText='📍 위도 '+la+', 경도 '+lo;
    window.parent.postMessage({{type:'MAP_PICK',lat:parseFloat(la),lng:parseFloat(lo)}}, '*');
  }});
</script></body></html>"""


def render_item_popup(item: dict):
    """카드 클릭 시 호출되는 팝업 전체 UI"""
    st.markdown(POT_CSS, unsafe_allow_html=True)

    label     = item.get("label", "")
    image_url = item.get("image_url", "")
    item_price = int(item.get("price", 0))          # ← 항목 가격

    is_logged_in = "user" in st.session_state
    user = st.session_state.get("user", {})

    if "pot_sub" not in st.session_state:
        st.session_state.pot_sub = "main"
    sub = st.session_state.pot_sub

    # ── 닫기 ──────────────────────────────────────────────────────────────
    if st.button("✕  닫기", key="pot_close"):
        st.session_state.pot_modal_item = None
        st.session_state.pot_sub = "main"
        st.rerun()

    # ── 이미지 ────────────────────────────────────────────────────────────
    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.markdown('<div class="pot-img-placeholder">🛍️</div>', unsafe_allow_html=True)

    st.markdown(f"### {label}")
    if item_price > 0:
        st.markdown(f'<div class="item-price-badge">💰 정가 {item_price:,}원</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════
    # MAIN — 두 버튼
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
    # CREATE — 팟 생성 폼
    # ══════════════════════════════════════════════════════════════════════
    elif sub == "create":
        st.markdown("#### 🛒 구메팟 생성")

        # 가격 자동 입력 (항목 price 기반)
        if item_price > 0:
            st.info(f"정가 **{item_price:,}원** 기준으로 인당 가격이 자동 계산됩니다.")
            price_total = item_price
        else:
            st.caption("항목에 가격이 설정되지 않아 직접 입력합니다.")
            price_total = st.number_input("총 가격 (원)", min_value=0, step=1000, value=10000, key="price_input")

        total_people = st.number_input("몇 명이서 나눌까요?", min_value=2, max_value=20, value=2, step=1, key="people_input")

        # 인당 가격 실시간 표시
        ppp = int(price_total) // max(int(total_people), 1)
        st.markdown(f"**👉 인당 가격: {ppp:,}원**")

        buy_date = st.date_input("구매 날짜", key="date_input")

        st.markdown("**📍 수령 장소**")
        loc_name = st.text_input("장소 이름", placeholder="예: 강남역 2번 출구 앞", key="loc_name")
        loc_lat  = st.number_input("위도",  value=37.5665, format="%.5f", key="loc_lat")
        loc_lng  = st.number_input("경도", value=126.9780, format="%.5f", key="loc_lng")

        st.caption("지도에서 클릭하면 위도/경도가 자동 입력됩니다.")
        components.html(_map_html(), height=340, scrolling=False)

        # 지도 postMessage → 위도·경도 세션에 저장
        map_js = """
        <script>
        window.addEventListener('message', function(e){
            if(e.data && e.data.type==='MAP_PICK'){
                // Streamlit number_input은 직접 못 바꾸므로 안내만 표시
                var el = document.getElementById('map_coords');
                if(el) el.innerText = '📍 클릭 위치 — 위도: '+e.data.lat+', 경도: '+e.data.lng
                    +'\n위의 입력칸에 직접 복사해 주세요.';
            }
        });
        </script>
        <pre id="map_coords" style="font-size:0.78rem;color:#3B82F6;margin-top:6px;
             background:#EFF6FF;padding:6px 10px;border-radius:8px;">
(지도를 클릭하면 좌표가 여기 표시됩니다)</pre>
        """
        st.markdown(map_js, unsafe_allow_html=True)

        st.markdown("")
        if st.button("✅ 팟 생성하기", use_container_width=True, key="submit_create"):
            if not loc_name.strip():
                st.warning("장소 이름을 입력해 주세요.")
            else:
                pot_id = create_pot(
                    item_label    = label,
                    item_image    = image_url,
                    creator_id    = user["user_id"],
                    creator_name  = user["name"],
                    total_people  = int(total_people),
                    buy_date      = str(buy_date),
                    location_name = loc_name,
                    location_lat  = float(loc_lat),
                    location_lng  = float(loc_lng),
                    price_total   = int(price_total),
                )
                st.success(f"팟이 생성됐습니다! (ID: {pot_id})")
                st.session_state.pot_sub = "find"
                st.rerun()

        if st.button("← 뒤로", key="back_create"):
            st.session_state.pot_sub = "main"; st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # FIND — 팟 목록
    # ══════════════════════════════════════════════════════════════════════
    elif sub == "find":
        st.markdown("#### 🔍 구메팟 찾기")
        pots = get_pots_for_item(label)

        if not pots:
            st.info("아직 생성된 팟이 없어요. 첫 번째로 팟을 만들어 보세요!")
        else:
            for pot in pots:
                pot_id      = pot["pot_id"]
                members_cnt = len(pot["members"])
                total       = pot["total_people"]
                dday        = calc_dday(pot["buy_date"])
                ppp         = price_per_person(pot)
                is_full     = members_cnt >= total
                already_in  = is_logged_in and user.get("user_id") in pot.get("members", [])

                st.markdown(f"""
                <div class="pot-card">
                  <div class="pot-row">
                    <span class="pot-creator">👤 {pot['creator_name']}</span>
                    <span class="{'pot-full-badge' if is_full else 'pot-dday'}">
                        {'마감' if is_full else dday}
                    </span>
                  </div>
                  <div class="pot-row">
                    <span class="pot-meta">👥 {members_cnt}/{total}명 모집 중</span>
                    <span class="pot-price">인당 {ppp:,}원</span>
                  </div>
                  <div class="pot-meta">📍 {pot['location_name']} &nbsp;|&nbsp; 📅 {pot['buy_date']}</div>
                </div>
                """, unsafe_allow_html=True)

                if already_in:
                    st.success("✅ 이미 참여 중인 팟입니다.")
                elif is_full:
                    st.button("마감됨", key=f"full_{pot_id}", disabled=True, use_container_width=True)
                elif not is_logged_in:
                    st.caption("참여하려면 로그인이 필요합니다.")
                else:
                    if st.button(f"참여하기", key=f"join_{pot_id}", use_container_width=True):
                        ok, msg = join_pot(pot_id, user["user_id"])
                        if ok:
                            st.success("팟에 참여했습니다! 마이페이지에서 확인하세요.")
                            st.rerun()
                        else:
                            st.error(msg)

        if st.button("← 뒤로", key="back_find"):
            st.session_state.pot_sub = "main"; st.rerun()
