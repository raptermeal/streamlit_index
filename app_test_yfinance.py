import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# ✅ 페이지 설정
st.set_page_config(page_title="지수 조회 도구", layout="wide")

# ✅ 지수 목록
index_list = [
    ("중국", "Shenzhen Index", "399001.SZ"),
    ("베트남", "Vietnam VN Index", "0P0000HY8X.VN"),
    ("한국", "KOSPI Composite Index", "^KS11"),
    ("인니", "IDX Composite", "^JKSE"),
    ("필리핀", "PSEi", "PSEi.PS"),
    ("미국", "NASDAQ Composite", "^IXIC"),
    ("미국", "S&P 500", "^GSPC"),
    ("미국", "Dow Jones Industrial Avg", "^DJI"),
]

# ✅ 사용자 입력: 지수 선택, 기간 설정
st.sidebar.header("📌 조회 조건")
selected = st.sidebar.selectbox("지수 선택", index_list, format_func=lambda x: f"{x[0]} - {x[1]}")
start_date = st.sidebar.date_input("시작일", datetime(2025, 4, 26).date())
end_date = st.sidebar.date_input("종료일", datetime(2025, 4, 30).date())

# ✅ 타임스탬프 변환
period1 = int(datetime.combine(start_date, datetime.min.time()).timestamp())
period2 = int(datetime.combine(end_date, datetime.min.time()).timestamp())

# ✅ 헤더
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://finance.yahoo.com/"
}

# ✅ 데이터 요청
st.markdown(f"### ✅ {selected[1]} ({selected[2]})")
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{selected[2]}"
params = {
    "symbol": selected[2],
    "interval": "1d",
    "period1": period1,
    "period2": period2,
    "includeAdjustedClose": "true",
    "events": "capitalGain|div|split",
    "formatted": "true",
    "lang": "en-US",
    "region": "US"
}

try:
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    result = data["chart"]["result"][0]

    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]

    df = pd.DataFrame({
        "날짜": [datetime.utcfromtimestamp(ts).date() for ts in timestamps],
        "종가": closes
    })

    st.dataframe(df, use_container_width=True)
    st.line_chart(df.set_index("날짜"))

except Exception as e:
    st.error(f"❗ 데이터 요청 실패: {e}")
