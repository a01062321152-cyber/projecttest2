"""wishlist_page.py — 룰렛 시스템 (편의점 파티 제거)"""

import re
import streamlit as st
import streamlit.components.v1 as components
from roulette_store import (register_item, get_active_items, get_my_items,
                             get_item, get_all_items, spin, has_spun,
                             remove_item, admin_remove_item,
                             SPIN_CREDIT_COST)
from rating_store   import get_temperature
from notification_store import push
from user_store import deduct_credits, get_credits

BANKS = [
    "은행 선택", "국민은행", "신한은행", "우리은행", "하나은행", "농협은행",
    "기업은행", "카카오뱅크", "토스뱅크", "케이뱅크", "SC제일은행",
    "씨티은행", "대구은행", "부산은행", "광주은행", "전북은행", "경남은행",
    "제주은행", "수협은행", "우체국", "새마을금고", "신협",
]

# ── URL 검증 ────────────────────────────────────────────────────────────────

_URL_RE = re.compile(
    r'^https?://'                        # http:// 또는 https://
    r'[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}'   # 도메인
    r'(/[^\s]*)?$',                      # 경로 (선택)
    re.IGNORECASE
)
_IMG_EXT = re.compile(
    r'\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?.*)?$', re.IGNORECASE)

def validate_image_url(url: str) -> str | None:
    """
    이미지 URL 검증.
    빈 문자열 → None (통과, 선택 항목)
    형식 불일치 → 에러 메시지
    """
    url = url.strip()
    if not url:
        return None   # 선택 항목이므로 빈 값은 허용
    if not _URL_RE.match(url):
        return "올바른 URL 형식이 아닙니다. (예: https://example.com/image.jpg)"
    if not _IMG_EXT.search(url):
        return "이미지 파일 URL이어야 합니다. (.jpg .jpeg .png .gif .webp .bmp .svg)"
    return None


def image_url_input(label: str, key: str,
                    placeholder: str = "https://example.com/image.jpg") -> tuple[str, str | None]:
    """이미지 URL 입력 + 실시간 검증 위젯. (value, error_or_None) 반환."""
    url = st.text_input(label, placeholder=placeholder, key=key)
    err = validate_image_url(url)
    if url.strip() and err:
        st.error(err)
    elif url.strip() and not err:
        st.markdown(
            f'<div style="font-size:.75rem;color:#16A34A;">✅ 유효한 이미지 URL</div>',
            unsafe_allow_html=True)
    return url.strip(), err

CSS = """
<style>
.tab-section-title{font-size:1.1rem;font-weight:700;color:#1a1a1a;
  margin-bottom:1rem;border-bottom:2px solid #E5E7EB;padding-bottom:.5rem;}
</style>
"""

# ── 유효성 검사 ──────────────────────────────────────────────────────────────

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


# ── 룰렛 애니메이션 HTML ─────────────────────────────────────────────────────

def _roulette_anim_html(is_win: bool, item_image: str = "") -> str:
    """
    당첨 → 모든 칸이 당첨 이모지/금색
    꽝   → 모든 칸이 꽝 이모지/회색·빨강
    어느 칸에 멈춰도 결과와 시각이 일치.
    """
    win_js = "true" if is_win else "false"
    safe_img = item_image.replace('"', '').replace("'", "") if item_image else ""

    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:transparent;display:flex;flex-direction:column;
  align-items:center;justify-content:center;height:300px;font-family:sans-serif;}}
#wrap{{position:relative;width:220px;height:220px;}}
canvas{{border-radius:50%;box-shadow:0 4px 24px rgba(0,0,0,.2);}}
#ptr{{position:absolute;top:-20px;left:50%;transform:translateX(-50%);
  font-size:2rem;line-height:1;}}
#msg{{margin-top:12px;font-size:1rem;font-weight:700;color:#1a1a1a;
  text-align:center;min-height:24px;}}
</style></head><body>
<div id="wrap">
  <div id="ptr">▼</div>
  <canvas id="c" width="220" height="220"></canvas>
