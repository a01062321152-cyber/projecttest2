"""
pot_page.py  —  구메팟 팝업 UI

"""

import streamlit as st
import streamlit.components.v1 as components
from pot_store  import (create_pot, get_pots_for_item, get_pot,
                         join_pot, end_pot, disband_pot, mark_rated,
                         calc_dday, price_per_person)
from rating_store       import add_score, get_temperature, temp_color, temp_label
from notification_store import push, push_all

POT_CSS = """
<style>
.pot-img-placeholder {
    width:100%;height:160px;border-radius:14px;
    background:linear-gradient(135deg,#EEF4FF,#DBEAFE);
    display:flex;align-items:center;justify-content:center;
    font-size:3rem;margin-bottom:1rem;
}
.pot-card {
    border:1.5px solid #E5E7EB;border-radius:14px;
    padding:1rem 1.2rem;margin-bottom:0.8rem;background:#FAFAFA;
}
.pot-card.ended  { background:#F0FFF4; border-color:#86EFAC; }
.pot-card.disbanded { background:#FFF7ED; border-color:#FCA5A5; opacity:.7; }
.pot-row { display:flex;justify-content:space-between;align-items:center;margin-bottom:.25rem; }
.pot-creator { font-weight:700;color:#1a1a1a;font-size:.95rem; }
.pot-meta    { font-size:.8rem;color:#6B7280; }
.pot-price   { font-weight:700;color:#3B82F6;font-size:1rem; }
.pot-dday    { font-size:.72rem;font-weight:700;color:#EF4444;
               background:#FEE2E2;padding:.15rem .55rem;border-radius:20px; }
.pot-full-b  { font-size:.72rem;color:#9CA3AF;
               background:#F3F4F6;padding:.15rem .55rem;border-radius:20px; }
.pot-ended-b { font-size:.72rem;color:#16A34A;
               background:#DCFCE7;padding:.15rem .55rem;border-radius:20px; }
.item-price-badge {
    display:inline-block;background:#EFF6FF;color:#3B82F6;
    font-size:.82rem;font-weight:700;padding:.25rem .8rem;
    border-radius:20px;margin-bottom:1rem;
}
</style>
"""


def _map_pick_html(lat=37.5665, lng=126.9780) -> str:
    """클릭으로 위치 선택하는 지도"""
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{{margin:0;padding:0;width:100%;height:300px;}}
#info{{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
       background:rgba(0,0,0,.65);color:#fff;font-size:.75rem;
       padding:4px 14px;border-radius:20px;z-index:999;white-space:nowrap;}}</style>
</head><body>
<div id="map"></div><div id="info">지도를 클릭해 위치를 선택하세요</div>
<script>
  var map=L.map('map').setView([{lat},{lng}],13);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
    {{attribution:'© OpenStreetMap'}}).addTo(map);
  var mk=null;
  map.on('click',function(e){{
    var la=e.latlng.lat.toFixed(5),lo=e.latlng.lng.toFixed(5);
    if(mk) map.removeLayer(mk);
    mk=L.marker([la,lo]).addTo(map);
    document.getElementById('info').innerText='📍 '+la+', '+lo;
    window.parent.postMessage({{type:'MAP_PICK',lat:parseFloat(la),lng:parseFloat(lo)}},'*');
  }});
</script></body></html>"""


def _map_view_html(lat, lng, name) -> str:
    """팟 상세에서 위치를 표시만 하는 지도"""
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{{margin:0;padding:0;width:100%;height:260px;}}</style>
</head><body>
<div id="map"></div>
<script>
  var map=L.map('map').setView([{lat},{lng}],15);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
    {{attribution:'© OpenStreetMap'}}).addTo(map);
  L.marker([{lat},{lng}]).addTo(map).bindPopup('{name}').openPopup();
</script></body></html>"""


# ── 팟 상세 팝업 ─────────────────────────────────────────────────────────────

