"""wishlist_page.py — 편의점 파티 생성 + 룰렛 시스템"""

import streamlit as st
import streamlit.components.v1 as components
from cvs_store      import create_party as cvs_create
from roulette_store import (register_item, get_active_items, get_my_items,
                             get_item, spin, has_spun, remove_item)
from rating_store   import get_temperature
from notification_store import push

CSS = """
<style>
.tab-section-title{font-size:1.1rem;font-weight:700;color:#1a1a1a;
  margin-bottom:1rem;border-bottom:2px solid #E5E7EB;padding-bottom:.5rem;}
.roulette-card{border:1.5px solid #E5E7EB;border-radius:14px;
  padding:1rem 1.2rem;margin-bottom:.8rem;background:#FAFAFA;
  display:flex;gap:1rem;align-items:flex-start;}
.roulette-card-img{width:80px;height:80px;border-radius:10px;object-fit:cover;
  background:linear-gradient(135deg,#EEF4FF,#DBEAFE);flex-shrink:0;
  display:flex;align-items:center;justify-content:center;font-size:2rem;}
.roulette-info{flex:1;}
.roulette-name{font-weight:700;color:#1a1a1a;font-size:.95rem;margin-bottom:.2rem;}
.roulette-desc{font-size:.78rem;color:#6B7280;margin-bottom:.3rem;}
.roulette-owner{font-size:.72rem;color:#9CA3AF;}
.roulette-prob{font-size:.72rem;font-weight:700;color:#3B82F6;
  background:#EFF6FF;padding:.15rem .5rem;border-radius:20px;}
.cvs-my-party{border:1.5px solid #DBEAFE;border-radius:14px;
  padding:.9rem 1.1rem;margin-bottom:.8rem;background:#F0F7FF;}
</style>
"""

ROULETTE_HTML = """<!DOCTYPE html><html><head>
<meta charset="utf-8">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:transparent;display:flex;flex-direction:column;
  align-items:center;justify-content:center;height:220px;font-family:'DM Sans',sans-serif;}
#wheel-wrap{position:relative;width:180px;height:180px;}
canvas#wheel{border-radius:50%;box-shadow:0 4px 20px rgba(0,0,0,.15);}
#pointer{position:absolute;top:-16px;left:50%;transform:translateX(-50%);
  font-size:1.6rem;line-height:1;}
#result{margin-top:12px;font-size:1rem;font-weight:700;color:#1a1a1a;
  min-height:24px;text-align:center;}
</style>
</head><body>
<div id="wheel-wrap">
  <div id="pointer">▼</div>
  <canvas id="wheel" width="180" height="180"></canvas>
</div>
<div id="result"></div>
<script>
var SEGMENTS=['🎁 당첨!','😢 꽝','😅 꽝','🥲 꽝','💀 꽝',
              '😵 꽝','🤦 꽝','😭 꽝','🙈 꽝','😤 꽝',
              '🫠 꽝','🤡 꽝','😤 꽝','😩 꽝','🤯 꽝',
              '😾 꽝','🥴 꽝','😬 꽝','🫥 꽝','🫣 꽝'];
var COLORS=['#3B82F6','#EF4444','#F59E0B','#10B981','#8B5CF6',
            '#EC4899','#14B8A6','#F97316','#6366F1','#84CC16',
            '#EF4444','#3B82F6','#F59E0B','#10B981','#8B5CF6',
            '#EC4899','#14B8A6','#F97316','#6366F1','#84CC16'];
var n=SEGMENTS.length;
var arc=2*Math.PI/n;
var canvas=document.getElementById('wheel');
var ctx=canvas.getContext('2d');
var cx=90,cy=90,r=85;
var spinning=false;
var targetAngle=0;
var currentAngle=0;

function draw(angle){
  ctx.clearRect(0,0,180,180);
  for(var i=0;i<n;i++){
    var start=angle+i*arc;
    ctx.beginPath();
    ctx.moveTo(cx,cy);
    ctx.arc(cx,cy,r,start,start+arc);
    ctx.closePath();
    ctx.fillStyle=COLORS[i];
    ctx.fill();
    ctx.save();
    ctx.translate(cx,cy);
    ctx.rotate(start+arc/2);
    ctx.fillStyle='#fff';
    ctx.font='bold 11px sans-serif';
    ctx.textAlign='right';
    ctx.fillText(SEGMENTS[i],r-6,4);
    ctx.restore();
  }
  // 중심원
  ctx.beginPath();
  ctx.arc(cx,cy,18,0,2*Math.PI);
  ctx.fillStyle='#fff';
  ctx.fill();
  ctx.strokeStyle='#E5E7EB';
  ctx.lineWidth=2;
  ctx.stroke();
}

draw(0);

window.addEventListener('message',function(e){
  if(!e.data||e.data.type!=='SPIN') return;
  if(spinning) return;
  spinning=true;
  document.getElementById('result').innerText='🎰 돌아가는 중...';
  var isWin=e.data.isWin;
  // 당첨이면 첫 칸(index 0)에 멈춤, 꽝이면 1~n-1 랜덤
  var stopIdx=isWin?0:Math.floor(Math.random()*(n-1))+1;
  var spins=5+Math.random()*3; // 5~8바퀴
  var finalAngle=-(spins*2*Math.PI + stopIdx*arc + arc/2);
  var startTime=null;
  var duration=4000;
  function animate(ts){
    if(!startTime) startTime=ts;
    var progress=Math.min((ts-startTime)/duration,1);
    // easeOutQuart
    var ease=1-Math.pow(1-progress,4);
    currentAngle=finalAngle*ease;
    draw(currentAngle);
    if(progress<1){
      requestAnimationFrame(animate);
    } else {
      spinning=false;
      var msgs=isWin?
        ['🎉 축하합니다! 당첨!','🥳 오늘 운이 터졌네요!','🏆 대박! 당첨됐습니다!']:
        ['😢 아쉽네요, 꽝!','💀 오늘은 운이 없어요...','🤡 다음엔 될 거예요!',
         '😭 꽝입니다... 세상이 야속하네요','🫠 녹아내리는 기분...'];
      var msg=msgs[Math.floor(Math.random()*msgs.length)];
      document.getElementById('result').innerText=msg;
      window.parent.postMessage({type:'SPIN_DONE',isWin:isWin},'*');
    }
  }
  requestAnimationFrame(animate);
});
</script>
</body></html>"""


