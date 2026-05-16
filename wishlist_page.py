"""wishlist_page.py — 편의점 파티 생성 + 룰렛 시스템"""

import re
import streamlit as st
import streamlit.components.v1 as components
from cvs_store      import create_party as cvs_create
from roulette_store import (register_item, get_active_items, get_my_items,
                             get_item, spin, has_spun, remove_item)
from rating_store   import get_temperature
from notification_store import push

# ── 상수 ─────────────────────────────────────────────────────────────────────
BANKS = [
    "은행 선택", "국민은행", "신한은행", "우리은행", "하나은행", "농협은행",
    "기업은행", "카카오뱅크", "토스뱅크", "케이뱅크", "SC제일은행",
    "씨티은행", "대구은행", "부산은행", "광주은행", "전북은행", "경남은행",
    "제주은행", "수협은행", "우체국", "새마을금고", "신협",
]

CSS = """
<style>
.tab-section-title{font-size:1.1rem;font-weight:700;color:#1a1a1a;
  margin-bottom:1rem;border-bottom:2px solid #E5E7EB;padding-bottom:.5rem;}
.roulette-card{border:1.5px solid #E5E7EB;border-radius:14px;
  padding:1rem 1.2rem;margin-bottom:.8rem;background:#FAFAFA;
  display:flex;gap:1rem;align-items:flex-start;}
.cvs-my-party{border:1.5px solid #DBEAFE;border-radius:14px;
  padding:.9rem 1.1rem;margin-bottom:.8rem;background:#F0F7FF;}
.cvs-order-row{display:flex;justify-content:space-between;align-items:center;
  padding:.45rem .6rem;border-radius:8px;background:#F3F4F6;margin-bottom:.35rem;
  font-size:.82rem;}
.cvs-paid{color:#16A34A;font-weight:700;}
.cvs-unpaid{color:#DC2626;}
.input-hint{font-size:.75rem;color:#9CA3AF;margin-top:.15rem;}
</style>
"""

# ── 유효성 검사 ──────────────────────────────────────────────────────────────

def _validate_contact_kakao(v: str) -> str | None:
    v = v.strip()
    if not v:         return "카카오톡 ID를 입력해 주세요."
    if len(v) < 3:    return "카카오톡 ID는 3자 이상이어야 합니다."
    if " " in v:      return "카카오톡 ID에 공백을 포함할 수 없습니다."
    if not re.fullmatch(r'[A-Za-z0-9_]+', v):
        return "카카오톡 ID는 영어, 숫자, 밑줄(_)만 사용할 수 있습니다."
    return None

def _validate_contact_phone(v: str) -> str | None:
    digits = re.sub(r'\D', '', v)
    if not digits:                      return "전화번호를 입력해 주세요."
    if not re.fullmatch(r'01[0-9]{8,9}', digits):
        return "올바른 전화번호를 입력해 주세요. (예: 01012345678)"
    return None

def _validate_account_number(v: str) -> str | None:
    v = v.strip()
    if not v:                           return "계좌번호를 입력해 주세요."
    if not re.fullmatch(r'[\d\-]+', v): return "계좌번호는 숫자만 입력해 주세요."
    digits = re.sub(r'\D', '', v)
    if len(digits) < 8:                 return "계좌번호가 너무 짧습니다."
    return None

def _format_phone(v: str) -> str:
    """01012345678 → 010-1234-5678"""
    d = re.sub(r'\D', '', v)
    if len(d) == 11:
        return f"{d[:3]}-{d[3:7]}-{d[7:]}"
    return d

# ── 연락처 입력 위젯 (공통) ──────────────────────────────────────────────────

def _contact_input(key_prefix: str) -> tuple[str, str | None]:
    """
    카카오톡 ID / 전화번호 선택 후 입력.
    Returns (formatted_value, error_or_None)
    """
    contact_type = st.radio(
        "연락처 유형",
        ["카카오톡 ID", "전화번호"],
        horizontal=True,
        key=f"{key_prefix}_ctype",
    )
    if contact_type == "카카오톡 ID":
        val = st.text_input("카카오톡 ID",
                             placeholder="예: gume_user123",
                             help="영어, 숫자, 밑줄(_)만 사용 가능합니다.",
                             key=f"{key_prefix}_cval")
        err = _validate_contact_kakao(val) if val else None
    else:
        val = st.text_input("전화번호",
                             placeholder="예: 01012345678 (숫자만)",
                             key=f"{key_prefix}_cval")
        if val:
            err = _validate_contact_phone(val)
            if not err:
                val = _format_phone(val)
        else:
            err = None
    if val and err:
        st.error(err)
    return val.strip(), err

