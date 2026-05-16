"""essentials_page.py — 생필품 정기구메 파티 UI"""

import re
import streamlit as st
import streamlit.components.v1 as components
from essentials_store import (create_party, get_open_parties, get_party,
                               apply_party, cancel_apply, close_party,
                               save_ratings, mark_credit_given, is_credit_given,
                               delete_party)
from notification_store import push
from user_store import add_credits, deduct_credits, get_credits
from rating_store import add_score

CSS = """
<style>
.ess-party-card{border:1.5px solid #BFDBFE;border-radius:14px;
  padding:.9rem 1.1rem;margin-bottom:.8rem;background:#FFFFFF;
  box-shadow:0 2px 8px rgba(37,99,235,.06);transition:all .15s;}
.ess-party-card:hover{border-color:#2563EB;background:#EFF6FF;
  box-shadow:0 4px 16px rgba(37,99,235,.12);}
.ess-badge{display:inline-block;font-size:.7rem;font-weight:700;
  padding:.15rem .55rem;border-radius:20px;margin-left:.4rem;}
.ess-open{background:#DBEAFE;color:#1D4ED8;}
.ess-closed{background:#FEF9C3;color:#B45309;}
.ess-rated{background:#EFF6FF;color:#2563EB;}
.ess-applicant-row{display:flex;justify-content:space-between;
  padding:.5rem .8rem;border-radius:10px;
  background:#EFF6FF;border:1px solid #DBEAFE;
  margin-bottom:.4rem;font-size:.82rem;color:#0F172A;}
.credit-badge{display:inline-block;background:#FEF9C3;color:#B45309;
  font-size:.72rem;font-weight:700;padding:.15rem .55rem;border-radius:20px;}
</style>
"""

BANKS = [
    "은행 선택", "국민은행", "신한은행", "우리은행", "하나은행", "농협은행",
    "기업은행", "카카오뱅크", "토스뱅크", "케이뱅크", "SC제일은행",
    "씨티은행", "대구은행", "부산은행", "광주은행", "전북은행", "경남은행",
    "제주은행", "수협은행", "우체국", "새마을금고", "신협",
]

CREDIT_PER_PURCHASE = 10  # 구매 참여당 지급 크래딧


def _validate_contact_kakao(v):
    v = v.strip()
    if not v:      return "카카오톡 ID를 입력해 주세요."
    if len(v) < 3: return "카카오톡 ID는 3자 이상이어야 합니다."
    if not re.fullmatch(r'[A-Za-z0-9_]+', v):
        return "카카오톡 ID는 영어, 숫자, 밑줄(_)만 사용할 수 있습니다."
    return None

def _validate_contact_phone(v):
    digits = re.sub(r'\D', '', v)
    if not digits: return "전화번호를 입력해 주세요."
    if not re.fullmatch(r'01[0-9]{8,9}', digits):
        return "올바른 전화번호를 입력해 주세요. (예: 01012345678)"
    return None

def _format_phone(v):
    d = re.sub(r'\D', '', v)
    return f"{d[:3]}-{d[3:7]}-{d[7:]}" if len(d) == 11 else d

def _contact_input(key_prefix):
    ctype = st.radio("연락처 유형", ["카카오톡 ID", "전화번호"],
                     horizontal=True, key=f"{key_prefix}_ctype")
    if ctype == "카카오톡 ID":
        val = st.text_input("카카오톡 ID", placeholder="예: gume_user123",
                             help="영어, 숫자, 밑줄(_)만 사용 가능합니다.",
                             key=f"{key_prefix}_cval")
        err = _validate_contact_kakao(val) if val else None
    else:
        val = st.text_input("전화번호", placeholder="예: 01012345678 (숫자만)",
                             key=f"{key_prefix}_cval")
        if val:
            err = _validate_contact_phone(val)
            if not err: val = _format_phone(val)
        else:
            err = None
    if val and err: st.error(err)
    return val.strip(), err

def _account_input(key_prefix):
    bank = st.selectbox("은행", BANKS, key=f"{key_prefix}_bank")
    acc  = st.text_input("계좌번호 (숫자만)", placeholder="예: 123456789012",
                          key=f"{key_prefix}_accnum")
    if acc and re.search(r'[^\d\-]', acc):
        st.warning("계좌번호는 숫자(0-9)만 입력할 수 있습니다.")
        acc = re.sub(r'[^\d]', '', acc)
    if bank == "은행 선택":    err = "은행을 선택해 주세요."
    elif not acc:              err = "계좌번호를 입력해 주세요."
    elif not re.fullmatch(r'\d+', acc): err = "계좌번호는 숫자만 입력해 주세요."
    elif len(acc) < 8:         err = "계좌번호가 너무 짧습니다. (최소 8자리)"
    elif len(acc) > 16:        err = "계좌번호가 너무 깁니다. (최대 16자리)"
    else:                      err = None
    formatted = f"{bank} {acc}".strip() if bank != "은행 선택" else acc
    if err and (acc or bank != "은행 선택"): st.error(err)
    return formatted, err