def render_pot_detail(pot_id: str):
    """내 팟 클릭 → 상세 (지도 + 연락처 + 종료/해산 + 평가)"""
    pot = get_pot(pot_id)
    if pot is None:
        st.error("팟 정보를 불러올 수 없습니다.")
        if st.button("← 닫기", key="detail_close_err"):
            st.session_state.pop("viewing_pot_id", None); st.rerun()
        return

    st.markdown(POT_CSS, unsafe_allow_html=True)

    user     = st.session_state.get("user", {})
    uid      = user.get("user_id", "")
    is_creator = uid == pot["creator_id"]
    status   = pot.get("status", "active")

    if st.button("← 닫기", key="detail_close"):
        st.session_state.pop("viewing_pot_id", None); st.rerun()

    # 이미지
    if pot.get("item_image"):
        st.image(pot["item_image"], use_container_width=True)
    else:
        st.markdown('<div class="pot-img-placeholder">🛍️</div>', unsafe_allow_html=True)

    dday = calc_dday(pot["buy_date"])
    ppp  = price_per_person(pot)
    st.markdown(f"### {pot['item_label']}")
    st.markdown(f"""
    | 항목 | 내용 |
    |------|------|
    | 팟장 | {pot['creator_name']} |
    | 인원 | {len(pot['members'])}/{pot['total_people']}명 |
    | 날짜 | {pot['buy_date']} ({dday}) |
    | 인당 | {ppp:,}원 |
    | 상태 | {'✅ 종료됨' if status=='ended' else '🔴 해산됨' if status=='disbanded' else '🟢 진행 중'} |
    """)

    # 연락처
    contact = pot.get("contact", "")
    if contact:
        st.info(f"📞 대표 연락처: **{contact}**")

    # 수령 위치 지도
    st.markdown("**📍 수령 위치**")
    st.caption(pot["location_name"])
    components.html(
        _map_view_html(pot["location_lat"], pot["location_lng"], pot["location_name"]),
        height=280, scrolling=False,
    )

    st.markdown("---")

    # ── 종료 / 해산 버튼 (팟장 + active 상태만) ──────────────────────────
    if is_creator and status == "active":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ 팟 종료", key=f"end_{pot_id}", use_container_width=True):
                end_pot(pot_id)
                push_all(pot["members"], "pot_ended",
                         f"'{pot['item_label']}' 팟이 종료됐습니다. 참여자를 평가해 주세요.")
                st.success("팟이 종료됐습니다. 평가를 진행해 주세요.")
                st.rerun()
        with c2:
            if st.button("💔 팟 해산", key=f"disband_{pot_id}", use_container_width=True):
                disband_pot(pot_id)
                push_all(pot["members"], "pot_disbanded",
                         f"'{pot['item_label']}' 팟이 해산됐습니다.")
                st.warning("팟이 해산됐습니다.")
                st.rerun()

    # ── 평가 (ended 상태 + 아직 평가 안 한 멤버) ─────────────────────────
    if status == "ended" and uid in pot.get("members", []) and uid not in pot.get("rated_by", []):
        st.markdown("#### ⭐ 참여자 평가 (10점 만점)")
        others = [m for m in pot["members"] if m != uid]
        if not others:
            st.info("평가할 다른 참여자가 없습니다.")
            mark_rated(pot_id, uid)
        else:
            scores = {}
            with st.form(f"rate_form_{pot_id}"):
                for member_id in others:
                    scores[member_id] = st.slider(
                        f"@{member_id}", 1, 10, 7, key=f"score_{pot_id}_{member_id}")
                submitted = st.form_submit_button("평가 제출", use_container_width=True)

            if submitted:
                for member_id, score in scores.items():
                    add_score(member_id, score)
                    push(member_id, "pot_ended",
                         f"'{pot['item_label']}' 팟 평가가 완료됐습니다. 매너 온도를 확인하세요!")
                mark_rated(pot_id, uid)
                st.success("평가가 제출됐습니다!")
                st.rerun()

    elif status == "ended" and uid in pot.get("rated_by", []):
        st.success("✅ 평가를 완료했습니다.")


# ── 메인 팝업 (카드 클릭) ────────────────────────────────────────────────────