# ── 계좌 입력 위젯 (공통) ────────────────────────────────────────────────────

def _account_input(key_prefix: str) -> tuple[str, str | None]:
    """
    은행 선택 + 숫자만 입력.
    Returns (formatted_account, error_or_None)
    미입력·형식 불일치·은행 미선택 모두 error 반환.
    """
    bank = st.selectbox("은행", BANKS, key=f"{key_prefix}_bank")
    acc  = st.text_input("계좌번호 (숫자만)",
                          placeholder="예: 123456789012",
                          key=f"{key_prefix}_accnum")

    # 숫자·하이픈 외 문자 즉시 경고 + 자동 제거
    if acc and re.search(r'[^\d\-]', acc):
        st.warning("계좌번호는 숫자(0-9)만 입력할 수 있습니다.")
        acc = re.sub(r'[^\d]', '', acc)

    # 에러 판정 (항상 명시적으로)
    if bank == "은행 선택":
        err = "은행을 선택해 주세요."
    elif not acc:
        err = "계좌번호를 입력해 주세요."
    elif not re.fullmatch(r'\d+', acc):
        err = "계좌번호는 숫자만 입력해 주세요."
    elif len(acc) < 8:
        err = "계좌번호가 너무 짧습니다. (최소 8자리)"
    elif len(acc) > 16:
        err = "계좌번호가 너무 깁니다. (최대 16자리)"
    else:
        err = None

    formatted = f"{bank} {acc}".strip() if bank != "은행 선택" else acc
    if err and (acc or bank != "은행 선택"):
        st.error(err)
    return formatted, err

# ── 지도 HTML ────────────────────────────────────────────────────────────────

def _map_pick_html():
    return """<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{margin:0;padding:0;width:100%;height:280px;}
#info{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.65);color:#fff;font-size:.75rem;
  padding:4px 14px;border-radius:20px;z-index:999;white-space:nowrap;}
#cur-btn{position:absolute;top:8px;right:8px;z-index:999;
  background:#fff;border:none;border-radius:8px;padding:6px 10px;
  font-size:.8rem;font-weight:600;cursor:pointer;color:#3B82F6;
  box-shadow:0 2px 8px rgba(0,0,0,.15);}
</style></head><body>
<div id="map"></div>
<div id="info">지도를 클릭해 위치를 선택하세요</div>
<button id="cur-btn" onclick="goMyLocation()">📍 내 위치로</button>
<script>
var map=L.map('map').setView([37.5665,126.9780],14);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {attribution:'© OpenStreetMap'}).addTo(map);
var mk=null, myMk=null;

function setPin(la,lo){
  if(mk) map.removeLayer(mk);
  mk=L.marker([la,lo]).addTo(map);
  document.getElementById('info').innerText='📍 '+la.toFixed(5)+', '+lo.toFixed(5);
  window.parent.postMessage({type:'MAP_PICK',lat:la,lng:lo},'*');
}
map.on('click',function(e){ setPin(e.latlng.lat,e.latlng.lng); });

function goMyLocation(){
  if(!navigator.geolocation){ alert('위치 권한이 없습니다.'); return; }
  navigator.geolocation.getCurrentPosition(function(pos){
    var la=pos.coords.latitude, lo=pos.coords.longitude;
    map.setView([la,lo],16);
    if(myMk) map.removeLayer(myMk);
    myMk=L.circleMarker([la,lo],
      {radius:8,color:'#3B82F6',fillColor:'#93C5FD',fillOpacity:.9})
      .addTo(map).bindPopup('📍 내 위치').openPopup();
  },function(){ alert('위치를 가져올 수 없습니다.'); });
}

if(navigator.geolocation){
  navigator.geolocation.getCurrentPosition(function(pos){
    var la=pos.coords.latitude, lo=pos.coords.longitude;
    map.setView([la,lo],15);
    myMk=L.circleMarker([la,lo],
      {radius:8,color:'#3B82F6',fillColor:'#93C5FD',fillOpacity:.9})
      .addTo(map).bindPopup('📍 내 위치');
  });
}
</script></body></html>"""