</div>
<div id="msg">🎰 돌아가는 중...</div>
<script>
var isWin = {win_js};
var n = 20, arc = 2*Math.PI/n;
var cv = document.getElementById('c'), ctx = cv.getContext('2d');
var cx=110, cy=110, r=104;

// 당첨: 전 칸 당첨 이모지 + 금색
var WIN_LABELS = ['🎁 당첨','🥳 당첨','🎉 당첨','✨ 당첨','🏆 당첨',
                  '💰 당첨','🎊 당첨','⭐ 당첨','🌟 당첨','💎 당첨',
                  '🎁 당첨','🥳 당첨','🎉 당첨','✨ 당첨','🏆 당첨',
                  '💰 당첨','🎊 당첨','⭐ 당첨','🌟 당첨','💎 당첨'];
var WIN_COLS   = ['#F59E0B','#FBBF24','#F59E0B','#D97706','#FBBF24',
                  '#F59E0B','#FBBF24','#D97706','#F59E0B','#FBBF24',
                  '#D97706','#F59E0B','#FBBF24','#F59E0B','#D97706',
                  '#FBBF24','#F59E0B','#D97706','#FBBF24','#F59E0B'];

// 꽝: 전 칸 꽝 이모지 + 회색/빨강
var LOSE_LABELS = ['😢 꽝','💀 꽝','😅 꽝','🥲 꽝','😵 꽝',
                   '🤦 꽝','😭 꽝','🙈 꽝','😤 꽝','🫠 꽝',
                   '🤡 꽝','😾 꽝','😩 꽝','🤯 꽝','😬 꽝',
                   '🥴 꽝','🫥 꽝','🫣 꽝','😱 꽝','💔 꽝'];
var LOSE_COLS   = ['#EF4444','#6B7280','#EF4444','#9CA3AF','#EF4444',
                   '#6B7280','#EF4444','#9CA3AF','#EF4444','#6B7280',
                   '#EF4444','#9CA3AF','#EF4444','#6B7280','#EF4444',
                   '#9CA3AF','#EF4444','#6B7280','#9CA3AF','#EF4444'];

var LABELS = isWin ? WIN_LABELS : LOSE_LABELS;
var COLS   = isWin ? WIN_COLS   : LOSE_COLS;

// 상품 이미지 (당첨 시 첫 칸에 표시)
var prodImg = null;
if(isWin && "{safe_img}"){{
  prodImg = new Image();
  prodImg.crossOrigin = 'anonymous';
  prodImg.src = "{safe_img}";
}}

function draw(angle){{
  ctx.clearRect(0,0,220,220);
  for(var i=0;i<n;i++){{
    var s = angle + i*arc;
    ctx.beginPath(); ctx.moveTo(cx,cy);
    ctx.arc(cx,cy,r,s,s+arc); ctx.closePath();
    ctx.fillStyle = COLS[i]; ctx.fill();

    ctx.save(); ctx.translate(cx,cy); ctx.rotate(s+arc/2);
    if(isWin && i===0 && prodImg && prodImg.complete && prodImg.naturalWidth>0){{
      var iw=28,ih=18;
      ctx.save(); ctx.beginPath();
      ctx.rect(r-iw-6,-ih/2,iw,ih); ctx.clip();
      ctx.drawImage(prodImg,r-iw-6,-ih/2,iw,ih);
      ctx.restore();
    }} else {{
      ctx.fillStyle='#fff'; ctx.font='bold 9px sans-serif';
      ctx.textAlign='right';
      ctx.fillText(LABELS[i],r-6,4);
    }}
    ctx.restore();
  }}
  // 중심원
  ctx.beginPath(); ctx.arc(cx,cy,22,0,2*Math.PI);
  ctx.fillStyle = isWin ? '#FEF3C7' : '#F3F4F6';
  ctx.fill();
  ctx.strokeStyle='#E5E7EB'; ctx.lineWidth=2; ctx.stroke();
  ctx.font='14px sans-serif'; ctx.textAlign='center';
  ctx.fillStyle='#1a1a1a';
  ctx.fillText(isWin ? '🎁' : '😢', cx, cy+5);
}}