def _map_pick_html(lat=37.5665, lng=126.9780):
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{{margin:0;padding:0;width:100%;height:280px;}}
#info{{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.65);color:#fff;font-size:.75rem;
  padding:4px 14px;border-radius:20px;z-index:999;white-space:nowrap;}}</style>
</head><body><div id="map"></div><div id="info">지도를 클릭해 집합 위치를 선택하세요</div>
<script>
var map=L.map('map').setView([{lat},{lng}],15);
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


def render_wishlist_page():
    st.markdown(CSS, unsafe_allow_html=True)

    user      = st.session_state.get("user", {})
    uid       = user.get("user_id", "")
    uname     = user.get("name", "")
    is_logged = "user" in st.session_state
    temp      = get_temperature(uid) if is_logged else 0

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
            # 파티 생성
            with st.expander("➕ 새 파티 만들기", expanded=False):
                with st.form("cvs_create_form"):
                    depart_time = st.text_input("출발 시간 (예: 18:30)")
                    contact     = st.text_input("연락처 (카카오톡 ID / 전화번호)")
                    account     = st.text_input("입금 계좌 (은행 + 번호)")
                    ok = st.form_submit_button("파티 생성", use_container_width=True)

                if ok:
                    if not depart_time or not contact or not account:
                        st.warning("모든 항목을 입력해 주세요.")
                    else:
                        pid = cvs_create(uid, uname, depart_time, contact, account)
                        st.success(f"파티가 생성됐습니다! (ID: {pid})")
                        st.rerun()

            st.divider()

            # 내 파티 관리
            from cvs_store import (get_parties_by_user, get_party,
                                    confirm_order, depart_party,
                                    set_gather_location, delete_party)

            my_parties = get_parties_by_user(uid)
            if my_parties:
                st.markdown("**📋 내 파티 목록**")
                for p in my_parties:
                    is_creator = p["creator_id"] == uid
                    status_map = {"waiting":"🟡 대기중","departed":"🚀 출발","arrived":"📍 집합완료"}
                    status_txt = status_map.get(p["status"], p["status"])

                    with st.expander(
                        f"{'[파티장]' if is_creator else '[참여]'} "
                        f"{p['creator_name']} · {p['depart_time']} · {status_txt}",
                        expanded=False):

                        st.markdown(f"""
                        <div class="cvs-my-party">
                          <b>출발: {p['depart_time']}</b> | 상태: {status_txt}<br>
                          📞 {p['contact']} | 💳 {p['account']}
                        </div>""", unsafe_allow_html=True)

                        # 주문 목록
                        orders = p["orders"]
                        if orders:
                            st.markdown("**주문 목록**")
                            for idx, o in enumerate(orders):
                                paid_txt = ("✅ 확정" if o["confirmed"]
                                            else "⏳ 입금대기")
                                st.markdown(f"""
                                <div class="cvs-order-row">
                                  <span>👤 {o['name']}</span>
                                  <span>{o['item_label']} × {o['qty']}</span>
                                  <span>{o['qty']*o['price']:,}원</span>
                                  <span class="{'cvs-paid' if o['confirmed'] else 'cvs-unpaid'}">
                                    {paid_txt}</span>
                                </div>""", unsafe_allow_html=True)

                                if is_creator and not o["confirmed"]:
                                    if st.button(f"✅ 합류 확인 (#{idx+1})",
                                                 key=f"cvs_confirm_{p['party_id']}_{idx}"):
                                        confirm_order(p["party_id"], idx)
                                        push(o["user_id"], "pot_joined",
                                             f"'{o['item_label']}' 입금이 확인됐습니다. 파티에 합류됐어요!")
                                        st.rerun()
                        else:
                            st.caption("아직 주문이 없습니다.")

                        # 파티장 전용 버튼
                        if is_creator:
                            if p["status"] == "waiting":
                                if st.button("🚀 파티 출발!", key=f"cvs_depart_{p['party_id']}",
                                             use_container_width=True):
                                    depart_party(p["party_id"])
                                    members = list({o["user_id"] for o in orders})
                                    from notification_store import push_all as _pa
                                    _pa(members, "pot_joined",
                                        f"{uname}의 편의점 파티가 출발했습니다!")
                                    st.success("출발!"); st.rerun()

                            elif p["status"] == "departed":
                                st.markdown("**📍 집합 위치 전송**")
                                gather_loc  = st.text_input("집합 장소 이름",
                                                             key=f"gloc_{p['party_id']}",
                                                             placeholder="예: 편의점 앞 공원 벤치")
                                gather_lat  = st.number_input("위도",  value=37.5665,
                                                               format="%.5f", key=f"glat_{p['party_id']}")
                                gather_lng  = st.number_input("경도", value=126.9780,
                                                               format="%.5f", key=f"glng_{p['party_id']}")
                                st.caption("지도 클릭 후 좌표를 위에 입력하세요.")
                                components.html(_map_pick_html(), height=300, scrolling=False)

                                if st.button("📍 위치 전송", key=f"cvs_gather_{p['party_id']}",
                                             use_container_width=True):
                                    if gather_loc.strip():
                                        set_gather_location(p["party_id"], gather_loc,
                                                            gather_lat, gather_lng)
                                        members = list({o["user_id"] for o in orders})
                                        from notification_store import push_all as _pa
                                        _pa(members, "pot_joined",
                                            f"집합 위치: {gather_loc} "
                                            f"(위도 {gather_lat:.4f}, 경도 {gather_lng:.4f})")
                                        st.success("위치 전송 완료!"); st.rerun()
                                    else:
                                        st.warning("장소 이름을 입력해 주세요.")

                            elif p["status"] == "arrived" and p.get("gather_location"):
                                st.success(f"📍 집합 위치: {p['gather_location']}")
                                components.html(_map_view_inline(
                                    p["gather_lat"], p["gather_lng"], p["gather_location"]),
                                    height=260, scrolling=False)


    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — 룰렛 시스템
    # ══════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown('<div class="tab-section-title">🎰 룰렛 시스템</div>',
                    unsafe_allow_html=True)

        if not is_logged:
            st.info("로그인이 필요합니다.")
            return

        # 룰렛 돌리기 결과 상태
        if "roulette_result" not in st.session_state:
            st.session_state.roulette_result = None
        if "roulette_spin_rid" not in st.session_state:
            st.session_state.roulette_spin_rid = None

        rt1, rt2 = st.tabs(["🎁 상품 목록", "📦 내 상품 관리"])

        # ── 상품 목록 탭 ─────────────────────────────────────────────────
        with rt1:
            active_items = get_active_items(exclude_user_id=uid)

            if not active_items:
                st.info("등록된 상품이 없습니다. 내 상품 관리에서 등록해 보세요!")
            else:
                for item in active_items:
                    rid   = item["roulette_id"]
                    prob  = max(1, 20 - item["spin_count"])
                    spun  = has_spun(rid, uid)
                    won   = item["status"] == "won"

                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        if item.get("image_url"):
                            st.image(item["image_url"], width=80)
                        else:
                            st.markdown('<div class="roulette-card-img">🎁</div>',
                                        unsafe_allow_html=True)
                    with col_info:
                        st.markdown(f"**{item['item_name']}**")
                        st.caption(item["item_desc"])
                        st.markdown(f"등록자: {item['owner_name']} "
                                    f"| 현재 확률: **1/{prob}**")
                        if won:
                            st.error("이미 당첨된 상품입니다.")
                        elif spun:
                            st.warning("이미 참여한 상품입니다.")
                        elif temp < 50:
                            st.warning(f"매너 온도 50° 이상만 참여 가능 (현재 {temp}°)")
                        else:
                            if st.button(f"🎰 룰렛 돌리기", key=f"spin_{rid}"):
                                is_win, msg = spin(rid, uid)
                                st.session_state.roulette_result   = (is_win, msg, rid)
                                st.session_state.roulette_spin_rid = rid
                                st.rerun()

                    st.divider()

            # 룰렛 애니메이션 + 결과
            if st.session_state.roulette_result:
                is_win, msg, rid = st.session_state.roulette_result
                item = get_item(rid)

                st.markdown("---")
                st.markdown("### 🎰 룰렛 결과")
                components.html(ROULETTE_HTML, height=240, scrolling=False)

                st.markdown(f"""
                <script>
                setTimeout(function(){{
                  var frames=document.querySelectorAll('iframe');
                  for(var f of frames){{
                    try{{
                      f.contentWindow.postMessage({{type:'SPIN',isWin:{'true' if is_win else 'false'}}},'*');
                    }}catch(e){{}}
                  }}
                }}, 300);
                </script>""", unsafe_allow_html=True)

                if is_win and item:
                    st.success(f"🎉 **당첨!** {item['item_name']}")
                    st.info(f"📞 당첨 연락처: **{item['contact']}**\n\n"
                            f"등록자({item['owner_name']})에게 연락해 상품을 수령하세요!")
                    push(item["owner_id"], "pot_ended",
                         f"{uname}님이 '{item['item_name']}' 룰렛에 당첨됐습니다! "
                         f"연락을 기다려 주세요.")
                else:
                    prob_left = max(1, 20 - (item["spin_count"] if item else 20))
                    st.warning(f"😢 꽝! 다음 확률: **1/{prob_left}**")

                if st.button("확인", key="roulette_confirm"):
                    st.session_state.roulette_result   = None
                    st.session_state.roulette_spin_rid = None
                    st.rerun()

        # ── 내 상품 관리 탭 ───────────────────────────────────────────────
        with rt2:
            st.markdown("**내 등록 상품**")
            my_items = get_my_items(uid)
            for item in my_items:
                status_map = {"active":"🟢 등록중","won":"🏆 당첨됨","removed":"❌ 삭제됨"}
                st.markdown(f"**{item['item_name']}** — {status_map.get(item['status'],'')} "
                             f"| 시도 {item['spin_count']}회")
                st.caption(item["item_desc"])
                if item["status"] == "active":
                    if st.button("삭제", key=f"rm_roulette_{item['roulette_id']}"):
                        remove_item(item["roulette_id"], uid)
                        st.rerun()
                st.divider()

            st.markdown("**➕ 새 상품 등록**")
            with st.form("roulette_register"):
                r_name    = st.text_input("상품 이름", placeholder="예: 스타벅스 아메리카노 기프티콘")
                r_desc    = st.text_area("상품 설명", placeholder="상태, 브랜드 등 간단히 적어주세요")
                r_contact = st.text_input("연락처", placeholder="당첨자가 연락할 방법")
                r_img     = st.text_input("이미지 URL (선택)", placeholder="https://...")
                r_ok      = st.form_submit_button("등록", use_container_width=True)

            if r_ok:
                if not r_name or not r_contact:
                    st.warning("이름과 연락처는 필수입니다.")
                elif temp < 50:
                    st.warning(f"매너 온도 50° 이상만 등록 가능 (현재 {temp}°)")
                else:
                    register_item(uid, uname, temp, r_name, r_desc, r_contact, r_img)
                    st.success("상품이 등록됐습니다!")
                    st.rerun()


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
</script></body></html>"""
