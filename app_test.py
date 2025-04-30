import streamlit as st
import yfinance as yf
from datetime import date, timedelta

st.set_page_config(page_title="Yahoo Finance 주가 시각화", layout="wide")
st.title("📈 야후파이낸스 주가 데이터")

ticker = st.text_input("종목 티커 입력 (예: AAPL, TSLA, ^KS11)", value="AAPL")

end_date = date.today()
start_date = end_date - timedelta(days=90)

@st.cache_data
def load_data(ticker, start_date, end_date):
    try:
        df = yf.download(ticker, start=start_date, end=end_date + timedelta(days=1), progress=False)
        return df
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {e}")
        return None

df = load_data(ticker, start_date, end_date)

if df is not None and not df.empty:
    st.subheader(f"최근 90일간 {ticker} 주가")
    st.line_chart(df["Close"])
    st.dataframe(df.tail())
else:
    st.warning("⚠️ 유효한 티커를 입력하세요.")
