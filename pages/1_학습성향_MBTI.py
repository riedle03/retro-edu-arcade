import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="학습성향 MBTI", page_icon="🧠")
KST = ZoneInfo("Asia/Seoul")

# 스타일
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
html, body, [class*="block-container"]{ background:#0f172a; color:#e5e7eb; }
h1,h2,h3{ font-family:'Press Start 2P', system-ui, -apple-system, Segoe UI, Roboto, 'Noto Sans KR', sans-serif; letter-spacing:1px; }
.retro-card{ border:4px solid #22d3ee; border-radius:12px; padding:18px; background:linear-gradient(180deg,#0b1220,#111827); box-shadow:0 0 0 4px #0b1220, inset 0 0 24px rgba(34,211,238,.25); }
.small{ font-size:12px; color:#94a3b8; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 8비트 학습 성향 진단 (MBTI)")

# 문항
QUESTIONS = {
    "EI": [
        ("여럿이 함께 공부하면 에너지가 난다.", False),
        ("발표/토론이 기대된다.", False),
        ("혼자 공부가 더 편하고 집중이 잘 된다.", True),
    ],
    "SN": [
        ("개념보다 예시/사례부터 보면 이해가 된다.", False),
        ("세부 절차를 순서대로 따라 배우는 편이다.", False),
        ("아이디어 확장/상상을 즐긴다.", True),
    ],
    "TF": [
        ("정답/근거가 분명한 문제가 좋다.", False),
        ("사람의 감정/관계도 중요하다.", True),
        ("의사결정에 데이터/논리를 우선한다.", False),
    ],
    "JP": [
        ("플래너로 일정 관리하고 계획대로 진행한다.", False),
        ("마감 직전 몰입이 효율적일 때가 많다.", True),
        ("계획이 바뀌어도 즉석에서 잘 대응한다.", True),
    ],
}
CHOICES = ["매우 그렇다 (+2)", "그렇다 (+1)", "보통 (0)", "아니다 (-1)", "전혀 아니다 (-2)"]
SCALE = {CHOICES[0]:2, CHOICES[1]:1, CHOICES[2]:0, CHOICES[3]:-1, CHOICES[4]:-2}

if "answers" not in st.session_state: st.session_state.answers = {}
if "result" not in st.session_state: st.session_state.result = None

st.markdown("<div class='retro-card'>아래 문항에 평소의 나와 가장 가까운 선택을 고르세요.</div>", unsafe_allow_html=True)

total_items = sum(len(v) for v in QUESTIONS.values())
answered = sum(1 for k in st.session_state.answers)
st.progress(answered / total_items if total_items else 0, text=f"{answered}/{total_items} 완료")

qnum = 0
for axis, items in QUESTIONS.items():
    st.subheader(f"🎯 {axis}")
    for i, (q, rev) in enumerate(items, start=1):
        qnum += 1
        key = (axis, i)
        st.session_state.answers[key] = st.radio(
            f"Q{qnum:02d}. {q}",
            CHOICES,
            index=2 if key not in st.session_state.answers else CHOICES.index(st.session_state.answers[key]),
            horizontal=True,
            key=f"radio-{axis}-{i}"
        )

def score_mbti(answers):
    raw = {"EI":0,"SN":0,"TF":0,"JP":0}
    for axis, items in QUESTIONS.items():
        for i, (_q, rev) in enumerate(items, start=1):
            val = SCALE[answers.get((axis,i), CHOICES[2])]
            if rev: val = -val
            raw[axis] += val
    mbti = ("E" if raw["EI"]>=0 else "I") + ("S" if raw["SN"]>=0 else "N") + ("T" if raw["TF"]>=0 else "F") + ("J" if raw["JP"]>=0 else "P")
    return mbti, raw

LEARNING_PROFILES = {
    "ISTJ": {"label":"체계적 실천가","tips":["단원 체크리스트","예제→변형→서술형","오답 원인 기록"]},
    "ENFP": {"label":"아이디어 점프러","tips":["프로젝트 연결","할 일 3개 제한","5분 규칙으로 시작"]},
    # 필요 시 나머지 유형 추가
}

col1, col2 = st.columns(2)
with col1:
    if st.button("🧮 결과 계산", type="primary"):
        mbti, raw = score_mbti(st.session_state.answers)
        st.session_state.result = {"mbti": mbti, "raw": raw, "at": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")}
with col2:
    if st.button("🔁 초기화"):
        st.session_state.answers = {}
        st.session_state.result = None
        st.experimental_rerun()

if st.session_state.result:
    mbti = st.session_state.result["mbti"]
    raw = st.session_state.result["raw"]
    prof = LEARNING_PROFILES.get(mbti, {"label":"맞춤 프로필","tips":["핵심 개념 정리","오답 원인 기록","주1회 메타인지 점검"]})
    st.success(f"🧠 결과: {mbti} · E/I {raw['EI']:+} · S/N {raw['SN']:+} · T/F {raw['TF']:+} · J/P {raw['JP']:+}")
    st.markdown("### 🔧 공부 팁")
    for t in prof["tips"]:
        st.markdown(f"- {t}")
else:
    st.info("‘🧮 결과 계산’을 누르면 MBTI 유형과 팁이 표시됩니다.")

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
