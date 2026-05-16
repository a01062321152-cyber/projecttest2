"""essentials_page.py — 생필품 정기구메 파티 UI"""

import streamlit as st
import streamlit.components.v1 as components
from essentials_store import (create_party, get_open_parties, get_party,
                               apply_party, cancel_apply, close_party, delete_party)
from notification_store import push, push_all

CSS = """
<style>
.ess-party-card{border:1.5px solid #E5E7EB;border-radius:14px;
  padding:.9rem 1.1rem;margin-bottom:.8rem;background:#F9FAFB;}
.ess-party-card:hover{border-color:#3B82F6;}
.ess-badge{display:inline-block;font-size:.7rem;font-weight:700;
  padding:.15rem .55rem;border-radius:20px;margin-left:.4rem;}
.ess-open{background:#DCFCE7;color:#16A34A;}
.ess-closed{background:#FEE2E2;color:#DC2626;}
.ess-applicant-row{display:flex;justify-content:space-between;
  padding:.45rem .6rem;border-radius:8px;background:#F3F4F6;margin-bottom:.35rem;
  font-size:.82rem;}
</style>
"""


def _map_view(lat, lng, name):
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{{margin:0;padding:0;width:100%;height:220px;}}</style>
</head><body><div id="map"></div>
<script>
var m=L.map('map').setView([{lat},{lng}],15);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{attribution:'© OpenStreetMap'}}).addTo(m);
L.marker([{lat},{lng}]).addTo(m).bindPopup('{name}').openPopup();
</script></body></html>"""


def render_essentials_popup(item: dict):
    """생필품 아이템 클릭 시 팝업"""
    st.markdown(CSS, unsafe_allow_html=True)

    label     = item.get("label", "")
    image_url = item.get("image_url", "")
    user      = st.session_state.get("user", {})
    uid       = user.get("user_id", "")
    is_admin  = user.get("is_admin", False)
    is_logged = "user" in st.session_state

    if "ess_sub" not in st.session_state:
        st.session_state.ess_sub = "main"
    if "ess_party_id" not in st.session_state:
        st.session_state.ess_party_id = None

    sub = st.session_state.ess_sub

    # 닫기
    if st.button("✕ 닫기", key="ess_close"):
        st.session_state.modal_item   = None
        st.session_state.modal_type   = None
        st.session_state.ess_sub      = "main"
        st.session_state.ess_party_id = None
        st.rerun()

    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.markdown('<div style="width:100%;height:140px;border-radius:12px;'
                    'background:linear-gradient(135deg,#EEF4FF,#DBEAFE);'
                    'display:flex;align-items:center;justify-content:center;'
                    'font-size:3rem;margin-bottom:.8rem;">🧴</div>',
                    unsafe_allow_html=True)

    st.markdown(f"### {label}")
    st.markdown("---")

    # ── MAIN: 파티 목록 ───────────────────────────────────────────────────
    if sub == "main":
        parties = get_open_parties(label)

        if is_admin:
            if st.button("➕ 파티 생성", key="ess_create_btn", use_container_width=True):
                pid = create_party(label, image_url, uid)
                st.success(f"파티가 생성됐습니다! (ID: {pid})")
                st.rerun()

        if not parties:
            st.info("현재 모집 중인 파티가 없습니다.")
        else:
            st.markdown("**📋 모집 중인 파티**")
            for p in parties:
                cnt = len(p["applicants"])
                st.markdown(f"""
                <div class="ess-party-card">
                  <b>파티 #{p['party_id'][:6]}</b>
                  <span class="ess-badge ess-open">모집중</span><br>
                  <span style="font-size:.8rem;color:#6B7280;">
                    신청자 {cnt}명 | 생성: {p['created_at'][:10]}
                  </span>
                </div>""", unsafe_allow_html=True)

                already = any(a["user_id"] == uid for a in p["applicants"])

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📝 신청하기", key=f"ess_apply_{p['party_id']}",
                                 use_container_width=True, disabled=already or not is_logged):
                        st.session_state.ess_sub      = "apply"
                        st.session_state.ess_party_id = p["party_id"]
                        st.rerun()
                with c2:
                    if is_admin:
                        if st.button("🔍 상세보기", key=f"ess_detail_{p['party_id']}",
                                     use_container_width=True):
                            st.session_state.ess_sub      = "admin_detail"
                            st.session_state.ess_party_id = p["party_id"]
                            st.rerun()

                if already:
                    st.success("✅ 신청 완료")
                    if st.button("신청 취소", key=f"ess_cancel_{p['party_id']}"):
                        cancel_apply(p["party_id"], uid)
                        st.rerun()

    # ── APPLY: 신청 폼 ────────────────────────────────────────────────────
    elif sub == "apply":
        st.markdown("#### 📝 파티 신청")
        with st.form("ess_apply_form"):
            contact = st.text_input("연락처", placeholder="카카오톡 ID / 전화번호")
            qty     = st.number_input("필요 개수", min_value=1, max_value=99, value=1, step=1)
            ok      = st.form_submit_button("신청 완료", use_container_width=True)

        if ok:
            ok2, msg = apply_party(
                st.session_state.ess_party_id, uid,
                user.get("name",""), contact, int(qty))
            if ok2:
                push(uid, "pot_joined", f"'{label}' 생필품 파티에 신청됐습니다.")
                st.success("신청 완료!")
                st.session_state.ess_sub = "main"; st.rerun()
            else:
                st.error(msg)

        if st.button("← 뒤로", key="ess_back_apply"):
            st.session_state.ess_sub = "main"; st.rerun()

    # ── ADMIN DETAIL: 신청자 목록 + 마감 ─────────────────────────────────
    elif sub == "admin_detail":
        p = get_party(st.session_state.ess_party_id)
        if not p:
            st.error("파티를 찾을 수 없습니다.")
            st.session_state.ess_sub = "main"; st.rerun()
            return

        st.markdown(f"#### 🔍 파티 상세 — #{p['party_id'][:6]}")
        applicants = p["applicants"]
        total_qty  = sum(a["qty"] for a in applicants)

        st.markdown(f"**총 신청자: {len(applicants)}명 / 총 수량: {total_qty}개**")

        for a in applicants:
            st.markdown(f"""
            <div class="ess-applicant-row">
              <span>👤 {a['name']} (@{a['user_id']})</span>
              <span>📞 {a['contact']}</span>
              <span><b>{a['qty']}개</b></span>
            </div>""", unsafe_allow_html=True)

        if p["status"] == "open":
            st.divider()
            st.markdown("**💰 파티 마감**")
            with st.form("ess_close_form"):
                price_per = st.number_input("개당 가격 (원)", min_value=0, step=100, value=1000)
                pay_dest  = st.text_input("송금처 (계좌번호 / 카카오페이 등)")
                close_ok  = st.form_submit_button("마감 처리", use_container_width=True)

            if close_ok:
                closed = close_party(p["party_id"], int(price_per), pay_dest)
                if closed:
                    for a in applicants:
                        amount = a["qty"] * int(price_per)
                        push(a["user_id"], "pot_ended",
                             f"'{label}' 생필품 파티가 마감됐습니다. "
                             f"총 {amount:,}원을 [{pay_dest}]로 보내주세요! "
                             f"({a['qty']}개 × {int(price_per):,}원)")
                    st.success("마감 처리 및 알림 발송 완료!")
                    st.rerun()
        else:
            st.info(f"✅ 마감됨 | 개당 {p['price_per_unit']:,}원 | 송금처: {p['payment_dest']}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← 뒤로", key="ess_back_detail"):
                st.session_state.ess_sub = "main"; st.rerun()
        with c2:
            if is_admin:
                if st.button("🗑️ 파티 삭제", key="ess_del_party"):
                    delete_party(p["party_id"])
                    st.session_state.ess_sub = "main"; st.rerun()