def _map_view_inline(lat, lng, name):
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{{margin:0;padding:0;width:100%;height:240px;}}</style>
</head><body><div id="map"></div>
<script>
var m=L.map('map').setView([{lat},{lng}],16);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{attribution:'© OpenStreetMap'}}).addTo(m);
L.marker([{lat},{lng}]).addTo(m).bindPopup('{name}').openPopup();
if(navigator.geolocation){{
  navigator.geolocation.getCurrentPosition(function(pos){{
    L.circleMarker([pos.coords.latitude,pos.coords.longitude],
      {{radius:8,color:'#3B82F6',fillColor:'#93C5FD',fillOpacity:.9}})
      .addTo(m).bindPopup('📍 내 위치');
  }});
}}
</script></body></html>"""

# ── 룰렛 애니메이션 ──────────────────────────────────────────────────────────

def _roulette_anim_html(is_win: bool) -> str:
    win_js = "true" if is_win else "false"
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:transparent;display:flex;flex-direction:column;
  align-items:center;justify-content:center;height:260px;
  font-family:'DM Sans',sans-serif;}}
#wrap{{position:relative;width:200px;height:200px;}}
canvas{{border-radius:50%;box-shadow:0 4px 24px rgba(0,0,0,.2);}}
#ptr{{position:absolute;top:-18px;left:50%;transform:translateX(-50%);
  font-size:1.8rem;line-height:1;}}
#msg{{margin-top:10px;font-size:.95rem;font-weight:700;color:#1a1a1a;
  text-align:center;min-height:22px;}}
</style></head><body>
<div id="wrap">
  <div id="ptr">▼</div>
  <canvas id="c" width="200" height="200"></canvas>
</div>
<div id="msg">🎰 돌아가는 중...</div>
<script>
var SEG=['🎁 당첨','😢 꽝','😅 꽝','🥲 꽝','💀 꽝',
         '😵 꽝','🤦 꽝','😭 꽝','🙈 꽝','😤 꽝',
         '🫠 꽝','🤡 꽝','😾 꽝','😩 꽝','🤯 꽝',
         '😬 꽝','🥴 꽝','🫥 꽝','🫣 꽝','😱 꽝'];
var COL=['#3B82F6','#EF4444','#F59E0B','#10B981','#8B5CF6',
         '#EC4899','#14B8A6','#F97316','#6366F1','#84CC16',
         '#EF4444','#3B82F6','#F59E0B','#10B981','#8B5CF6',
         '#EC4899','#14B8A6','#F97316','#6366F1','#84CC16'];
var n=SEG.length, arc=2*Math.PI/n;
var cv=document.getElementById('c'), ctx=cv.getContext('2d');
var cx=100, cy=100, r=94;
var isWin={win_js};
function draw(angle){{
  ctx.clearRect(0,0,200,200);
  for(var i=0;i<n;i++){{
    var s=angle+i*arc;
    ctx.beginPath(); ctx.moveTo(cx,cy);
    ctx.arc(cx,cy,r,s,s+arc); ctx.closePath();
    ctx.fillStyle=COL[i]; ctx.fill();
    ctx.save(); ctx.translate(cx,cy); ctx.rotate(s+arc/2);
    ctx.fillStyle='#fff'; ctx.font='bold 10px sans-serif';
    ctx.textAlign='right'; ctx.fillText(SEG[i],r-6,4); ctx.restore();
  }}
  ctx.beginPath(); ctx.arc(cx,cy,20,0,2*Math.PI);
  ctx.fillStyle='#fff'; ctx.fill();
  ctx.strokeStyle='#E5E7EB'; ctx.lineWidth=2; ctx.stroke();
}}
draw(0);
var stopIdx=isWin?0:(Math.floor(Math.random()*(n-1))+1);
var spins=6+Math.random()*2;
var finalAngle=-(spins*2*Math.PI+stopIdx*arc+arc/2);
var duration=5000, startTime=null;
function animate(ts){{
  if(!startTime) startTime=ts;
  var prog=Math.min((ts-startTime)/duration,1);
  var ease=1-Math.pow(1-prog,4);
  draw(finalAngle*ease);
  if(prog<1){{ requestAnimationFrame(animate); }}
  else{{ document.getElementById('msg').innerText=isWin?'🎉 당첨!!!':'😢 꽝...'; }}
}}
requestAnimationFrame(animate);
</script></body></html>"""


