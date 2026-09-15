import streamlit as st
from openai import OpenAI
import json
import random


# =========================================================
# 페이지 설정
# =========================================================

st.set_page_config(
    page_title="AI 추리 사건",
    page_icon="🕵️",
    layout="centered"
)


# =========================================================
# API 설정
# =========================================================

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error(
        "🔑 OPENAI_API_KEY가 설정되지 않았습니다.\n\n"
        "Streamlit Cloud → Settings → Secrets에서 "
        "OPENAI_API_KEY를 설정해주세요."
    )
    st.stop()


client = OpenAI(api_key=api_key)

MODEL = "gpt-5.4-nano"


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 25px;
    }

    .case-box {
        padding: 20px;
        border-radius: 15px;
        background: #f5f5f5;
        border: 1px solid #ddd;
        margin-bottom: 15px;
    }

    .suspect-box {
        padding: 15px;
        border-radius: 12px;
        background: #fafafa;
        border: 1px solid #ddd;
        margin-bottom: 10px;
    }

    .clue-box {
        padding: 15px;
        border-radius: 12px;
        background: #fff8dc;
        border: 1px solid #eadb9b;
        margin-bottom: 10px;
    }

    .success-box {
        padding: 20px;
        border-radius: 15px;
        background: #e8f5e9;
        border: 2px solid #66bb6a;
        text-align: center;
    }

    .wrong-box {
        padding: 20px;
        border-radius: 15px;
        background: #ffebee;
        border: 2px solid #ef5350;
        text-align: center;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="main-title">🕵️ AI 추리 사건</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI가 만든 사건을 조사하고 범인을 찾아보세요!'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# 세션 초기화
# =========================================================

if "case" not in st.session_state:
    st.session_state.case = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "revealed_clues" not in st.session_state:
    st.session_state.revealed_clues = []

if "result" not in st.session_state:
    st.session_state.result = None


# =========================================================
# AI 호출 함수
# =========================================================

def ask_ai(prompt):

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

    return response.output_text


# =========================================================
# 사건 생성
# =========================================================

def create_case(difficulty, theme):

    prompt = f"""
당신은 추리 게임 전문 작가입니다.

한국어로 플레이 가능한 추리 사건 하나를 만들어주세요.

난이도: {difficulty}
사건 분위기: {theme}

조건:

1. 사건은 완전히 허구여야 합니다.
2. 용의자는 정확히 4명입니다.
3. 범인은 용의자 중 정확히 1명입니다.
4. 범인이 누구인지 논리적으로 추리할 수 있는 단서가 있어야 합니다.
5. 용의자마다 알리바이를 만들어주세요.
6. 단서 중 일부는 처음부터 공개하고,
   일부는 플레이어가 조사하거나 질문해야 알 수 있도록 만들어주세요.
7. 범인이 너무 쉽게 드러나면 안 됩니다.
8. 하지만 충분히 조사하면 논리적으로 범인을 특정할 수 있어야 합니다.
9. 사건은 폭력적인 묘사보다 추리와 논리에 집중해주세요.

반드시 아래 JSON 형식으로만 답해주세요.

{{
    "title": "사건 제목",
    "summary": "사건의 기본 상황",
    "location": "사건 장소",
    "time": "사건 발생 시간",
    "victim": "피해자 또는 사건의 중심 인물",
    "suspects": [
        {{
            "name": "용의자 이름",
            "role": "직업 또는 관계",
            "description": "인물 설명",
            "alibi": "알리바이"
        }}
    ],
    "initial_clues": [
        "처음부터 발견되는 단서 1",
        "처음부터 발견되는 단서 2",
        "처음부터 발견되는 단서 3"
    ],
    "hidden_clues": [
        "조사하면 발견되는 단서 1",
        "조사하면 발견되는 단서 2",
        "조사하면 발견되는 단서 3",
        "조사하면 발견되는 단서 4"
    ],
    "answer": "범인의 이름",
    "explanation": "범인이 누구인지 설명하는 논리적 해설"
}}
"""

    result = ask_ai(prompt)

    try:
        return json.loads(result)

    except Exception:

        # JSON 코드 블록으로 반환될 경우 처리
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

        return json.loads(result)


# =========================================================
# 새 사건 버튼
# =========================================================

with st.sidebar:

    st.header("⚙️ 사건 설정")

    difficulty = st.selectbox(
        "난이도",
        [
            "쉬움",
            "보통",
            "어려움"
        ]
    )

    theme = st.selectbox(
        "사건 분위기",
        [
            "학교",
            "박물관",
            "호텔",
            "연구실",
            "저택",
            "기차",
            "회사"
        ]
    )

    if st.button(
        "🆕 새 사건 만들기",
        use_container_width=True
    ):

        with st.spinner("🕵️ 사건을 구성하고 있습니다..."):

            try:

                st.session_state.case = create_case(
                    difficulty,
                    theme
                )

                st.session_state.messages = []

                st.session_state.revealed_clues = []

                st.session_state.result = None

                st.rerun()

            except Exception as e:

                st.error(
                    "사건 생성 중 오류가 발생했습니다.\n\n"
                    + str(e)
                )


# =========================================================
# 사건이 없을 때
# =========================================================

if st.session_state.case is None:

    st.info(
        "👈 왼쪽 설정에서 난이도와 사건 분위기를 선택한 뒤 "
        "'새 사건 만들기'를 눌러주세요."
    )

    st.markdown(
        """
        ### 🕵️ 게임 방법

        **1️⃣ 사건 생성**

        AI가 새로운 추리 사건을 만듭니다.

        **2️⃣ 단서 조사**

        사건에 공개된 단서를 확인합니다.

        **3️⃣ AI에게 질문**

        사건과 용의자에 대해 질문할 수 있습니다.

        **4️⃣ 범인 선택**

        충분히 조사한 뒤 범인을 선택합니다.

        **5️⃣ 정답 확인**

        범인이 맞는지 확인하고 사건의 진상을 확인합니다.
        """
    )

    st.stop()


# =========================================================
# 사건 정보
# =========================================================

case = st.session_state.case


st.markdown(
    f"""
    <div class="case-box">

    <h2>📁 {case["title"]}</h2>

    <p>
    <b>📍 장소:</b> {case["location"]}
    </p>

    <p>
    <b>⏰ 시간:</b> {case["time"]}
    </p>

    <p>
    <b>👤 사건:</b> {case["victim"]}
    </p>

    <hr>

    <p>
    {case["summary"]}
    </p>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 용의자
# =========================================================

st.header("👥 용의자")

for i, suspect in enumerate(case["suspects"]):

    with st.expander(
        f"🔎 {suspect['name']} — {suspect['role']}"
    ):

        st.write(
            f"**인물 설명:** {suspect['description']}"
        )

        st.write(
            f"**알리바이:** {suspect['alibi']}"
        )


# =========================================================
# 초기 단서
# =========================================================

st.header("🔎 발견된 단서")

for i, clue in enumerate(
    case["initial_clues"]
):

    st.markdown(
        f"""
        <div class="clue-box">
        🔍 <b>단서 {i + 1}</b><br>
        {clue}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 추가 단서 조사
# =========================================================

st.subheader("🔍 추가 조사")

if len(
    st.session_state.revealed_clues
) < len(case["hidden_clues"]):

    next_number = (
        len(
            st.session_state.revealed_clues
        ) + 1
    )

    if st.button(
        f"🔎 현장 조사하기 ({next_number}/{len(case['hidden_clues'])})",
        use_container_width=True
    ):

        clue = case["hidden_clues"][
            len(
                st.session_state.revealed_clues
            )
        ]

        st.session_state.revealed_clues.append(
            clue
        )

        st.rerun()

else:

    st.success(
        "모든 추가 단서를 조사했습니다."
    )


for i, clue in enumerate(
    st.session_state.revealed_clues
):

    st.markdown(
        f"""
        <div class="clue-box">
        🧩 <b>추가 단서 {i + 1}</b><br>
        {clue}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# AI에게 질문
# =========================================================

st.header("💬 AI 탐정에게 질문")

st.caption(
    "예: '김민수가 사건 시간에 정말 혼자 있었나요?'"
)

question = st.text_input(
    "질문",
    placeholder="사건에 대해 궁금한 것을 질문하세요.",
    label_visibility="collapsed"
)


if st.button(
    "💬 질문하기",
    use_container_width=True
):

    if not question.strip():

        st.warning(
            "질문을 입력해주세요."
        )

    else:

        visible_clues = (
            case["initial_clues"]
            +
            st.session_state.revealed_clues
        )

        suspect_text = "\n".join(
            [
                f"{s['name']}: "
                f"{s['role']}, "
                f"{s['description']}, "
                f"알리바이: {s['alibi']}"
                for s in case["suspects"]
            ]
        )

        clue_text = "\n".join(
            visible_clues
        )

        prompt = f"""
당신은 추리 게임의 조사관 보조 AI입니다.

플레이어가 사건을 조사하고 있습니다.

중요 규칙:

- 범인의 이름을 직접 알려주지 마세요.
- 아직 공개되지 않은 hidden clue의 내용을 직접 공개하지 마세요.
- 플레이어가 제공받은 정보 안에서만 답하세요.
- 질문에 답하되 추리를 대신하지 마세요.
- 필요하면 어떤 부분을 더 조사해야 하는지 힌트를 주세요.
- 거짓 정보를 만들지 마세요.

사건:
{case["summary"]}

용의자:
{suspect_text}

현재 공개된 단서:
{clue_text}

플레이어 질문:
{question}

한국어로 짧고 자연스럽게 답해주세요.
"""

        with st.spinner(
            "🤖 사건 기록을 확인하고 있습니다..."
        ):

            try:

                answer = ask_ai(prompt)

                st.session_state.messages.append(
                    {
                        "question": question,
                        "answer": answer
                    }
                )

            except Exception as e:

                st.error(
                    "AI 응답 중 오류가 발생했습니다.\n\n"
                    + str(e)
                )


# =========================================================
# 질문 기록
# =========================================================

if st.session_state.messages:

    st.subheader("📜 조사 기록")

    for item in reversed(
        st.session_state.messages
    ):

        st.markdown(
            f"**🧑‍💼 나:** {item['question']}"
        )

        st.markdown(
            f"**🤖 AI:** {item['answer']}"
        )

        st.divider()


# =========================================================
# 범인 추리
# =========================================================

st.header("🧩 범인은 누구일까요?")

suspect_names = [
    s["name"]
    for s in case["suspects"]
]


choice = st.radio(
    "범인이라고 생각하는 사람을 선택하세요.",
    suspect_names
)


if st.button(
    "🔍 범인 확인하기",
    use_container_width=True
):

    correct_answer = case["answer"]

    if choice == correct_answer:

        st.session_state.result = "correct"

    else:

        st.session_state.result = "wrong"

    st.rerun()


# =========================================================
# 결과
# =========================================================

if st.session_state.result == "correct":

    st.markdown(
        f"""
        <div class="success-box">

        <h2>🎉 정답입니다!</h2>

        <p>
        당신이 선택한 <b>{choice}</b>이(가)
        범인입니다.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("🧠 사건의 진실")

    st.write(
        case["explanation"]
    )


elif st.session_state.result == "wrong":

    st.markdown(
        f"""
        <div class="wrong-box">

        <h2>❌ 틀렸습니다.</h2>

        <p>
        <b>{choice}</b>은(는) 범인이 아닙니다.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "아직 사건을 더 조사할 수 있습니다. "
        "단서를 다시 확인해보세요!"
    )


# =========================================================
# 푸터
# =========================================================

st.divider()

st.caption(
    "🕵️ AI 추리 사건 | Powered by OpenAI"
)
