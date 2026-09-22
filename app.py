import streamlit as st
import requests
import pandas as pd
from datetime import date

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="보라고등학교 학사일정",
    page_icon="🏫",
    layout="wide"
)

SCHOOL_NAME = "보라고등학교"
OFFICE_CODE = "J10"
SCHOOL_CODE = "7530882"

API_URL = "https://open.neis.go.kr/hub/SchoolSchedule"


# =========================
# 학사일정 가져오기
# =========================
@st.cache_data(ttl=600)
def get_schedule(year):

    params = {
        # API 키 없이 호출
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,

        # 경기도교육청
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE,

        # 보라고등학교
        "SD_SCHUL_CODE": SCHOOL_CODE,

        # 조회 기간
        "AA_FROM_YMD": f"{year}0101",
        "AA_TO_YMD": f"{year}1231",
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # NEIS JSON 구조 확인
        if "SchoolSchedule" not in data:
            return pd.DataFrame()

        schedule = data["SchoolSchedule"]

        if len(schedule) < 2:
            return pd.DataFrame()

        rows = schedule[1].get("row", [])

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows)

    except Exception as e:
        st.error(f"학사일정을 불러오는 중 오류가 발생했습니다.\n\n{e}")
        return pd.DataFrame()


# =========================
# 제목
# =========================
st.title("🏫 보라고등학교 학사일정")
st.caption("나이스(NEIS) 학사일정 Open API")

st.divider()


# =========================
# 조회 연도
# =========================
col1, col2 = st.columns([1, 2])

with col1:
    year = st.selectbox(
        "📅 조회 연도",
        [2025, 2026, 2027],
        index=1
    )

with col2:
    st.info(
        f"교육청 코드: {OFFICE_CODE}  |  "
        f"학교 코드: {SCHOOL_CODE}"
    )


# =========================
# 데이터 가져오기
# =========================
df = get_schedule(year)


# =========================
# 데이터가 없는 경우
# =========================
if df.empty:

    st.warning(
        "학사일정 데이터를 불러오지 못했습니다."
    )

    st.markdown("""
    ### 확인할 사항

    - 학교 코드: `7530882`
    - 교육청 코드: `J10`
    - NEIS 학사일정 API 연결 상태
    - API에서 키 없이 제공되는 데이터인지 확인

    현재 앱은 **API 키 없이 호출하는 방식**으로 설정되어 있습니다.
    """)

    st.stop()


# =========================
# 필요한 컬럼 정리
# =========================
columns = {
    "AA_YMD": "날짜",
    "EVENT_NM": "행사명",
    "EVENT_CNTNT": "내용",
    "ONE_GRADE_EVENT_YN": "1학년",
    "TWO_GRADE_EVENT_YN": "2학년",
    "THREE_GRADE_EVENT_YN": "3학년",
}

existing_columns = {
    k: v for k, v in columns.items()
    if k in df.columns
}

df = df.rename(columns=existing_columns)


# 날짜 변환
if "날짜" in df.columns:
    df["날짜"] = pd.to_datetime(
        df["날짜"],
        format="%Y%m%d",
        errors="coerce"
    )

    df = df.sort_values("날짜")


# =========================
# 월 선택
# =========================
if "날짜" in df.columns:

    months = sorted(
        df["날짜"]
        .dropna()
        .dt.month
        .unique()
        .tolist()
    )

    if months:

        month_options = ["전체"] + [
            f"{m}월" for m in months
        ]

        selected_month = st.selectbox(
            "📆 월 선택",
            month_options
        )

        if selected_month != "전체":

            month = int(
                selected_month.replace("월", "")
            )

            display_df = df[
                df["날짜"].dt.month == month
            ]

        else:
            display_df = df

    else:
        display_df = df

else:
    display_df = df


# =========================
# 검색
# =========================
search = st.text_input(
    "🔎 일정 검색",
    placeholder="예: 시험, 방학, 개학, 체험학습"
)

if search:

    mask = display_df.astype(str).apply(
        lambda row: row.str.contains(
            search,
            case=False,
            na=False
        ).any(),
        axis=1
    )

    display_df = display_df[mask]


# =========================
# 일정 개수
# =========================
st.subheader(
    f"📋 학사일정 ({len(display_df)}건)"
)


# =========================
# 카드 형태 일정
# =========================
if not display_df.empty:

    for _, row in display_df.iterrows():

        event_date = row.get("날짜", "")
        event_name = row.get("행사명", "")
        event_content = row.get("내용", "")

        if pd.notna(event_date):
            date_text = event_date.strftime(
                "%Y년 %m월 %d일"
            )
        else:
            date_text = "날짜 없음"

        with st.container(border=True):

            st.markdown(
                f"### 📅 {date_text}"
            )

            st.markdown(
                f"**{event_name}**"
            )

            if pd.notna(event_content) and event_content:
                st.write(event_content)


# =========================
# 전체 표
# =========================
st.divider()

st.subheader("📊 전체 학사일정")

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# =========================
# 안내
# =========================
st.divider()

st.caption(
    "※ 본 서비스는 나이스(NEIS) 학사일정 Open API를 이용합니다."
)
