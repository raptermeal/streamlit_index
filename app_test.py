import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

# 📌 페이지 설정
st.set_page_config(page_title="야후파이낸스 주가 시각화", layout="wide")

# 📌 기본 설정
st.title("📈 야후파이낸스 주가 데이터")
ticker = st.text_input("종목 티커 입력 (예: AAPL, TSLA, MSFT)", value="AAPL")

# 📌 날짜 설정 (최근 90일)
end_date = date.today()
start_date = end_date - timedelta(days=90)

# 📌 데이터 다운로드
data = yf.download(ticker, start=start_date, end=end_date)

# 📌 데이터가 있을 때 시각화
if not data.empty:
    st.subheader(f"최근 90일간 {ticker} 주가 추이")
    st.line_chart(data["Close"])
    st.dataframe(data.tail())
else:
    st.warning("⚠️ 유효한 티커를 입력하세요.")
