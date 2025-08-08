# pages/5_레트로_자리_랜덤_배치.py
# 레트로 자리 랜덤 배치 (성별 색상 / 조 배지 / PNG 내보내기 / 씨드 설명)
import random, itertools, io, re, os
from typing import List, Dict, Optional
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# 멀티페이지에서는 홈에서 set_page_config를 이미 호출했을 수 있으므로 예외 처리
try:
    st.set_page_config(page_title="레트로 자리 랜덤 바꾸기", page_icon="🎲", layout="wide")
except Exception:
    pass

# ============================ Retro CSS ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
:root{ --bg:#0f172a; --panel:#111827; --aqua:#22d3ee; --lime:#16a34a; --text:#e5e7eb; }
html,body,[class*="css"] { background: var(--bg) !important; color: var(--text) !important; }
section.main>div { padding: 20px 28px 110px 28px; } /* footer 여백 */

.retro-title{
  font-family:'Press Start 2P', monospace; letter-spacing:1px; line-height:1.4;
  text-shadow:0 0 4px rgba(34,211,238,.6), 0 0 10px rgba(34,211,238,.25);
}

.retro-card{
  border:4px solid var(--aqua); border-radius:14px; padding:14px;
  background:linear-gradient(180deg,#0b1220,#111827);
  box-shadow:0 0 0 4px #0b1220, inset 0 0 24px rgba(34,211,238,.25);
}

.crt{ position:relative; overflow:hidden; border:6px solid var(--lime); border-radius:12px; }
.crt:after{
  content:""; position:absolute; inset:0;
  background:repeating-linear-gradient(0deg, rgba(255,255,255,.03) 0px, rgba(255,255,255,.03) 1px, transparent 2px, transparent 3px);
  pointer-events:none; mix-blend-mode:overlay; opacity:.7;
}

.seat {
  display:flex; align-items:center; justify-content:center; text-align:center;
  border:3px solid #0ea5e9; border-radius:12px; padding:8px; min-height:88px;
  font-weight:700;
  background:linear-gradient(180deg, #1e293b, #0b1220);
}
.seat.locked { border-color:#f59e0b; filter:saturate(.7) brightness(.9); }
.seat .nick{
  font-family:'Press Start 2P', monospace; font-size:11px; line-height:1.3;
  word-break:keep-all; color:#e2e8f0; text-shadow:0 0 6px rgba(0,0,0,.6);
}

/* 성별 색상 */
.male   { background:linear-gradient(180deg, #1f3b68, #0b1f3a); border-color:#38bdf8; }
.female { background:linear-gradient(180deg, #5a2f4f, #2a0f26); border-color:#f472b6; }
.neutral{ background:linear-gradient(180deg, #253247, #0b1220); }

/* 좌석 안 조 번호 배지 */
.seat .badge {
  position:absolute;
  top:6px; left:8px;
  font-size:10px; padding:2px 6px;
  border-radius:10px; border:1px solid #94a3b8;
  color:#e2e8f0; background:rgba(2,6,23,.6);
}

/* 안내문용 배지 */
.legend-pill{
  display:inline-block; font-size:12px; padding:3px 8px;
  border-radius:10px; border:1px solid #94a3b8; color:#e2e8f0;
  background:rgba(2,6,23,.5); margin-right:6px;
}
.small { font-size:12px; color:#a8b1c9;}

/* footer */
#retro-footer{position:fixed;left:0;right:0;bottom:0;z-index:9999;background:rgba(2,6,23,.9);
  border-top:1px solid #334155; backdrop-filter:blur(6px); padding:10px 12px;}
#retro-footer .inner{text-align:center;font-size:12px;color:#94a3b8;font-weight:500;}
#retro-footer a{color:#22d3ee;text-decoration:none;} #retro-footer a:hover{text-decoration:underline;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="retro-title">🎲 자리 랜덤 바꾸기</h1>', unsafe_allow_html=True)
st.caption("이름/성별/조 입력 → 행·열 설정 → [셔플]. 두 좌석 [선택]을 연속 클릭하면 서로 교환. 🔒고정은 셔플 제외.")

# ============================ State ============================
def init_state():
    ss = st.session_state
    if "rows" not in ss: ss.rows = 4            # 행(가로 줄 수)
    if "cols" not in ss: ss.cols = 4            # 열(세로 자리 수)
    if "seats" not in ss: ss.seats = [[None for _ in range(ss.cols)] for __ in range(ss.rows)]
    if "locked" not in ss: ss.locked = [[False for _ in range(ss.cols)] for __ in range(ss.rows)]
    if "selecting" not in ss: ss.selecting = None
    if "people" not in ss: ss.people = []       # list of dicts: {name, gender, group}
init_state()

def resize_grid(r, c):
    old_r, old_c = len(st.session_state.seats), len(st.session_state.seats[0])
    new_seats = [[None for _ in range(c)] for __ in range(r)]
    new_lock  = [[False for _ in range(c)] for __ in range(r)]
    for i in range(min(r, old_r)):
        for j in range(min(c, old_c)):
            new_seats[i][j] = st.session_state.seats[i][j]
            new_lock[i][j]  = st.session_state.locked[i][j]
    st.session_state.seats, st.session_state.locked = new_seats, new_lock

def normalize_gender(g: Optional[str]) -> Optional[str]:
    if not g: return None
    g = str(g).strip().lower()
    if g in ["m", "male", "남", "남자", "boy"]: return "M"
    if g in ["f", "female", "여", "여자", "girl"]: return "F"
    return None

def parse_text_lines(text: str) -> List[Dict]:
    """이름[,성별][,조] / 괄호표기(홍길동(남) 2) 등 다양한 라인 파싱"""
    people = []
    for line in text.splitlines():
        s = line.strip()
        if not s: continue
        name, gender, group = s, None, None
        m = re.search(r"[([]\s*([mfMF남여男女])\s*[])]", s)
        if m: gender = m.group(1)
        m2 = re.search(r"(\d+)\s*$", s)
        if m2: group = int(m2.group(1))
        parts = [p.strip() for p in re.split(r"[,\t]", s)]
        if len(parts) >= 1: name = parts[0] or name
        if len(parts) >= 2: gender = parts[1] or gender
        if len(parts) >= 3 and parts[2].isdigit(): group = int(parts[2])
        people.append({"name": name, "gender": normalize_gender(gender), "group": group})
    return people

def parse_uploaded(file) -> List[Dict]:
    """CSV: name[, gender][, group] (헤더 없어도 동작)"""
    try:
        df = pd.read_csv(file)
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, header=None)
        if df.shape[1] == 1:
            df.columns = ["name"]
    cols = [c.lower() for c in df.columns]
    col_map = {}
    for key in ["name", "gender", "group"]:
        if key in cols: col_map[key] = df.columns[cols.index(key)]
    people = []
    for _, row in df.iterrows():
        name = str(row.get(col_map.get("name", "name"), row.get(0, ""))).strip()
        if not name: continue
        gender = normalize_gender(row.get(col_map.get("gender", "gender"), None))
        group = row.get(col_map.get("group", "group"), None)
        try: group = int(group) if pd.notna(group) else None
        except Exception: group = None
        people.append({"name": name, "gender": gender, "group": group})
    return people

def flat_positions(rows, cols): return list(itertools.product(range(rows), range(cols)))

def shuffle_seats(seed=None):
    """
    좌석을 셔플합니다.
    - seed가 None이면 실행 때마다 다른 배치
    - seed(숫자/문자)를 주면 항상 같은 결과 → '재현' 가능
    """
    ss = st.session_state
    rng = random.Random(seed)
    targets = [(i,j) for i,j in flat_positions(ss.rows, ss.cols) if not ss.locked[i][j]]
    pool = ss.people.copy()
    need = len(targets)
    if len(pool) < need:
        pool = pool + [{"name": "빈자리", "gender": None, "group": None} for _ in range(need - len(pool))]
    else:
        pool = pool[:need]
    rng.shuffle(pool)
    for (i,j), person in zip(targets, pool):
        ss.seats[i][j] = person

def swap(a, b):
    (i1,j1),(i2,j2) = a,b
    st.session_state.seats[i1][j1], st.session_state.seats[i2][j2] = \
        st.session_state.seats[i2][j2], st.session_state.seats[i1][j1]

def seats_to_dataframe() -> pd.DataFrame:
    data = []
    for i,row in enumerate(st.session_state.seats, start=1):
        for j,person in enumerate(row, start=1):
            if person is None: person = {"name":"", "gender":None, "group":None}
            data.append({"row":i, "col":j, **person})
    return pd.DataFrame(data)

def render_png(font_bytes: Optional[bytes]=None, cell=(240,130), margin=24) -> bytes:
    rows, cols = st.session_state.rows, st.session_state.cols
    cw, ch = cell
    w, h = cols*cw + margin*2, rows*ch + margin*2
    img = Image.new("RGB", (w, h), (15,23,42))
    draw = ImageDraw.Draw(img)
    font = None; badge_font = None
    try:
        if font_bytes:
            font = ImageFont.truetype(io.BytesIO(font_bytes), 22)
            badge_font = ImageFont.truetype(io.BytesIO(font_bytes), 16)
    except Exception:
        font = None
    if font is None: font = ImageFont.load_default()
    if badge_font is None: badge_font = font

    def fill_color(g):
        if g == "M": return (31,59,104)
        if g == "F": return (90,47,79)
        return (37,50,71)

    for i in range(rows):
        for j in range(cols):
            x0, y0 = margin + j*cw, margin + i*ch
            person = st.session_state.seats[i][j]
            name  = (person or {}).get("name","")
            gender= (person or {}).get("gender",None)
            group = (person or {}).get("group",None)
            draw.rounded_rectangle([x0, y0, x0+cw-1, y0+ch-1], radius=18,
                                   fill=fill_color(gender), outline=(56,189,248), width=3)
            if group:
                bx0, by0 = x0+10, y0+8
                draw.rounded_rectangle([bx0,by0,bx0+42,by0+24], radius=8,
                                       outline=(148,163,184), width=1, fill=(2,6,23))
                draw.text((bx0+10,by0+6), str(group), fill=(226,232,240), font=badge_font)
            if name:
                draw.text((x0 + 20, y0 + (ch - 20)/2), name, fill=(226,232,240), font=font)
    buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()

# ============================ Sidebar ============================
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    c1, c2 = st.columns(2)
    with c1:
        rows = st.number_input("행(가로)", 1, 12, st.session_state.rows)   # ← 행
    with c2:
        cols = st.number_input("열(세로)", 1, 12, st.session_state.cols)   # ← 열
    if rows != st.session_state.rows or cols != st.session_state.cols:
        st.session_state.rows, st.session_state.cols = int(rows), int(cols)
        resize_grid(int(rows), int(cols))

    st.markdown("### 🧑‍🤝‍🧑 이름/성별/조 입력")
    up = st.file_uploader("CSV 업로드 (name, gender, group)", type=["csv"])
    txt = st.text_area("직접 입력(이름[,성별][,조])", height=160)
    if st.button("명단 적용/갱신", use_container_width=True):
        people = []
        if up is not None: people += parse_uploaded(up)
        if txt.strip(): people += parse_text_lines(txt)
        st.session_state.people = [p for p in people if p["name"]]
        st.success(f"명단 {len(st.session_state.people)}명 적용!")

    st.markdown("### 👥 조 편성")
    group_cnt = st.number_input("조 개수(자동 배정)", 0, 20, 0)
    if st.button("조 자동 배정 (라운드로빈)", use_container_width=True):
        if group_cnt > 0 and st.session_state.people:
            g = 1
            for p in st.session_state.people:
                p["group"] = g
                g = (g % group_cnt) + 1
            st.success("조 번호 자동 배정 완료!")

    st.markdown("### 🎛️ 동작")
    seed = st.text_input(
        "💾 씨드",
        placeholder="예: 1024",
        help="자리 섞기 결과를 재현하기 위한 난수 초기값입니다. 같은 명단·동일 씨드로 셔플하면 결과가 같습니다."
    )
    with st.expander("씨드가 뭐예요?"):
        st.markdown("""
- **씨드(seed)** = 난수 생성기의 **초기값**입니다.  
- 같은 명단에서 **같은 씨드**로 셔플하면 **항상 동일한 배치**가 나옵니다.  
- 숫자뿐 아니라 문자열도 가능: `1024`, `2025-2학기`, `eventA` 등.
""")

    c3, c4 = st.columns(2)
    with c3:
        if st.button("🎲 셔플", use_container_width=True):
            shuffle_seats(seed if seed else None)
    with c4:
        if st.button("↺ 초기화", use_container_width=True):
            st.session_state.seats = [[None for _ in range(st.session_state.cols)] for __ in range(st.session_state.rows)]
            st.session_state.locked = [[False for _ in range(st.session_state.cols)] for __ in range(st.session_state.rows)]
            st.session_state.selecting = None

    csv = seats_to_dataframe().to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ CSV 저장", data=csv, file_name="seating.csv",
                       mime="text/csv", use_container_width=True)

    st.markdown("### 🖼️ PNG 내보내기")
    font_file = st.file_uploader("한글 폰트 TTF(선택)", type=["ttf"])
    if st.button("🧷 PNG 생성", use_container_width=True):
        font_bytes = font_file.read() if font_file else None
        png = render_png(font_bytes=font_bytes)
        st.download_button("⬇️ PNG 다운로드", data=png, file_name="seating.png",
                           mime="image/png", use_container_width=True)

# ============================ 보드 ============================
st.markdown('<div class="retro-card crt">', unsafe_allow_html=True)
st.markdown(
    "#### 🧩 칠판(정면)  "
    "<span class='legend-pill'>Click 2회 → 자리교환</span>  "
    "<span class='legend-pill'>🔒 → 셔플 제외</span>",
    unsafe_allow_html=True
)

cols_container = st.columns(st.session_state.cols, vertical_alignment="center", gap="small")

for j, col in enumerate(cols_container):
    with col:
        for i in range(st.session_state.rows):
            person = st.session_state.seats[i][j]
            locked = st.session_state.locked[i][j]
            label = (person or {}).get("name") or "빈자리"
            gender = (person or {}).get("gender")
            group  = (person or {}).get("group")
            klass = "male" if gender == "M" else ("female" if gender == "F" else "neutral")

            b1, b2 = st.columns([4, 1])

            # 좌석 카드
            with b1:
                badge_html = f"<div class='badge'>#{group}</div>" if group else ""
                card_html = (
                    f"<div class='seat {klass} {'locked' if locked else ''}' style='position:relative;'>"
                    + badge_html
                    + f"<div class='nick'>{label}</div>"
                    + "</div>"
                )
                st.markdown(card_html, unsafe_allow_html=True)

                if st.button("선택" if not locked else "보기",
                             key=f"seat_{i}_{j}",
                             use_container_width=True,
                             disabled=locked):
                    if st.session_state.selecting is None:
                        st.session_state.selecting = (i, j)
                    else:
                        if st.session_state.selecting != (i, j):
                            swap(st.session_state.selecting, (i, j))
                        st.session_state.selecting = None

            # 잠금 토글
            with b2:
                if st.button("🔒" if not locked else "🔓", key=f"lock_{i}_{j}"):
                    st.session_state.locked[i][j] = not locked

st.markdown("</div>", unsafe_allow_html=True)

# 상태 표시
sel = st.session_state.selecting
st.markdown(
    f"<p class='small'>상태: {'교환할 좌석을 하나 더 선택하세요.' if sel else '대기 중'}"
    + (f" → 선택1: ({sel[0]+1}행, {sel[1]+1}열)" if sel else "")
    + "</p>",
    unsafe_allow_html=True
)

# 처음 부팅 시 예시 데이터
if "booted" not in st.session_state:
    st.session_state.booted = True
    if not any(any(r) for r in st.session_state.seats):
        demo = [
            {"name":"Alex","gender":"M","group":1},{"name":"Bao","gender":"M","group":1},
            {"name":"Chan","gender":"M","group":2},{"name":"Dana","gender":"F","group":2},
            {"name":"Eun","gender":"F","group":3},{"name":"Finn","gender":"M","group":3},
            {"name":"Giri","gender":"M","group":4},{"name":"Hana","gender":"F","group":4},
            {"name":"Ian","gender":"M","group":1},{"name":"Jin","gender":"M","group":1},
            {"name":"Kay","gender":"F","group":2},{"name":"Lia","gender":"F","group":2},
            {"name":"Min","gender":"M","group":3},{"name":"Nuri","gender":"F","group":3},
            {"name":"Oli","gender":"M","group":4},{"name":"Pyo","gender":"M","group":4},
        ]
        st.session_state.people = demo
        shuffle_seats()

# ============================ Sticky Footer ============================
st.markdown("""
<div id="retro-footer"><div class="inner">
  © 2025 이대형. All rights reserved.<br>
  <a href="https://aicreatorz.netlify.app/" target="_blank">https://aicreatorz.netlify.app/</a>
</div></div>
""", unsafe_allow_html=True)
