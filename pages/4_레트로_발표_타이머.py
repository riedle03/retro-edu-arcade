# 레트로 발표 타이머 (수정된 버전)
import time
import os
import streamlit as st

st.set_page_config(page_title="레트로 발표 타이머", page_icon="🕹️", layout="wide")

# ==== Assets (optional) ====
# assets 폴더가 실제 존재하지 않을 경우를 대비한 예외 처리
try:
    # __file__ 변수가 없는 환경(예: 일부 클라우드 노트북)을 위한 처리
    base_path = os.path.dirname(__file__) if "__file__" in locals() else "."
    ASSETS = os.path.join(base_path, "assets")
    SUCCESS_SOUND = os.path.join(ASSETS, "success1.mp3")
    if not os.path.exists(SUCCESS_SOUND):
        SUCCESS_SOUND = None
except Exception:
    SUCCESS_SOUND = None


# ==== CSS ====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
:root{ --green:#16a34a; --yellow:#f59e0b; --red:#dc2626; --panel:#0b1220; --text:#e5e7eb; --aqua:#22d3ee; }
html, body, [class*="css"]{ background:#0f172a; color:var(--text); }
section.main>div{ padding:8px 10px 96px 10px; }

.crt-wrap{ position:relative; width:100%; height:calc(100vh - 32px); display:flex; align-items:center; justify-content:center; }
.crt{
  position:relative; width:min(96vw,1400px); height:min(84vh,820px);
  border-radius:22px; overflow:hidden; background:#000;
  box-shadow:0 0 0 6px #0b1220,0 0 28px rgba(34,211,238,.25), inset 0 0 60px rgba(0,0,0,.6);
  border:4px solid var(--aqua);
}
.crt:after{
  content:""; position:absolute; inset:0; pointer-events:none;
  background:repeating-linear-gradient(0deg, rgba(255,255,255,.035) 0px, rgba(255,255,255,.035) 1px, transparent 2px, transparent 3px);
  opacity:.6; mix-blend-mode:overlay;
}
.crt:before{ content:""; position:absolute; inset:0; pointer-events:none; box-shadow: inset 0 0 140px rgba(34,211,238,.08); }

.screen{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:24px;
         font-family:'Press Start 2P', monospace; text-align:center; }
.time{ font-size:clamp(48px,16vw,160px); font-weight:900; letter-spacing:.04em; color:#fff;
       text-shadow:0 0 10px rgba(0,0,0,.35), 0 0 18px rgba(34,211,238,.18); }
.urgent{ animation: blink 1s infinite; }
@keyframes blink{ 0%{opacity:1} 50%{opacity:.65} 100%{opacity:1} }
.sub{ font-size:clamp(12px,2.5vw,24px); color:rgba(255,255,255,.92); text-shadow:0 1px 6px rgba(0,0,0,.35); }

#retro-footer{
  position:fixed; left:0; right:0; bottom:0; z-index:2; background:rgba(2,6,23,.9);
  border-top:1px solid #334155; backdrop-filter:blur(6px); padding:6px 10px;
  text-align:center; font-size:11px; color:#94a3b8; font-family:'Press Start 2P', monospace;
}
</style>
""", unsafe_allow_html=True)

# ==== State (상태 관리) ====
ss = st.session_state
defaults = {
    "duration_sec": 0, "end_ts": None, "paused": False,
    "paused_remaining": 0, "running": False, "ended": False,
    "play_sound": True, "minutes": 3, "tick_ms": 200,
}
for k, v in defaults.items():
    if k not in ss: ss[k] = v

# ==== Helpers (도우미 함수) ====
def remaining_secs() -> float:
    """남은 시간을 초 단위로 계산하여 반환합니다."""
    if ss.running and not ss.paused and ss.end_ts is not None:
        return max(0.0, ss.end_ts - time.time())
    if ss.paused:
        return max(0.0, ss.paused_remaining)
    if ss.ended:
        return 0.0
    # 타이머 시작 전에는 설정된 시간을 표시합니다.
    return ss.minutes * 60

def fmt(sec: float) -> str:
    """초를 '분:초' (MM:SS) 형식의 문자열로 변환합니다."""
    s = max(0, int(round(sec)))
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"

def pick_bg(rem: float, total: float) -> str:
    """남은 시간에 따라 배경색을 결정합니다."""
    if not ss.running or total <= 0: return "var(--green)" # 시작 전 녹색
    ratio = rem / total
    if ratio > 0.5: return "var(--green)"
    if ratio > 0.2: return "var(--yellow)"
    return "var(--red)"

# ==== Callbacks (버튼 클릭 시 실행될 함수) ====
def cb_preset(mins:int):
    """프리셋 버튼 클릭 시 분을 설정합니다."""
    ss.minutes = mins
    # 실행 중이 아닐 때만 리셋
    if not ss.running:
        cb_reset()

def cb_start():
    """시작/재시작 버튼 클릭 시 타이머를 초기화하고 시작합니다."""
    ss.duration_sec = ss.minutes * 60
    ss.end_ts = time.time() + ss.duration_sec
    ss.running = True
    ss.paused = False
    ss.ended = False
    ss.play_sound = True # 재시작 시 효과음 재생 가능하도록 설정

def cb_toggle():
    """일시정지/재개 버튼 클릭 시 상태를 전환합니다."""
    if not ss.running: return # 타이머가 실행 중이 아닐 때는 아무것도 하지 않음
    if not ss.paused:
        ss.paused_remaining = remaining_secs()
        ss.paused = True
    else:
        ss.end_ts = time.time() + ss.paused_remaining
        ss.paused = False

def cb_reset():
    """리셋 버튼 클릭 시 모든 상태를 초기화합니다."""
    ss.running = False
    ss.paused = False
    ss.ended = False
    ss.end_ts = None
    ss.duration_sec = ss.minutes * 60
    ss.paused_remaining = 0

# ==== Sidebar Controls (사이드바 UI) ====
with st.sidebar:
    st.markdown("## 🕹️ 레트로 발표 타이머")
    ss.minutes = st.number_input("발표 시간(분)", min_value=1, max_value=180, step=1, value=ss.minutes)

    ss.tick_ms = st.selectbox("갱신 주기", options=[100, 200, 500, 1000],
                              index=[100, 200, 500, 1000].index(ss.tick_ms),
                              format_func=lambda x: f"{x} ms")

    st.write("프리셋")
    c1, c2, c3 = st.columns(3)
    c1.button("3분", on_click=cb_preset, args=(3,), use_container_width=True)
    c2.button("5분", on_click=cb_preset, args=(5,), use_container_width=True)
    c3.button("10분", on_click=cb_preset, args=(10,), use_container_width=True)

    st.divider()
    st.button("▶ 시작/재시작", use_container_width=True, on_click=cb_start)
    st.button("⏸ 일시정지/재개", use_container_width=True, on_click=cb_toggle)
    st.button("⟲ 리셋", use_container_width=True, on_click=cb_reset)

    st.toggle("종료 효과음", value=ss.play_sound, key="play_sound_toggle", help="0초가 되면 효과음을 재생합니다.")
    ss.play_sound = ss.play_sound_toggle

# ==== 상태 계산 및 업데이트 ====
rem = remaining_secs()
is_running_now = ss.running and not ss.paused

# 타이머가 실행 중일 때 시간이 다 되면 상태 변경
if is_running_now and rem <= 0:
    ss.running = False
    ss.ended = True
    is_running_now = False # 현재 스크립트 실행 주기 내에서 상태를 즉시 반영
    rem = 0

# ==== Main Screen (메인 화면 렌더링) ====
bg = pick_bg(rem, ss.duration_sec)
if is_running_now:
    status = "진행 중"
elif ss.paused:
    status = "일시정지"
elif ss.ended:
    status = "완료!"
else:
    status = "대기 중"

urgent_class = " urgent" if (is_running_now and rem <= 10) else ""
time_text = fmt(rem)

st.markdown(f"""
<div class="crt-wrap">
  <div class="crt">
    <div class="screen" style="background:{bg};">
      <div class="time{urgent_class}">{time_text}</div>
      <div class="sub">{status}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ==== Sound (효과음 재생) ====
# ss.ended 상태가 되고, ss.play_sound가 True일 때 한 번만 재생
if ss.ended and ss.play_sound:
    if SUCCESS_SOUND and os.path.exists(SUCCESS_SOUND):
        with open(SUCCESS_SOUND, "rb") as f:
            st.audio(f.read(), format="audio/mp3", start_time=0)
    ss.play_sound = False # 소리가 반복 재생되지 않도록 플래그를 변경

# ==== Footer (하단 푸터) ====
st.markdown("<div id='retro-footer'>© © 2025 Lee Daehyoung. All rights reserved. • Press Start 2P & CRT Style</div>", unsafe_allow_html=True)


# ==== 다음 업데이트 예약 (스크립트의 가장 마지막에 위치) ====
# 타이머가 '실행 중' 상태일 때만 지정된 시간 후 재실행을 예약합니다.
# 이 로직이 화면 렌더링 코드보다 뒤에 있어, UI가 먼저 갱신되고 다음 업데이트가 예약됩니다.
if is_running_now:
    time.sleep(ss.tick_ms / 1000)
    st.rerun()