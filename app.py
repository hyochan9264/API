import streamlit as st
import requests
import pandas as pd
import calendar
from datetime import date

# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="보라고등학교 학사일정",
    page_icon="🏫",
    layout="wide"
)

SCHOOL_NAME = "보라고등학교"
EDU_CODE = "J10"
SCHOOL_CODE = "7530882"

API_URL = "https://open.neis.go.kr/hub/SchoolSchedule"

YEAR = 2026


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main-title {
    text-align: center;
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 5px;
}

.sub-title {
    text-align: center;
    color: #666;
    margin-bottom: 25px;
}

.month-title {
    font-size: 25px;
    font-weight: bold;
    margin-top: 20px;
}

.day-box {
    border: 1px solid #dddddd;
    border-radius: 10px;
    padding: 8px;
    min-height: 75px;
    margin-bottom: 5px;
    background-color: white;
}

.day-number {
    font-weight: bold;
    font-size: 16px;
}

.event {
    font-size: 12px;
    margin-top: 5px;
    color: #1769aa;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# NEIS API
# =========================================================

@st.cache_data(ttl=600)
def get_neis_schedule():

    params = {
        # API 키가 없는 경우 NEIS에서 sample key 방식 사용
        "KEY": "sample",
        "Type": "json",
        "pIndex": 1,

        # sample key에서는 최대 5건
        "pSize": 5,

        "ATPT_OFCDC_SC_CODE": EDU_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,

        # 2026년 전체
        "AA_FROM_YMD": "20260101",
        "AA_TO_YMD": "20261231"
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if "SchoolSchedule" not in data:
            return pd.DataFrame()

        schedule_data = data["SchoolSchedule"]

        if len(schedule_data) < 2:
            return pd.DataFrame()

        rows = schedule_data[1].get("row", [])

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        return df

    except Exception:
        return pd.DataFrame()


df = get_neis_schedule()


# =========================================================
# 데이터 정리
# =========================================================

if not df.empty:

    if "AA_YMD" in df.columns:

        df["AA_YMD"] = pd.to_datetime(
            df["AA_YMD"].astype(str),
            format="%Y%m%d",
            errors="coerce"
        )

    if "EVENT_NM" not in df.columns:
        df["EVENT_NM"] = ""

    if "EVENT_CNTNT" not in df.columns:
        df["EVENT_CNTNT"] = ""


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="main-title">🏫 보라고등학교 학사일정</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">2026년 학사일정 정보</div>',
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# 학교 정보
# =========================================================

info1, info2, info3 = st.columns(3)

with info1:
    st.metric("학교", SCHOOL_NAME)

with info2:
    st.metric("교육청 코드", EDU_CODE)

with info3:
    st.metric("학교 코드", SCHOOL_CODE)


st.divider()


# =========================================================
# 검색
# =========================================================

search_text = st.text_input(
    "🔎 학사일정 검색",
    placeholder="예: 시험, 방학, 개학, 체험학습"
)


# =========================================================
# 일정 검색
# =========================================================

filtered_df = df.copy()

if search_text and not df.empty:

    mask = (
        df["EVENT_NM"].astype(str).str.contains(
            search_text,
            case=False,
            na=False
        )
        |
        df["EVENT_CNTNT"].astype(str).str.contains(
            search_text,
            case=False,
            na=False
        )
    )

    filtered_df = df[mask]


# =========================================================
# 월별 달력
# =========================================================

st.header("📅 2026년 전체 학사일정")

for month in range(1, 13):

    month_name = f"{month}월"

    st.markdown(
        f'<div class="month-title">🗓️ {YEAR}년 {month_name}</div>',
        unsafe_allow_html=True
    )

    # 요일
    weekday_names = [
        "월", "화", "수",
        "목", "금", "토", "일"
    ]

    header_cols = st.columns(7)

    for i, weekday in enumerate(weekday_names):

        header_cols[i].markdown(
            f"**{weekday}**"
        )


    # 달력
    month_calendar = calendar.monthcalendar(
        YEAR,
        month
    )

    for week in month_calendar:

        cols = st.columns(7)

        for weekday_index, day in enumerate(week):

            if day == 0:

                cols[weekday_index].write("")

                continue


            current_date = date(
                YEAR,
                month,
                day
            )


            # 해당 날짜의 일정
            events = []

            if not filtered_df.empty:

                for _, row in filtered_df.iterrows():

                    event_date = row.get(
                        "AA_YMD"
                    )

                    if pd.notna(event_date):

                        if event_date.date() == current_date:

                            event_name = str(
                                row.get(
                                    "EVENT_NM",
                                    ""
                                )
                            )

                            if event_name:
                                events.append(
                                    event_name
                                )


            # 날짜 출력
            html = f"""
            <div class="day-box">
                <div class="day-number">
                    {day}
                </div>
            """

            for event in events:

                html += f"""
                <div class="event">
                    📌 {event}
                </div>
                """

            html += "</div>"

            cols[weekday_index].markdown(
                html,
                unsafe_allow_html=True
            )


    st.divider()


# =========================================================
# NEIS 데이터 표시
# =========================================================

st.header("📋 NEIS에서 받은 학사일정")


if df.empty:

    st.warning(
        "NEIS에서 학사일정 데이터를 가져오지 못했습니다."
    )

    st.info(
        "현재 앱은 API 인증키 없이 실행되도록 설정되어 있습니다. "
        "NEIS 공식 API에서는 인증키가 없을 경우 5건의 샘플 데이터만 제공합니다."
    )

else:

    display_columns = []

    if "AA_YMD" in df.columns:
        display_columns.append("AA_YMD")

    if "EVENT_NM" in df.columns:
        display_columns.append("EVENT_NM")

    if "EVENT_CNTNT" in df.columns:
        display_columns.append("EVENT_CNTNT")

    display_df = df[display_columns].copy()

    rename_dict = {
        "AA_YMD": "날짜",
        "EVENT_NM": "행사명",
        "EVENT_CNTNT": "행사내용"
    }

    display_df = display_df.rename(
        columns=rename_dict
    )

    if "날짜" in display_df.columns:

        display_df["날짜"] = display_df[
            "날짜"
        ].dt.strftime("%Y-%m-%d")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 안내
# =========================================================

st.divider()

st.caption(
    "데이터 출처: 나이스 교육정보 개방 포털(NEIS)"
)

st.caption(
    "교육청 코드: J10 | 학교 코드: 7530882"
)

st.caption(
    "※ API 인증키 없이 실행하는 경우 NEIS의 샘플 데이터 제한이 적용됩니다."
)