# ── 메인 렌더 함수 ────────────────────────────────────────────────────────────

def render_wishlist_page():
    st.markdown(CSS, unsafe_allow_html=True)

    user      = st.session_state.get("user", {})
    uid       = user.get("user_id", "")
    uname     = user.get("name", "")
    is_logged = "user" in st.session_state
    temp      = get_temperature(uid) if is_logged else 0.0

    tab1, tab2 = st.tabs(["🏪 편의점 파티", "🎰 룰렛 시스템"])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1 — 편의점 파티
    # ══════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown('<div class="tab-section-title">🏪 편의점 파티</div>',
                    unsafe_allow_html=True)

        if not is_logged:
            st.info("로그인이 필요합니다.")
        else:
            # ── 파티 생성 ─────────────────────────────────────────────────
            with st.expander("➕ 새 파티 만들기", expanded=False):
                st.markdown("**출발 시간**")
                depart_time_obj = st.time_input(
                    "출발 시간 선택",
                    value=None,
                    key="cvs_depart_time",
                    help="시간을 클릭해서 선택하세요.",
                    label_visibility="collapsed",
                )
                st.markdown("**연락처**")
                contact, contact_err = _contact_input("cvs_create")

                st.markdown("**입금 계좌**")
                account, account_err = _account_input("cvs_create")

                st.markdown("")
                if st.button("파티 생성", key="cvs_create_btn", use_container_width=True):
                    errs = []
                    if depart_time_obj is None:
                        errs.append("출발 시간을 선택해 주세요.")
                    if contact_err or not contact:
                        errs.append(contact_err or "연락처를 입력해 주세요.")
                    if account_err:
                        errs.append(account_err)
                    elif not account or account.strip() in ("", "은행 선택"):
                        errs.append("계좌번호를 올바르게 입력해 주세요.")

                    if errs:
                        for e in errs: st.error(e)
                    else:
                        depart_str = depart_time_obj.strftime("%H:%M")
                        pid = cvs_create(uid, uname, depart_str, contact, account)
                        st.success(f"파티가 생성됐습니다! (ID: {pid})")
                        st.rerun()

            st.divider()

            # ── 내 파티 목록 ──────────────────────────────────────────────
            from cvs_store import (get_parties_by_user, get_party,
                                    confirm_order, depart_party,
                                    set_gather_location, delete_party)
            from notification_store import push_all as _pa

            my_parties = get_parties_by_user(uid)
            if my_parties:
                st.markdown("**📋 내 파티 목록**")
                for p in my_parties:
                    is_creator = p["creator_id"] == uid
                    status_map = {
                        "waiting": "🟡 대기중",
                        "departed": "🚀 출발",
                        "arrived": "📍 집합완료",
                    }
                    status_txt = status_map.get(p["status"], p["status"])

                    with st.expander(
                        f"{'[파티장] ' if is_creator else '[참여] '}"
                        f"{p['creator_name']} · {p['depart_time']} · {status_txt}",
                        expanded=False,
                    ):
                        st.markdown(f"""
                        <div class="cvs-my-party">
                          <b>출발: {p['depart_time']}</b> | 상태: {status_txt}<br>
                          📞 {p['contact']} | 💳 {p['account']}
                        </div>""", unsafe_allow_html=True)

                        orders = p["orders"]
                        if orders:
                            st.markdown("**주문 목록**")
                            for idx, o in enumerate(orders):
                                paid_txt = "✅ 확정" if o["confirmed"] else "⏳ 입금대기"
                                st.markdown(f"""
                                <div class="cvs-order-row">
                                  <span>👤 {o['name']}</span>
                                  <span>{o['item_label']} × {o['qty']}</span>
                                  <span>{o['qty']*o['price']:,}원</span>
                                  <span class="{'cvs-paid' if o['confirmed'] else 'cvs-unpaid'}">
                                    {paid_txt}</span>
                                </div>""", unsafe_allow_html=True)

                                if is_creator and not o["confirmed"]:
                                    if st.button(
                                        f"✅ 합류 확인 (#{idx+1})",
                                        key=f"cvs_confirm_{p['party_id']}_{idx}",
                                    ):
                                        confirm_order(p["party_id"], idx)
                                        push(o["user_id"], "pot_joined",
                                             f"'{o['item_label']}' 입금이 확인됐습니다. "
                                             f"파티에 합류됐어요!")
                                        st.rerun()
                        else:
                            st.caption("아직 주문이 없습니다.")

                        if is_creator:
                            if p["status"] == "waiting":
                                if st.button("🚀 파티 출발!",
                                             key=f"cvs_depart_{p['party_id']}",
                                             use_container_width=True):
                                    depart_party(p["party_id"])
                                    members = list({o["user_id"] for o in orders})
                                    _pa(members, "pot_joined",
                                        f"{uname}의 편의점 파티가 출발했습니다!")
                                    st.success("출발!"); st.rerun()

                            elif p["status"] == "departed":
                                st.markdown("**📍 집합 위치 전송**")
                                gather_loc = st.text_input(
                                    "집합 장소 이름",
                                    key=f"gloc_{p['party_id']}",
                                    placeholder="예: 편의점 앞 공원 벤치",
                                )
                                gather_lat = st.number_input(
                                    "위도", value=37.5665, format="%.5f",
                                    key=f"glat_{p['party_id']}",
                                )
                                gather_lng = st.number_input(
                                    "경도", value=126.9780, format="%.5f",
                                    key=f"glng_{p['party_id']}",
                                )
                                st.caption("아래 지도를 클릭하면 좌표가 표시됩니다. "
                                           "📍 내 위치로 버튼으로 현재 위치를 불러올 수 있어요.")
                                components.html(_map_pick_html(), height=300, scrolling=False)

                                if st.button("📍 위치 전송",
                                             key=f"cvs_gather_{p['party_id']}",
                                             use_container_width=True):
                                    if not gather_loc.strip():
                                        st.warning("장소 이름을 입력해 주세요.")
                                    else:
                                        set_gather_location(
                                            p["party_id"], gather_loc,
                                            gather_lat, gather_lng,
                                        )
                                        members = list({o["user_id"] for o in orders})
                                        _pa(members, "pot_joined",
                                            f"집합 위치: {gather_loc} "
                                            f"(위도 {gather_lat:.4f}, 경도 {gather_lng:.4f})")
                                        st.success("위치 전송 완료!"); st.rerun()

                            elif p["status"] == "arrived" and p.get("gather_location"):
                                st.success(f"📍 집합 위치: {p['gather_location']}")
                                components.html(
                                    _map_view_inline(
                                        p["gather_lat"],
                                        p["gather_lng"],
                                        p["gather_location"],
                                    ),
                                    height=260, scrolling=False,
                                )
                                if st.button("🗑️ 파티 삭제",
                                             key=f"cvs_del_{p['party_id']}",
                                             use_container_width=True):
                                    delete_party(p["party_id"])
                                    st.success("파티가 삭제됐습니다."); st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — 룰렛 시스템
    # ══════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown('<div class="tab-section-title">🎰 룰렛 시스템</div>',
                    unsafe_allow_html=True)

        if not is_logged:
            st.info("로그인이 필요합니다.")
            return

        for k, v in [("roulette_result", None),
                      ("roulette_spin_rid", None),
                      ("roulette_spinning", False)]:
            if k not in st.session_state:
                st.session_state[k] = v

        rt1, rt2 = st.tabs(["🎁 상품 목록", "📦 내 상품 관리"])

        # ── 상품 목록 ──────────────────────────────────────────────────────
        with rt1:
            # active 상품만 (won·removed 자동 제외)
            active_items = get_active_items(exclude_user_id=uid)

            if not active_items:
                st.info("등록된 상품이 없습니다. 내 상품 관리에서 등록해 보세요!")
            else:
                for item in active_items:
                    rid  = item["roulette_id"]
                    prob = max(1, 20 - item["spin_count"])
                    spun = has_spun(rid, uid)
                    won  = item["status"] == "won"  # 혹시 목록에 포함됐을 경우 방어

                    if won:
                        continue  # 당첨 상품은 건너뜀 (자동 필터)

                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        if item.get("image_url"):
                            st.image(item["image_url"], width=80)
                        else:
                            st.markdown(
                                '<div style="width:80px;height:80px;border-radius:10px;'
                                'background:linear-gradient(135deg,#EEF4FF,#DBEAFE);'
                                'display:flex;align-items:center;justify-content:center;'
                                'font-size:2rem;">🎁</div>',
                                unsafe_allow_html=True,
                            )
                    with col_info:
                        st.markdown(f"**{item['item_name']}**")
                        st.caption(item["item_desc"])
                        st.markdown(
                            f"등록자: {item['owner_name']} | "
                            f"현재 확률: **1/{prob}**"
                        )
                        if spun:
                            st.warning("이미 참여한 상품입니다.")
                        elif temp < 50:
                            st.warning(
                                f"매너 온도 50° 이상만 참여 가능 (현재 {temp}°)"
                            )
                        else:
                            if st.button(
                                "🎰 룰렛 돌리기",
                                key=f"spin_{rid}",
                            ):
                                is_win, msg = spin(rid, uid)
                                st.session_state.roulette_result   = (is_win, msg, rid)
                                st.session_state.roulette_spin_rid = rid
                                st.session_state.roulette_spinning = True
                                st.rerun()

                    st.divider()

            # ── 애니메이션 + 결과 ─────────────────────────────────────────
            if st.session_state.get("roulette_spinning") and st.session_state.roulette_result:
                import time, random as _r
                is_win, msg, rid = st.session_state.roulette_result
                item = get_item(rid)

                st.markdown("---")
                ph = st.empty()
                with ph:
                    components.html(_roulette_anim_html(is_win), height=260, scrolling=False)
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
                    st.info(
                        f"**상품:** {item['item_name']}\n\n"
                        f"**등록자:** {item['owner_name']}\n\n"
                        f"📞 **연락처:** {item['contact']}"
                    )
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
                    st.caption(f"다음 도전 확률: **1/{prob_left}** (점점 올라가는 중!)")

                if st.button("확인", key="roulette_confirm"):
                    st.session_state.roulette_result   = None
                    st.session_state.roulette_spin_rid = None
                    st.session_state.roulette_spinning = False
                    st.rerun()

            elif (st.session_state.roulette_result
                  and not st.session_state.get("roulette_spinning")):
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

        # ── 내 상품 관리 ───────────────────────────────────────────────────
        with rt2:
            st.markdown("**내 등록 상품**")
            my_items = get_my_items(uid)
            status_map = {"active": "🟢 등록중", "won": "🏆 당첨됨", "removed": "❌ 삭제됨"}

            # won·removed 상품은 목록에 표시만 하고 자동 정리 안내
            active_mine  = [i for i in my_items if i["status"] == "active"]
            ended_mine   = [i for i in my_items if i["status"] in ("won", "removed")]

            if not active_mine and not ended_mine:
                st.info("등록한 상품이 없습니다.")

            for item in active_mine:
                st.markdown(f"**{item['item_name']}** — 🟢 등록중 | 시도 {item['spin_count']}회")
                st.caption(item["item_desc"])
                if st.button("삭제", key=f"rm_roulette_{item['roulette_id']}"):
                    remove_item(item["roulette_id"], uid)
                    st.rerun()
                st.divider()

            if ended_mine:
                st.markdown("**종료된 상품** (자동 비공개 처리됨)")
                for item in ended_mine:
                    st.markdown(
                        f"~~{item['item_name']}~~ — "
                        f"{status_map.get(item['status'],'')} | "
                        f"시도 {item['spin_count']}회"
                    )

            st.markdown("---")
            st.markdown("**➕ 새 상품 등록**")
            r_name    = st.text_input("상품 이름", placeholder="예: 스타벅스 아메리카노 기프티콘",
                                       key="r_name")
            r_desc    = st.text_area("상품 설명", placeholder="상태, 브랜드 등 간단히 적어주세요",
                                      key="r_desc")

            st.markdown("**연락처** (당첨자가 연락할 방법)")
            r_contact, r_contact_err = _contact_input("roulette_reg")

            r_img = st.text_input("이미지 URL (선택)", placeholder="https://...",
                                   key="r_img")

            if st.button("등록", use_container_width=True, key="roulette_reg_btn"):
                errs = []
                if not r_name.strip():
                    errs.append("상품 이름을 입력해 주세요.")
                if r_contact_err or not r_contact:
                    errs.append(r_contact_err or "연락처를 입력해 주세요.")
                if temp < 50:
                    errs.append(f"매너 온도 50° 이상만 등록 가능 (현재 {temp}°)")

                if errs:
                    for e in errs: st.error(e)
                else:
                    register_item(uid, uname, temp, r_name.strip(),
                                  r_desc.strip(), r_contact, r_img.strip())
                    st.success("상품이 등록됐습니다!")
                    st.rerun()