draw(0);

// 어느 칸이든 같은 내용 → 랜덤 위치에 멈춰도 결과와 일치
var stopIdx    = Math.floor(Math.random()*n);
var spins      = 6 + Math.random()*2;
var finalAngle = -(spins*2*Math.PI + stopIdx*arc + arc/2);
var duration   = 5000, startTime = null;

function animate(ts){{
  if(!startTime) startTime=ts;
  var prog=Math.min((ts-startTime)/duration,1);
  var ease=1-Math.pow(1-prog,4);
  draw(finalAngle*ease);
  if(prog<1){{ requestAnimationFrame(animate); }}
  else{{ document.getElementById('msg').innerText=isWin?'🎉 당첨!!!':'😢 꽝...'; }}
}}

if(prodImg && !prodImg.complete){{
  prodImg.onload  = function(){{ requestAnimationFrame(animate); }};
  prodImg.onerror = function(){{ requestAnimationFrame(animate); }};
}} else {{ requestAnimationFrame(animate); }}
</script></body></html>"""
# ── 메인 렌더 ────────────────────────────────────────────────────────────────

def render_wishlist_page():
    st.markdown(CSS, unsafe_allow_html=True)

    user      = st.session_state.get("user", {})
    uid       = user.get("user_id", "")
    uname     = user.get("name", "")
    is_logged = "user" in st.session_state
    temp      = get_temperature(uid) if is_logged else 0.0
    credits   = get_credits(uid) if is_logged else 0

    st.markdown('<div class="tab-section-title">🎰 럭키 룰렛</div>',
                unsafe_allow_html=True)

    if not is_logged:
        st.info("로그인이 필요합니다.")
        return

    # 크래딧 + 매너온도 표시
    col_c, col_t = st.columns(2)
    with col_c:
        st.markdown(f"🪙 **보유 크래딧: {credits}**")
    with col_t:
        st.markdown(f"🌡️ **매너 온도: {temp}°**")

    st.caption(f"1회 참여 비용: {SPIN_CREDIT_COST}🪙 크래딧 | 참여 조건: 매너 온도 50° 이상")
    st.markdown("---")

    for k, v in [("roulette_result", None), ("roulette_spin_rid", None),
                  ("roulette_spinning", False)]:
        if k not in st.session_state: st.session_state[k] = v

    is_admin = st.session_state.get("user", {}).get("is_admin", False)

    if is_admin:
        rt1, rt2, rt3 = st.tabs(["🎁 상품 목록", "📦 내 등록 상품", "🛡️ 관리자"])
    else:
        rt1, rt2 = st.tabs(["🎁 상품 목록", "📦 내 등록 상품"])
        rt3 = None

    # ── 상품 목록 ─────────────────────────────────────────────────────────
    with rt1:
        active_items = get_active_items(exclude_user_id=uid)

        if not active_items:
            st.info("등록된 상품이 없습니다. 내 등록 상품 탭에서 등록해 보세요!")
        else:
            for item in active_items:
                rid   = item["roulette_id"]
                prob  = max(1, 20 - item["spin_count"])
                spun  = has_spun(rid, uid)

                col_img, col_info = st.columns([1, 3])
                with col_img:
                    if item.get("image_url","").strip():
                        try:
                            st.image(item["image_url"], width=80)
                        except Exception:
                            st.markdown(
                                '<div style="width:80px;height:80px;border-radius:10px;'
                                'background:linear-gradient(135deg,#EEF4FF,#DBEAFE);'
                                'display:flex;align-items:center;justify-content:center;'
                                'font-size:2rem;">🎁</div>',
                                unsafe_allow_html=True)
                    else:
                        st.markdown(
                            '<div style="width:80px;height:80px;border-radius:10px;'
                            'background:linear-gradient(135deg,#EEF4FF,#DBEAFE);'
                            'display:flex;align-items:center;justify-content:center;'
                            'font-size:2rem;">🎁</div>',
                            unsafe_allow_html=True)
                with col_info:
                    st.markdown(f"**{item['item_name']}**")
                    st.caption(item["item_desc"])
                    st.markdown(f"등록자: {item['owner_name']} | 현재 확률: **1/{prob}**")

                    if temp < 50:
                        st.warning(f"매너 온도 50° 이상만 참여 가능 (현재 {temp}°)")
                    elif credits < SPIN_CREDIT_COST:
                        st.warning(f"크래딧이 부족합니다. (필요: {SPIN_CREDIT_COST}, 보유: {credits})")
                    else:
                        if st.button(f"🎰 도전! ({SPIN_CREDIT_COST}🪙 소모)",
                                     key=f"spin_{rid}"):
                            # 크래딧 먼저 차감
                            ok, new_bal = deduct_credits(uid, SPIN_CREDIT_COST)
                            if not ok:
                                st.error("크래딧 차감에 실패했습니다.")
                            else:
                                is_win, msg = spin(rid, uid)
                                # session_state 갱신
                                st.session_state.user["credits"] = new_bal
                                st.session_state.roulette_result   = (is_win, msg, rid)
                                st.session_state.roulette_spin_rid = rid
                                st.session_state.roulette_spinning = True
                                st.rerun()

                st.divider()

        # ── 룰렛 애니메이션 + 결과 ───────────────────────────────────────
        if st.session_state.get("roulette_spinning") and st.session_state.roulette_result:
            import time, random as _r
            is_win, msg, rid = st.session_state.roulette_result
            item = get_item(rid)
            item_img = item.get("image_url", "") if item else ""

            st.markdown("---")
            ph = st.empty()
            with ph:
                components.html(
                    _roulette_anim_html(is_win, item_img),
                    height=320, scrolling=False)
            time.sleep(5)
            ph.empty()
            st.session_state.roulette_spinning = False

            if is_win and item:
                st.balloons()
                win_msgs = [
                    "🎉 대박!! 당첨됐습니다!!!",
                    "🥳 오늘 운이 완전 터졌네요!",
                    "🏆 믿기지 않지만... 당첨!!!",
                    "✨ 하늘이 당신 편이에요! 당첨!",
                ]
                st.success(_r.choice(win_msgs))
                st.info(f"**상품:** {item['item_name']}\n\n"
                        f"**등록자:** {item['owner_name']}\n\n"
                        f"📞 **연락처:** {item['contact']}")
                push(item["owner_id"], "pot_ended",
                     f"{uname}님이 '{item['item_name']}' 룰렛에 당첨됐습니다! "
                     f"연락을 기다려 주세요.")
            else:
                lose_msgs = [
                    "😢 아쉽네요... 꽝입니다.",
                    "💀 오늘은 운이 없어요. 다음엔 될 거예요!",
                    "🤡 꽝! 세상이 야속하네요...",
                    "😭 꽝... 하지만 확률이 올랐어요!",
                    "🫠 녹아내리는 기분이지만 포기하지 마세요!",
                    "🥲 꽝이지만 당신은 소중한 사람입니다.",
                ]
                prob_left = max(1, 20 - (item["spin_count"] if item else 20))
                st.warning(_r.choice(lose_msgs))
                st.caption(f"다음 도전 확률: **1/{prob_left}** | 남은 크래딧: {get_credits(uid)}")

            if st.button("확인", key="roulette_confirm"):
                st.session_state.roulette_result   = None
                st.session_state.roulette_spin_rid = None
                st.session_state.roulette_spinning = False
                st.rerun()

        elif st.session_state.roulette_result and not st.session_state.get("roulette_spinning"):
            import random as _r
            is_win, msg, rid = st.session_state.roulette_result
            item = get_item(rid)
            st.markdown("---")
            if is_win and item:
                st.success(f"🎉 당첨! **{item['item_name']}**")
                st.info(f"📞 연락처: **{item['contact']}** ({item['owner_name']})")
            else:
                prob_left = max(1, 20 - (item["spin_count"] if item else 20))
                st.warning(f"😢 꽝! 다음 확률: **1/{prob_left}**")
            if st.button("확인", key="roulette_confirm2"):
                st.session_state.roulette_result   = None
                st.session_state.roulette_spin_rid = None
                st.rerun()

    # ── 내 상품 관리 ──────────────────────────────────────────────────────
    with rt2:
        st.markdown("**내가 등록한 상품**")
        my_items    = get_my_items(uid)
        # active 상품만 표시 (won·removed 자동 제외)
        active_mine = [i for i in my_items if i["status"] == "active"]

        if not active_mine:
            st.info("현재 등록된 상품이 없습니다.")
        else:
            for item in active_mine:
                st.markdown(f"**{item['item_name']}** — 🟢 등록중 | 시도 {item['spin_count']}회")
                st.caption(item["item_desc"])
                if st.button("삭제", key=f"rm_roulette_{item['roulette_id']}"):
                    remove_item(item["roulette_id"], uid); st.rerun()
                st.divider()

        st.markdown("---")
        st.markdown("**➕ 룰렛 상품 등록**")
        r_name = st.text_input("상품 이름", placeholder="예: 스타벅스 아메리카노 기프티콘", key="r_name")
        r_desc = st.text_area("상품 설명", placeholder="상태, 브랜드 등 간단히 적어주세요", key="r_desc")
        st.markdown("**연락처** (당첨자가 연락할 방법)")
        r_contact, r_contact_err = _contact_input("roulette_reg")
        r_img, r_img_err = image_url_input("이미지 URL (선택)", key="r_img")

        if st.button("등록", use_container_width=True, key="roulette_reg_btn"):
            errs = []
            if not r_name.strip():               errs.append("상품 이름을 입력해 주세요.")
            if r_contact_err or not r_contact:   errs.append(r_contact_err or "연락처를 입력해 주세요.")
            if r_img_err:                        errs.append(r_img_err)
            if temp < 50:                        errs.append(f"매너 온도 50° 이상만 등록 가능 (현재 {temp}°)")
            if errs:
                for e in errs: st.error(e)
            else:
                register_item(uid, uname, temp, r_name.strip(),
                              r_desc.strip(), r_contact, r_img.strip())
                st.success("상품이 등록됐습니다!"); st.rerun()

    # ── 관리자 탭 ─────────────────────────────────────────────────────────
    if rt3 is not None:
        with rt3:
            st.markdown("**🛡️ 전체 상품 현황**")
            all_items = get_all_items()
            status_map = {"active": "🟢 등록중", "won": "🏆 당첨됨", "removed": "❌ 삭제됨"}

            if not all_items:
                st.info("등록된 상품이 없습니다.")
            else:
                for item in sorted(all_items,
                                   key=lambda x: x["created_at"], reverse=True):
                    s = status_map.get(item["status"], item["status"])
                    col_i, col_t, col_b = st.columns([1, 5, 1])
                    with col_i:
                        if item.get("image_url","").strip():
                            try:
                                st.image(item["image_url"], width=60)
                            except Exception:
                                st.markdown("🎁")
                        else:
                            st.markdown("🎁")
                    with col_t:
                        st.markdown(f"**{item['item_name']}** {s}")
                        st.caption(
                            f"등록자: {item['owner_name']} | "
                            f"시도: {item['spin_count']}회 | "
                            f"{item['created_at'][:10]}")
                    with col_b:
                        if item["status"] == "active":
                            if st.button("🗑️", key=f"admin_rm_{item['roulette_id']}",
                                         help="강제 삭제"):
                                admin_remove_item(item["roulette_id"])
                                st.success("삭제됐습니다."); st.rerun()
                    st.divider()
