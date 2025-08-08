import streamlit as st
import random
import pandas as pd
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

st.set_page_config(page_title="디지털 칭찬 상자+", page_icon="🌟")
KST = ZoneInfo("Asia/Seoul")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Press+Start 2P&display=swap" rel="stylesheet">
<style>
html, body, [class*="block-container"]{ background:#0f172a; color:#e5e7eb; }
h1,h2,h3,.retro-title{ font-family:'Press Start 2P', system-ui, -apple-system, Segoe UI, Roboto, 'Noto Sans KR', sans-serif; letter-spacing:1px; }
.retro-card{ border:4px solid #22d3ee; border-radius:14px; padding:18px; background:linear-gradient(180deg,#0b1220,#111827); box-shadow:0 0 0 4px #0b1220, inset 0 0 24px rgba(34,211,238,.25); }
.crt{ position:relative; background:#0b1b13; border:6px solid #16a34a; border-radius:12px; padding:24px; min-height:160px; display:flex; align-items:center; justify-content:center; color:#a7f3d0; text-shadow:0 0 6px rgba(34,197,94,0.6); font-family:'Press Start 2P', monospace; line-height:1.6; text-align:center; overflow:hidden; }
.crt:before{ content:""; position:absolute; inset:0; background:repeating-linear-gradient(to bottom, rgba(255,255,255,0.06) 0px, rgba(255,255,255,0.06) 1px, transparent 2px, transparent 4px); pointer-events:none; mix-blend-mode:overlay; }
.cursor{ display:inline-block; margin-left:6px; width:10px; height:1em; background:#a7f3d0; animation:blink 1s steps(1) infinite; }
.small{ font-size:12px; color:#94a3b8; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='retro-title' style='font-size:26px;'>🌟 디지털 칭찬 상자+</div>", unsafe_allow_html=True)
st.markdown("<p class='small'>학생을 입력하지 않아도 칭찬 문구만 랜덤으로 표시됩니다. (학생은 중복 등장하지 않음)</p>", unsafe_allow_html=True)

# 상태
if "compliments" not in st.session_state:
    st.session_state.compliments = [
        "오늘도 최선을 다했어요! 멋져요!","어제보다 한 걸음 더 성장했네요 👏","도전하는 마음, 그 자체로 최고예요!",
        "친구를 배려하는 모습이 정말 인상적이었어요 😊","실수는 배움의 시작! 아주 잘했어요!","집중력이 대단해요—계속 이렇게만 가자!",
        "질문 덕분에 수업이 더 풍성해졌어요 💡","항상 웃는 얼굴로 수업에 참여해줘서 고마워요 😀","자신의 의견을 용기 있게 말한 점이 멋졌어요!",
        "배운 내용을 친구에게 설명해주는 모습이 최고예요!","꾸준히 노력하는 모습이 감동이에요 ✨","책임감 있게 맡은 일을 끝내줘서 고마워요",
        "새로운 아이디어를 제안해줘서 수업이 재미있었어요","어려운 문제를 끝까지 포기하지 않고 풀어냈군요!","다른 친구의 발표를 경청해줘서 고마워요",
        "준비물을 꼼꼼히 챙겨오는 모습이 보기 좋아요","집중해서 필기하는 모습이 인상적이었어요","토론에서 근거를 들어 의견을 말하는 게 훌륭했어요",
        "활발하게 참여해줘서 수업 분위기가 좋아졌어요","새로운 도전을 즐기는 용기가 멋져요","예의 바른 인사가 하루를 기분 좋게 만들었어요",
        "친구를 격려하는 따뜻한 말 한마디가 최고예요","수업 준비를 미리 해오는 성실함이 돋보여요","책을 열심히 읽는 모습이 보기 좋았어요",
        "협동심을 발휘해서 팀을 잘 이끌었어요","다른 친구의 실수를 이해해주는 마음이 아름다워요","조용히 하지만 꾸준히 노력하는 모습이 멋져요",
        "정리정돈을 잘해줘서 교실이 깔끔해졌어요","수업 자료를 잘 찾아와서 도움이 많이 됐어요","배운 것을 생활 속에서 실천하는 모습이 훌륭해요",
        "발표 때 목소리가 또렷하고 자신감 있었어요","작은 일에도 감사 인사를 해주는 마음이 예뻐요","수업 태도가 다른 친구들의 모범이 되고 있어요",
        "몰입해서 과제를 하는 모습이 대단했어요","수업 시간에 눈빛이 반짝였어요 ✨","주어진 시간을 잘 지켜서 훌륭했어요","다양한 관점을 제시해줘서 수업이 풍성해졌어요"
    ]
if "students" not in st.session_state: st.session_state.students = []
if "picked_students" not in st.session_state: st.session_state.picked_students = set()
if "last_display" not in st.session_state: st.session_state.last_display = "PRESS ▶ TO REVEAL PRAISE"
if "history" not in st.session_state: st.session_state.history = []

with st.expander("📝 학생 & 칭찬 문구 관리"):
    c1, c2 = st.columns(2)
    with c1:
        st.caption("학생 명단 (쉼표 또는 줄바꿈)")
        students_raw = st.text_area("학생 입력", height=150, value="\n".join(st.session_state.students) if st.session_state.students else "")
        if st.button("💾 학생 저장", type="primary"):
            lst = [x.strip() for x in students_raw.replace(",", "\n").split("\n") if x.strip()]
            st.session_state.students = lst
            st.session_state.picked_students = set()
            st.success(f"학생 {len(lst)}명 저장 완료! (중복 등장 방지)")
    with c2:
        st.caption("칭찬 문구 (쉼표 또는 줄바꿈)")
        compliments_raw = st.text_area("문구 입력", height=150, value="\n".join(st.session_state.compliments))
        if st.button("💾 문구 저장"):
            items = [x.strip() for x in compliments_raw.replace(",", "\n").split("\n") if x.strip()]
            if items:
                st.session_state.compliments = items
                st.success(f"문구 {len(items)}개 저장 완료!")

    colr1, colr2, colr3 = st.columns(3)
    with colr1:
        if st.button("🔄 학생 뽑힘 기록 초기화"):
            st.session_state.picked_students = set()
            st.success("모든 학생이 다시 추첨 대상입니다.")
    with colr2:
        if st.button("🧹 전체 기록 초기화"):
            st.session_state.history = []
            st.session_state.last_display = "PRESS ▶ TO REVEAL PRAISE"
            st.success("히스토리를 모두 비웠습니다.")
    with colr3:
        st.info(f"남은 학생 수: {max(0, len(st.session_state.students) - len(st.session_state.picked_students))}")

# 버튼 → 상태 업데이트 → CRT 출력
st.markdown("<div class='retro-card'>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1,1,1])
with c2:
    if st.button("▶ 오늘의 칭찬 주인공 뽑기", use_container_width=True):
        remaining = [s for s in st.session_state.students if s not in st.session_state.picked_students] if st.session_state.students else []
        if not st.session_state.compliments:
            st.warning("먼저 칭찬 문구를 저장해 주세요!")
        elif st.session_state.students and not remaining:
            st.warning("모든 학생이 이미 뽑혔습니다! (초기화 후 다시 시도)")
        else:
            student = random.choice(remaining) if remaining else None
            compliment = random.choice(st.session_state.compliments)
            display = f"{student} 님!\n{compliment}" if student else compliment
            st.session_state.last_display = display

            if student:
                st.session_state.picked_students.add(student)
            st.session_state.history.append({"시간": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"), "학생": student or "", "문구": compliment})

            # MP3만 재생
            assets_dir = Path(__file__).parent.parent / "assets"
            mp3_list = sorted([p for p in assets_dir.glob("*.mp3")]) if assets_dir.exists() else []
            if mp3_list:
                sfx_path = random.choice(mp3_list)
                b64 = base64.b64encode(sfx_path.read_bytes()).decode("utf-8")
                st.markdown(f"""<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></source></audio>""", unsafe_allow_html=True)
            else:
                st.info("💡 assets 폴더에 MP3 파일을 넣어주세요. (예: success1.mp3, coin.mp3, win.mp3)")

st.markdown(f"<div class='crt'>{st.session_state.last_display}<span class='cursor'></span></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.history:
    st.subheader("🗂 칭찬 기록")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)
    st.download_button("💾 기록 다운로드 (CSV)", df.to_csv(index=False).encode("utf-8-sig"), "praise_history.csv", "text/csv")

# 푸터
st.markdown("""
<hr style="margin-top:50px; margin-bottom:10px; border: 1px solid #334155;">
<div style='text-align: center; font-size: 12px; color: #94a3b8;'>
    © 2025 이대형. All rights reserved.<br>
    <a href="https://aicreatorz.netlify.app/" target="_blank" style="color:#22d3ee; text-decoration: none;">
        https://aicreatorz.netlify.app/
    </a>
</div>
""", unsafe_allow_html=True)
