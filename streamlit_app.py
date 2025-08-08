import streamlit as st

st.set_page_config(page_title="Retro Class Tools", page_icon="🕹️")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
html, body, [class*="block-container"]{ background:#0f172a; color:#e5e7eb; }
h1,h2,h3{ font-family:'Press Start 2P', system-ui, -apple-system, Segoe UI, Roboto, 'Noto Sans KR', sans-serif; letter-spacing:1px; }
.card{ border:4px solid #22d3ee; border-radius:14px; padding:18px; background:linear-gradient(180deg,#0b1220,#111827); box-shadow:0 0 0 4px #0b1220, inset 0 0 24px rgba(34,211,238,.25); }
a{text-decoration:none;}
.small{ font-size:12px; color:#94a3b8; }
</style>
""", unsafe_allow_html=True)

st.title("🕹️ Retro Class Tools")
st.markdown("<p class='small'>레트로 감성 학급 도구 3종 – 좌측 사이드바 또는 아래 링크로 이동하세요.</p>", unsafe_allow_html=True)

st.markdown("<div class='card'><b>페이지 바로가기</b></div>", unsafe_allow_html=True)
st.page_link("pages/1_학습성향_MB_TI.py", label="🧠 학습성향 MBTI", icon="🧠")
st.page_link("pages/2_역할_룰렛.py", label="🎰 픽셀 레트로 역할 룰렛", icon="🎰")
st.page_link("pages/3_디지털_칭찬_상자.py", label="🌟 디지털 칭찬 상자+", icon="🌟")

# 푸터 (항상 추가)
st.markdown(
    """
    <hr style="margin-top:50px; margin-bottom:10px; border: 1px solid #334155;">
    <div style='text-align: center; font-size: 12px; color: #94a3b8;'>
        © 2025 이대형. All rights reserved.<br>
        <a href="https://aicreatorz.netlify.app/" target="_blank" style="color:#22d3ee; text-decoration: none;">
            https://aicreatorz.netlify.app/
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