def render_essentials_popup(item: dict):
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
                    'background:linear-gradient(135deg,#EFF6FF,#DBEAFE);'
                    'display:flex;align-items:center;justify-content:center;'
                    'font-size:3rem;margin-bottom:.8rem;">🧴</div>',
                    unsafe_allow_html=True)

    st.markdown(f"### {label}")
    st.markdown(f'<span class="credit-badge">🪙 참여 시 {CREDIT_PER_PURCHASE} 크래딧 적립</span>',
                unsafe_allow_html=True)
    st.markdown("---")

    # ── MAIN ─────────────────────────────────────────────────────────────
    if sub == "main":
        parties = get_open_parties(label)

        if is_admin:
            if st.button("➕ 공동구매 파티 생성", key="ess_create_btn", use_container_width=True):
                pid = create_party(label, image_url, uid)
                st.success(f"파티가 생성됐습니다! (ID: {pid})")
                st.rerun()

        if not parties:
            st.info("현재 진행 중인 공동구매가 없습니다.")
        else:
            st.markdown("**📋 현재 모집 중인 공동구매**")
            for p in parties:
                cnt    = len(p["applicants"])
                already = any(a["user_id"] == uid for a in p["applicants"])
                st.markdown(f"""
                <div class="ess-party-card">
                  <b>파티 #{p['party_id'][:6]}</b>
                  <span class="ess-badge ess-open">모집중</span><br>
                  <span style="font-size:.8rem;color:#64748B;">
                    신청자 {cnt}명 | 생성: {p['created_at'][:10]}
                    | 📅 마감: {p.get('deadline', '-')}
                  </span>
                </div>""", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📝 참여 신청", key=f"ess_apply_{p['party_id']}",
                                 use_container_width=True,
                                 disabled=already or not is_logged):
                        st.session_state.ess_sub      = "apply"
                        st.session_state.ess_party_id = p["party_id"]
                        st.rerun()
                with c2:
                    if is_admin:
                        if st.button("🔍 신청자 현황", key=f"ess_detail_{p['party_id']}",
                                     use_container_width=True):
                            st.session_state.ess_sub      = "admin_detail"
                            st.session_state.ess_party_id = p["party_id"]
                            st.rerun()

                if already:
                    st.success("✅ 신청 완료")
                    if st.button("신청 취소", key=f"ess_cancel_{p['party_id']}"):
                        cancel_apply(p["party_id"], uid); st.rerun()

    # ── APPLY ─────────────────────────────────────────────────────────────
    elif sub == "apply":
        st.markdown("#### 📝 파티 신청")
        st.markdown("**연락처**")
        contact, contact_err = _contact_input("ess_apply")
        qty = st.number_input("필요 개수", min_value=1, max_value=99, value=1, step=1)

        if st.button("신청 완료", use_container_width=True, key="ess_apply_submit"):
            if contact_err or not contact:
                st.error(contact_err or "연락처를 입력해 주세요.")
            else:
                ok2, msg = apply_party(
                    st.session_state.ess_party_id, uid,
                    user.get("name", ""), contact, int(qty))
                if ok2:
                    push(uid, "pot_joined", f"'{label}' 공동구매 파티에 신청됐습니다.")
                    st.success("신청 완료!")
                    st.session_state.ess_sub = "main"; st.rerun()
                else:
                    st.error(msg)

        if st.button("← 뒤로", key="ess_back_apply"):
            st.session_state.ess_sub = "main"; st.rerun()

    # ── ADMIN DETAIL ──────────────────────────────────────────────────────
    elif sub == "admin_detail":
        p = get_party(st.session_state.ess_party_id)
        if not p:
            st.error("파티를 찾을 수 없습니다.")
            st.session_state.ess_sub = "main"; st.rerun()
            return

        status = p["status"]
        status_map = {"open": "🟢 모집중", "closed": "🟡 마감됨", "rated": "🟣 평가완료"}
        st.markdown(f"#### 🔍 파티 상세 — #{p['party_id'][:6]} "
                    f"{status_map.get(status, status)}")

        applicants = p["applicants"]
        total_qty  = sum(a["qty"] for a in applicants)
        st.markdown(f"**총 신청자: {len(applicants)}명 / 총 수량: {total_qty}개**")
        if p.get("deadline"):
            st.caption(f"📅 마감일: {p['deadline']}")

        for a in applicants:
            st.markdown(f"""
            <div class="ess-applicant-row">
              <span>👤 {a['name']} (@{a['user_id']})</span>
              <span>📞 {a['contact']}</span>
              <span><b>{a['qty']}개</b></span>
            </div>""", unsafe_allow_html=True)

        # ── 마감 처리 ──────────────────────────────────────────────────────
        if status == "open":
            st.divider()
            st.markdown("**💰 파티 마감**")
            price_per = st.number_input("개당 가격 (원)", min_value=0, step=100,
                                         value=1000, key="ess_price_per")
            st.markdown("**송금 계좌**")
            pay_dest, pay_dest_err = _account_input("ess_close")

            if st.button("✅ 마감 처리", use_container_width=True, key="ess_close_submit"):
                if pay_dest_err or not pay_dest or pay_dest.startswith("은행 선택"):
                    st.error(pay_dest_err or "계좌번호를 올바르게 입력해 주세요.")
                elif price_per <= 0:
                    st.error("개당 가격을 입력해 주세요.")
                else:
                    closed = close_party(p["party_id"], int(price_per), pay_dest)
                    if closed:
                        for a in applicants:
                            amount = a["qty"] * int(price_per)
                            push(a["user_id"], "pot_ended",
                                 f"'{label}' 공동구매 파티가 마감됐습니다. "
                                 f"총 {amount:,}원을 [{pay_dest.strip()}]로 보내주세요! "
                                 f"({a['qty']}개 × {int(price_per):,}원)")
                        st.success("마감 처리 및 알림 발송 완료!"); st.rerun()

        # ── 크래딧 지급 + 평가 (closed 상태) ──────────────────────────────
        elif status == "closed":
            st.divider()
            st.markdown(f"✅ 마감됨 | 개당 {p['price_per_unit']:,}원 | "
                        f"송금처: {p['payment_dest']}")
            st.markdown("---")

            # 크래딧 지급
            st.markdown(f"**🪙 크래딧 지급** (참여자 인당 {CREDIT_PER_PURCHASE} 크래딧)")
            not_given = [a for a in applicants
                         if not is_credit_given(p["party_id"], a["user_id"])]
            if not not_given:
                st.success("모든 참여자에게 크래딧이 지급됐습니다.")
            else:
                if st.button(f"🪙 {len(not_given)}명에게 크래딧 지급",
                             key="ess_give_credits", use_container_width=True):
                    for a in not_given:
                        add_credits(a["user_id"], CREDIT_PER_PURCHASE)
                        mark_credit_given(p["party_id"], a["user_id"])
                        push(a["user_id"], "pot_joined",
                             f"'{label}' 공동구매 참여로 {CREDIT_PER_PURCHASE} 🪙 크래딧이 적립됐습니다!")
                    st.success("크래딧 지급 완료!"); st.rerun()

            st.markdown("---")

            # 평가
            st.markdown("**⭐ 파티 평가** (참여자 만족도 1~5점)")
            st.caption("평가 후 파티를 삭제할 수 있습니다.")
            scores = {}
            with st.form("ess_rate_form"):
                for a in applicants:
                    scores[a["user_id"]] = st.slider(
                        f"@{a['user_id']} ({a['name']})",
                        1, 5, 3, key=f"rate_{p['party_id']}_{a['user_id']}")
                submitted = st.form_submit_button("평가 완료 및 파티 종료",
                                                   use_container_width=True)
            if submitted:
                # 평가 점수 → rating_store (10점 만점으로 환산: ×2)
                for uid_r, score in scores.items():
                    add_score(uid_r, score * 2)
                save_ratings(p["party_id"], scores)
                for a in applicants:
                    push(a["user_id"], "pot_ended",
                         f"'{label}' 공동구매 파티 평가가 완료됐습니다. 매너 온도를 확인해보세요!")
                st.success("평가 완료!"); st.rerun()

        # ── 삭제 (rated 상태) ──────────────────────────────────────────────
        elif status == "rated":
            st.divider()
            st.success("✅ 평가까지 완료된 파티입니다.")
            ratings = p.get("ratings", {})
            if ratings:
                st.markdown("**평가 결과**")
                for a in applicants:
                    score = ratings.get(a["user_id"], "-")
                    st.markdown(f"- {a['name']} (@{a['user_id']}): **{score}점**")
            if st.button("🗑️ 파티 삭제", key="ess_del_rated",
                         use_container_width=True):
                delete_party(p["party_id"])
                st.success("파티가 삭제됐습니다.")
                st.session_state.ess_sub = "main"; st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← 뒤로", key="ess_back_detail"):
                st.session_state.ess_sub = "main"; st.rerun()
        with c2:
            if is_admin and status == "open":
                if st.button("🗑️ 파티 삭제", key="ess_del_party"):
                    delete_party(p["party_id"])
                    st.session_state.ess_sub = "main"; st.rerun()
                  
