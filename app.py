import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime


# =========================================================
# 페이지 설정
# =========================================================

st.set_page_config(
    page_title="보라고등학교 학사일정",
    page_icon="🏫",
    layout="wide"
)


# =========================================================
# 기본 설정
# =========================================================

API_URL = "https://open.neis.go.kr/hub/SchoolSchedule"

ATPT_OFCDC_SC_CODE = "J10"
SD_SCHUL_CODE = "7530882"

SCHOOL_NAME = "보라고등학교"


# =========================================================
# NEIS API KEY
# =========================================================

try:

    API_KEY = st.secrets["NEIS_API_KEY"]

except Exception:

    st.error(
        """
        🔑 NEIS API Key가 설정되지 않았습니다.

        Streamlit Cloud의

        Settings → Secrets

        에서 다음과 같이 입력해주세요.

        NEIS_API_KEY = "발급받은_API_키"
        """
    )

    st.stop()


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .title {
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

    .info-card {
        padding: 20px;
        border-radius: 15px;
        background: #f5f7fa;
        border: 1px solid #e1e5ea;
        text-align: center;
    }

    .calendar-card {
        padding: 15px;
        border-radius: 12px;
        background: white;
        border: 1px solid #ddd;
        margin-bottom: 10px;
    }

    .date-number {
        font-size: 24px;
        font-weight: bold;
    }

    .event-name {
        font-size: 17px;
        font-weight: bold;
    }

    .event-content {
        color: #666;
        margin-top: 5px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="title">🏫 보라고등학교 학사일정</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'NEIS 교육정보를 이용한 학교 학사일정 조회 서비스'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# 학년도 선택
# =========================================================

current_year = date.today().year

col1, col2, col3 = st.columns([2, 2, 1])


with col1:

    year = st.selectbox(
        "📅 학년도",
        list(
            range(
                current_year - 2,
                current_year + 2
            )
        ),
        index=2
    )


with col2:

    month = st.selectbox(
        "🗓️ 월",
        ["전체"] + list(range(1, 13))
    )


with col3:

    st.write("")

    refresh = st.button(
        "🔄 새로고침",
        use_container_width=True
    )


# =========================================================
# NEIS 데이터 가져오기
# =========================================================

@st.cache_data(ttl=600)
def get_schedule(year):

    params = {

        "KEY": API_KEY,

        "Type": "json",

        "pIndex": 1,

        "pSize": 1000,

        "ATPT_OFCDC_SC_CODE":
            ATPT_OFCDC_SC_CODE,

        "SD_SCHUL_CODE":
            SD_SCHUL_CODE,

        "AA_FROM_YMD":
            f"{year}0101",

        "AA_TO_YMD":
            f"{year}1231"
    }


    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()


    except requests.exceptions.RequestException as e:

        return None, f"NEIS API 연결 오류: {e}"


    except ValueError:

        return None, "NEIS API에서 JSON 데이터를 받지 못했습니다."


    # -----------------------------------------------------
    # API 오류 처리
    # -----------------------------------------------------

    if "RESULT" in data:

        result = data["RESULT"]

        return None, result.get(
            "MESSAGE",
            "NEIS API 오류가 발생했습니다."
        )


    # -----------------------------------------------------
    # 학사일정 데이터 추출
    # -----------------------------------------------------

    try:

        rows = data["SchoolSchedule"][1]["row"]

    except (KeyError, IndexError):

        return pd.DataFrame(), None


    return pd.DataFrame(rows), None


# =========================================================
# 새로고침
# =========================================================

if refresh:

    get_schedule.clear()


# =========================================================
# 데이터 조회
# =========================================================

with st.spinner(
    f"{year}학년도 학사일정을 불러오는 중..."
):

    df, error = get_schedule(year)


# =========================================================
# 오류
# =========================================================

if error:

    st.error(
        f"❌ {error}"
    )

    st.info(
        "NEIS 인증키가 올바른지 확인해주세요."
    )

    st.stop()


# =========================================================
# 데이터 없음
# =========================================================

if df is None or df.empty:

    st.warning(
        f"⚠️ {year}학년도 학사일정 데이터가 없습니다."
    )

    st.stop()


# =========================================================
# 날짜 변환
# =========================================================

if "AA_YMD" in df.columns:

    df["DATE"] = pd.to_datetime(
        df["AA_YMD"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

else:

    df["DATE"] = pd.NaT


# =========================================================
# 월 필터
# =========================================================

filtered_df = df.copy()


if month != "전체":

    filtered_df = filtered_df[
        filtered_df["DATE"].dt.month == month
    ]


# =========================================================
# 상단 정보
# =========================================================

total_count = len(filtered_df)

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "🏫 학교",
        SCHOOL_NAME
    )


with col2:

    st.metric(
        "📅 학년도",
        f"{year}년"
    )


with col3:

    st.metric(
        "📌 일정 수",
        f"{total_count}개"
    )


# =========================================================
# 주요 일정 컬럼 찾기
# =========================================================

def get_value(row, column):

    value = row.get(column, "")

    if pd.isna(value):

        return ""

    return str(value)


# =========================================================
# 다음 일정
# =========================================================

today = pd.Timestamp.today().normalize()


future_df = df[
    df["DATE"] >= today
].sort_values("DATE")


st.markdown("## 🔔 다음 학사일정")


if not future_df.empty:

    next_row = future_df.iloc[0]

    next_date = next_row["DATE"]

    event_name = get_value(
        next_row,
        "EVENT_NM"
    )

    event_content = get_value(
        next_row,
        "EVENT_CNTNT"
    )

    st.info(
        f"""
        **{next_date.strftime('%Y년 %m월 %d일')}**

        📌 **{event_name}**

        {event_content}
        """
    )

else:

    st.info(
        "올해 남은 학사일정이 없습니다."
    )


# =========================================================
# 월별 일정
# =========================================================

st.markdown("## 📅 학사일정")


if filtered_df.empty:

    st.warning(
        "선택한 조건에 해당하는 일정이 없습니다."
    )

else:

    filtered_df = filtered_df.sort_values(
        "DATE"
    )


    for _, row in filtered_df.iterrows():

        event_date = row["DATE"]

        if pd.isna(event_date):

            continue


        date_text = event_date.strftime(
            "%Y년 %m월 %d일"
        )


        event_name = get_value(
            row,
            "EVENT_NM"
        )


        event_content = get_value(
            row,
            "EVENT_CNTNT"
        )


        st.markdown(
            f"""
            <div class="calendar-card">

            <div class="date-number">
            📅 {date_text}
            </div>

            <div class="event-name">
            {event_name}
            </div>

            <div class="event-content">
            {event_content}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# 전체 데이터
# =========================================================

st.markdown("---")

st.markdown("## 📋 전체 일정표")


display_columns = [
    "AA_YMD",
    "EVENT_NM",
    "EVENT_CNTNT",
    "ONE_GRADE_EVENT_YN",
    "TWO_GRADE_EVENT_YN",
    "THREE_GRADE_EVENT_YN"
]


available_columns = [
    col
    for col in display_columns
    if col in filtered_df.columns
]


display_df = filtered_df[
    available_columns
].copy()


rename_columns = {

    "AA_YMD": "날짜",

    "EVENT_NM": "행사명",

    "EVENT_CNTNT": "행사내용",

    "ONE_GRADE_EVENT_YN": "1학년",

    "TWO_GRADE_EVENT_YN": "2학년",

    "THREE_GRADE_EVENT_YN": "3학년"

}


display_df = display_df.rename(
    columns=rename_columns
)


if "날짜" in display_df.columns:

    display_df["날짜"] = pd.to_datetime(
        display_df["날짜"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 검색
# =========================================================

st.markdown("## 🔎 일정 검색")


search_word = st.text_input(
    "검색어",
    placeholder="예: 시험, 방학, 입학, 졸업..."
)


if search_word:

    search_df = filtered_df[
        filtered_df.apply(
            lambda row:
            search_word.lower()
            in " ".join(
                str(value)
                for value in row.values
                if pd.notna(value)
            ).lower(),
            axis=1
        )
    ]


    st.write(
        f"검색 결과: **{len(search_df)}개**"
    )


    if search_df.empty:

        st.warning(
            "검색 결과가 없습니다."
        )

    else:

        search_display = search_df[
            available_columns
        ].copy()


        search_display = search_display.rename(
            columns=rename_columns
        )


        if "날짜" in search_display.columns:

            search_display["날짜"] = pd.to_datetime(
                search_display["날짜"].astype(str),
                format="%Y%m%d",
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")


        st.dataframe(
            search_display,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# 안내
# =========================================================

st.markdown("---")

st.caption(
    "📡 데이터 출처: 교육부 나이스(NEIS) 교육정보 개방 포털"
)

st.caption(
    "※ 학사일정은 학교의 NEIS 등록 정보에 따라 달라질 수 있습니다."
)