def render_item_popup(item: dict):
    st.markdown(POT_CSS, unsafe_allow_html=True)

    label      = item.get("label", "")
    image_url  = item.get("image_url", "")
    item_price = int(item.get("price", 0))
    is_logged_in = "user" in st.session_state
    user         = st.session_state.get("user", {})
    is_admin     = user.get("is_admin", False)

    if "pot_sub" not in st.session_state:
        st.session_state.pot_sub = "main"
    sub = st.session_state.pot_sub

    # 닫기
    if st.button("✕  닫기", key="pot_close"):
        st.session_state.pot_modal_item = None
        st.session_state.pot_sub = "main"
        st.rerun()

    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.markdown('<div class="pot-img-placeholder">🛍️</div>', unsafe_allow_html=True)

    st.markdown(f"### {label}")
    if item_price > 0:
        st.markdown(f'<div class="item-price-badge">💰 정가 {item_price:,}원</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── MAIN ──────────────────────────────────────────────────────────────
    if sub == "main":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🛒 구메팟 생성", use_container_width=True, key="go_create"):
                if not is_logged_in:   st.warning("로그인이 필요합니다.")
                elif is_admin:         st.warning("관리자는 팟을 생성할 수 없습니다.")
                else:
                    st.session_state.pot_sub = "create"; st.rerun()
        with c2:
            if st.button("🔍 구메팟 찾기", use_container_width=True, key="go_find"):
                st.session_state.pot_sub = "find"; st.rerun()

    # ── CREATE ────────────────────────────────────────────────────────────
    elif sub == "create":
        st.markdown("#### 🛒 구메팟 생성")

        if item_price > 0:
            st.info(f"정가 **{item_price:,}원** 기준으로 인당 가격이 자동 계산됩니다.")
            price_total = item_price
        else:
            price_total = st.number_input("총 가격 (원)", min_value=0, step=1000, value=10000, key="price_input")

        total_people = st.number_input("몇 명이서 나눌까요?", min_value=2, max_value=20, value=2, step=1, key="people_input")
        ppp = int(price_total) // max(int(total_people), 1)
        st.markdown(f"**👉 인당 가격: {ppp:,}원**")

        buy_date = st.date_input("구매 날짜", key="date_input")
        contact  = st.text_input("📞 대표 연락처", placeholder="카카오톡 ID, 전화번호 등", key="contact_input")

        st.markdown("**📍 수령 장소**")
        loc_name = st.text_input("장소 이름", placeholder="예: 강남역 2번 출구 앞", key="loc_name")
        col_lat, col_lng = st.columns(2)
        with col_lat:
            loc_lat = st.number_input("위도",  value=37.5665, format="%.5f", key="loc_lat")
        with col_lng:
            loc_lng = st.number_input("경도", value=126.9780, format="%.5f", key="loc_lng")

        st.caption("지도를 클릭하면 아래에 좌표가 표시됩니다. 입력칸에 직접 복사해 주세요.")
        components.html(_map_pick_html(), height=320, scrolling=False)
        st.markdown("""
        <script>
        window.addEventListener('message',function(e){
          if(e.data&&e.data.type==='MAP_PICK'){
            var el=document.getElementById('map_coord_display');
            if(el) el.innerText='📍 위도: '+e.data.lat+' / 경도: '+e.data.lng;
          }
        });
        </script>
        <pre id="map_coord_display"
          style="font-size:.78rem;color:#3B82F6;background:#EFF6FF;
                 padding:6px 10px;border-radius:8px;margin-top:4px;">
(지도 클릭 후 좌표 확인)</pre>
        """, unsafe_allow_html=True)

        st.markdown("")
        if st.button("✅ 팟 생성하기", use_container_width=True, key="submit_create"):
            if not loc_name.strip():
                st.warning("장소 이름을 입력해 주세요.")
            else:
                pot_id = create_pot(
                    item_label=label, item_image=image_url,
                    creator_id=user["user_id"], creator_name=user["name"],
                    total_people=int(total_people), buy_date=str(buy_date),
                    location_name=loc_name, location_lat=float(loc_lat),
                    location_lng=float(loc_lng), price_total=int(price_total),
                    contact=contact,
                )
                push(user["user_id"], "pot_joined",
                     f"'{label}' 구메팟을 생성하고 자동 참여됐습니다.")
                st.success(f"팟 생성 완료! (ID: {pot_id})")
                st.session_state.pot_sub = "find"; st.rerun()

        if st.button("← 뒤로", key="back_create"):
            st.session_state.pot_sub = "main"; st.rerun()

    # ── FIND ──────────────────────────────────────────────────────────────
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
                    <span class="{'pot-full-b' if is_full else 'pot-dday'}">
                        {'마감' if is_full else dday}</span>
                  </div>
                  <div class="pot-row">
                    <span class="pot-meta">👥 {members_cnt}/{total}명</span>
                    <span class="pot-price">인당 {ppp:,}원</span>
                  </div>
                  <div class="pot-meta">📍 {pot['location_name']} | 📅 {pot['buy_date']}</div>
                </div>
                """, unsafe_allow_html=True)

                if already_in:
                    st.success("✅ 이미 참여 중")
                elif is_full:
                    st.button("마감됨", key=f"full_{pot_id}", disabled=True, use_container_width=True)
                elif not is_logged_in:
                    st.caption("참여하려면 로그인이 필요합니다.")
                elif is_admin:
                    st.caption("관리자는 팟에 참여할 수 없습니다.")
                else:
                    if st.button("참여하기", key=f"join_{pot_id}", use_container_width=True):
                        ok, msg = join_pot(pot_id, user["user_id"])
                        if ok:
                            push(user["user_id"], "pot_joined",
                                 f"'{label}' 구메팟에 참여했습니다.")
                            push(pot["creator_id"], "pot_joined",
                                 f"{user['name']}님이 '{label}' 팟에 참여했습니다.")
                            st.success("팟에 참여했습니다!")
                            st.rerun()
                        else:
                            st.error(msg)

        if st.button("← 뒤로", key="back_find"):
            st.session_state.pot_sub = "main"; st.rerun()
