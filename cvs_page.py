"""cvs_page.py — 편의점 상품 클릭 → 파티 신청 UI"""

import re
import streamlit as st
from cvs_store import (get_waiting_parties, get_party, apply_order,
                        confirm_order, depart_party)
from notification_store import push


CSS = """
<style>
.cvs-party-card{border:1.5px solid #E5E7EB;border-radius:14px;
  padding:.9rem 1.1rem;margin-bottom:.8rem;background:#F9FAFB;cursor:pointer;}
.cvs-party-card:hover{border-color:#3B82F6;background:#EFF6FF;}
.cvs-time-badge{display:inline-block;font-size:.75rem;font-weight:700;
  color:#fff;background:#3B82F6;padding:.2rem .6rem;border-radius:20px;margin-right:.4rem;}
.cvs-order-row{display:flex;justify-content:space-between;align-items:center;
  padding:.45rem .6rem;border-radius:8px;background:#F3F4F6;margin-bottom:.35rem;
  font-size:.82rem;}
.cvs-paid{color:#16A34A;font-weight:700;}
.cvs-unpaid{color:#DC2626;}
</style>
"""

def _validate_account(v: str) -> str | None:
    v = v.strip()
    if not v:                              return "계좌번호를 입력해 주세요."
    if len(v) < 5:                         return "계좌번호가 너무 짧습니다."
    if re.fullmatch(r'[가-힣\s]{1,5}', v): return "올바른 계좌번호 또는 송금 수단을 입력해 주세요."
    return None

def _validate_time(v: str) -> str | None:
    v = v.strip()
    if not v: return "출발 시간을 입력해 주세요."
    if not re.fullmatch(r'([01]?\d|2[0-3]):([0-5]\d)', v):
        return "올바른 시간 형식을 입력해 주세요. (예: 18:30)"
    return None


def render_cvs_popup(item: dict):
    st.markdown(CSS, unsafe_allow_html=True)

    label     = item.get("label", "")
    image_url = item.get("image_url", "")
    price     = int(item.get("price", 0))
    user      = st.session_state.get("user", {})
    uid       = user.get("user_id", "")
    is_logged = "user" in st.session_state

    if "cvs_sub" not in st.session_state:
        st.session_state.cvs_sub      = "list"
        st.session_state.cvs_party_id = None
    sub = st.session_state.cvs_sub

    if st.button("✕ 닫기", key="cvs_close"):
        st.session_state.modal_item   = None
        st.session_state.modal_type   = None
        st.session_state.cvs_sub      = "list"
        st.session_state.cvs_party_id = None
        st.rerun()

    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.markdown('<div style="width:100%;height:140px;border-radius:12px;'
                    'background:linear-gradient(135deg,#EEF4FF,#DBEAFE);'
                    'display:flex;align-items:center;justify-content:center;'
                    'font-size:3rem;margin-bottom:.8rem;">🏪</div>',
                    unsafe_allow_html=True)

    st.markdown(f"### {label}")
    if price:
        st.markdown(f"💰 **{price:,}원**")
    st.markdown("---")

    # ── LIST ─────────────────────────────────────────────────────────────
    if sub == "list":
        parties = get_waiting_parties()
        if not parties:
            st.info("현재 출발 대기 중인 편의점 파티가 없습니다.")
            if st.button("➕ 파티 만들러 가기", use_container_width=True, key="cvs_go_create"):
                st.session_state.modal_item = None
                st.session_state.modal_type = None
                st.session_state.page = "wishlist"
                st.rerun()
        else:
            st.markdown("**🏪 출발 대기 중인 파티 (빠른 출발 순)**")
            for p in parties:
                confirmed_cnt = sum(1 for o in p["orders"] if o["confirmed"])
                already = any(o["user_id"] == uid for o in p["orders"])

                st.markdown(f"""
                <div class="cvs-party-card">
                  <span class="cvs-time-badge">🕐 {p['depart_time']}</span>
                  <b>{p['creator_name']}</b>의 파티<br>
                  <span style="font-size:.8rem;color:#6B7280;">
                    📦 주문 {len(p['orders'])}건 (확정 {confirmed_cnt}건) |
                    📞 {p['contact']}
                  </span>
                </div>""", unsafe_allow_html=True)

                if already:
                    st.success("✅ 이미 신청함")
                    st.caption(f"💳 계좌: {p['account']}")
                elif not is_logged:
                    st.caption("신청하려면 로그인하세요.")
                else:
                    if st.button("이 파티에 신청",
                                 key=f"cvs_join_{p['party_id']}",
                                 use_container_width=True):
                        st.session_state.cvs_sub      = "apply"
                        st.session_state.cvs_party_id = p["party_id"]
                        st.rerun()

    # ── APPLY ─────────────────────────────────────────────────────────────
    elif sub == "apply":
        p = get_party(st.session_state.cvs_party_id)
        if not p:
            st.error("파티를 찾을 수 없습니다.")
            st.session_state.cvs_sub = "list"; st.rerun()
            return

        st.markdown(f"#### 📝 신청 — {p['creator_name']}의 파티")
        st.info(f"💳 입금 계좌: **{p['account']}**\n\n"
                f"신청 후 위 계좌로 입금하면 파티장이 확인 후 합류 처리해 줍니다.")

        qty = st.number_input("수량", min_value=1, max_value=20, value=1, step=1,
                               key="cvs_qty")
        total = qty * price
        st.markdown(f"**예상 금액: {total:,}원** ({qty}개 × {price:,}원)")

        if st.button("신청하기", use_container_width=True, key="cvs_apply_submit"):
            ok, msg = apply_order(
                p["party_id"], uid, user.get("name", ""),
                label, image_url, int(qty), price)
            if ok:
                push(p["creator_id"], "pot_joined",
                     f"{user.get('name','')}님이 '{label}' {qty}개를 신청했습니다. "
                     f"입금 확인 후 합류 처리해 주세요.")
                push(uid, "pot_joined",
                     f"'{label}' 편의점 파티에 신청 완료! "
                     f"{total:,}원을 [{p['account']}]로 입금해 주세요.")
                st.success("신청 완료! 알림을 확인하세요.")
                st.session_state.cvs_sub = "list"; st.rerun()
            else:
                st.error(msg)

        if st.button("← 뒤로", key="cvs_back_apply"):
            st.session_state.cvs_sub = "list"; st.rerun()
