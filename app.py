import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

# 페이지 설정
st.set_page_config(layout="wide")

# ✅ 상단 여백 줄이기 + 버튼 스타일 조정
st.markdown("""
    <style>
        .block-container {padding-top: 1.5rem;}
        .stButton > button:first-child {border: 2px solid #ffcccc;}
        td, th {text-align: center; vertical-align: middle;}
        th:nth-child(1), td:nth-child(1),
        th:nth-child(2), td:nth-child(2),
        th:nth-child(3), td:nth-child(3) {text-align: left;}
        section.main > div {overflow-x: hidden;}
    </style>
""", unsafe_allow_html=True)

weekday_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}

# 타이틀
st.title("주요지표조회")

# 데이터 불러오기
df_index = pd.read_csv("./index_list.csv")

# 세션 상태 초기화
for key in ["df_final", "df_raw", "csv_data", "query_done"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "query_done" else False

st.sidebar.markdown(
    """
    <style>
    div[data-testid="stDateInput"] > label {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: -0.5rem;
    }
    div[data-testid="stDateInput"] {
        margin-top: -0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.subheader("📅 기준날짜")
selected_date = st.sidebar.date_input(
    "📅 기준날짜",
    datetime.today().date(),
    label_visibility="collapsed"
)
selected_items = []

st.sidebar.subheader("지표")
for _, row in df_index[df_index["구분"] == "지표"].iterrows():
    if st.sidebar.checkbox(f"{row['국가_짧은명']}){row['항목명_짧은']}", value=True):
        selected_items.append(row)

st.sidebar.subheader("환율")
for _, row in df_index[df_index["구분"] == "환율"].iterrows():
    if st.sidebar.checkbox(f"{row['국가_짧은명']}){row['항목명_짧은']}", value=True):
        selected_items.append(row)

st.sidebar.subheader("사료")
for _, row in df_index[df_index["구분"] == "사료"].iterrows():
    if st.sidebar.checkbox(f"{row['국가_짧은명']}){row['항목명_짧은']}", value=True):
        selected_items.append(row)

st.sidebar.markdown("---")
st.sidebar.markdown("📄 **출처**: Yahoo Finance")
st.sidebar.markdown("🛠️ **제작**: 디지털혁신팀")

# 날짜 처리
today = datetime.combine(selected_date, datetime.min.time())
start_of_week = today - timedelta(days=today.weekday())
end_of_week = start_of_week + timedelta(days=4)
three_months_ago = today - timedelta(days=90)

year, month = today.year, today.month
week_number = ((today.day - 1) // 7) + 1

col_title, col_blank, col_query, col_csv = st.columns([2, 2, 1, 1])
with col_title:
    st.markdown(f"#### 📅 {year}년 {month}월 {week_number}주차")
with col_blank:
    st.empty()
with col_query:
    run_query = st.button("📥 조회하기", use_container_width=True)
with col_csv:
    st.download_button(
        label="📄 CSV 저장",
        data=st.session_state.csv_data if st.session_state.csv_data else "",
        file_name=f"Index_Summary_{today.strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=st.session_state.csv_data is None
    )

# 조회 버튼 클릭 시 초기화
if run_query:
    st.session_state.df_final = pd.DataFrame()
    st.session_state.df_raw = pd.DataFrame()
    st.session_state.csv_data = None
    st.session_state.query_done = False

# 초기 테이블 생성
if run_query and selected_items:
    records = []
    week_dates = pd.date_range(start=start_of_week, end=end_of_week)
    week_columns = [f"{d.month}월{d.day}일({weekday_map[d.weekday()]})" for d in week_dates]

    for row in selected_items:
        record = {
            "국가": row["국가"],
            "구분": row["구분"],
            "항목": row["항목명_짧은"],
            "기준값(전일)": None,
            "변동률 (%)": None,
            "평균값(3개월)": None,
            **{col: None for col in week_columns}
        }
        records.append(record)

    df_init = pd.DataFrame(records)
    df_raw_init = df_init.copy()

    category_sort = {"지표": 0, "환율": 1, "사료": 2}
    df_init["구분정렬"] = df_init["구분"].map(category_sort)
    df_raw_init["구분정렬"] = df_raw_init["구분"].map(category_sort)

    df_init = df_init.sort_values(["국가", "구분정렬", "항목"]).drop(columns="구분정렬").reset_index(drop=True)
    df_raw_init = df_raw_init.sort_values(["국가", "구분정렬", "항목"]).drop(columns="구분정렬").reset_index(drop=True)

    st.session_state.df_final = df_init
    st.session_state.df_raw = df_raw_init

# 데이터 조회
if run_query and selected_items:
    with st.spinner("데이터 조회 중입니다..."):
        for row in selected_items:
            try:
                data = yf.download(
                    row["티커"],
                    start=three_months_ago.strftime("%Y-%m-%d"),
                    end=(today + timedelta(days=1)).strftime("%Y-%m-%d"),
                    progress=False
                )
                if data.empty:
                    continue

                close_prices = data["Close"]
                if isinstance(close_prices, pd.DataFrame) and row["티커"] in close_prices.columns:
                    close_prices = close_prices[row["티커"]]
                close_dict = {d.date(): round(v, 2) for d, v in close_prices.items() if not pd.isna(v)}

                week_data = [
                    round(close_dict.get(d.date(), float('nan')), 2) if not pd.isna(close_dict.get(d.date(), float('nan'))) else None
                    for d in week_dates
                ]

                past_dates = sorted(
                    [d for d, v in close_dict.items() if d < today.date() and v not in (None, 0) and not pd.isna(v)],
                    reverse=True
                )

                if len(past_dates) >= 2:
                    latest_date, second_latest_date = past_dates[0], past_dates[1]
                    prev_day_value = close_dict[latest_date]
                    change_rate = (close_dict[second_latest_date] - prev_day_value) / close_dict[second_latest_date] * 100 if close_dict[second_latest_date] != 0 else None
                else:
                    prev_day_value, change_rate = None, None

                avg_3months = round(pd.Series(
                    [v for d, v in close_dict.items() if three_months_ago.date() <= d <= today.date()]
                ).mean(), 2) if close_dict else None

                idx_final = (st.session_state.df_final["국가"] == row["국가"]) & (st.session_state.df_final["항목"] == row["항목명_짧은"])
                idx_raw = (st.session_state.df_raw["국가"] == row["국가"]) & (st.session_state.df_raw["항목"] == row["항목명_짧은"])

                for i, col in enumerate(week_columns):
                    st.session_state.df_final.loc[idx_final, col] = week_data[i]
                    st.session_state.df_raw.loc[idx_raw, col] = week_data[i]

                st.session_state.df_final.loc[idx_final, "기준값(전일)"] = prev_day_value
                st.session_state.df_raw.loc[idx_raw, "기준값(전일)"] = prev_day_value
                st.session_state.df_final.loc[idx_final, "변동률 (%)"] = f"{change_rate:.2f}%" if change_rate is not None else None
                st.session_state.df_raw.loc[idx_raw, "변동률 (%)"] = change_rate
                st.session_state.df_final.loc[idx_final, "평균값(3개월)"] = avg_3months
                st.session_state.df_raw.loc[idx_raw, "평균값(3개월)"] = avg_3months

            except Exception as e:
                st.warning(f"{row['항목명_짧은']} 에러: {e}")

    st.session_state.csv_data = st.session_state.df_raw.to_csv(index=False).encode("utf-8-sig")
    st.session_state.query_done = True
    st.rerun()

# 메시지 출력
if st.session_state.query_done:
    st.success("✅ 데이터 조회 완료되었습니다.")
else:
    st.error("📥 조회 버튼을 눌러주세요.")

# 테이블 출력 (가운데 정렬)
if st.session_state.df_final is not None and not st.session_state.df_final.empty:

    def format_cell(val):
        try:
            val = float(val)
            return f"{int(round(val)):,}" if val >= 1000 else f"{val:.2f}"
        except:
            return val

    def style_row(row):
        styles = []
        for col in row.index:
            cell_style = ""
            if row["구분"] == "지표":
                cell_style += 'background-color: #e5f3ff;'
            if "변동률" in col:
                try:
                    value = float(str(row[col]).replace("%", "")) if isinstance(row[col], str) else row[col]
                    if value > 0:
                        cell_style += 'color: blue;'
                    elif value < 0:
                        cell_style += 'color: red;'
                except:
                    pass
            if col == "기준값(전일)":  # ✅ 기준값(전일) 컬럼은 bold
                cell_style += 'font-weight: bold;'
            if col in ["국가", "구분", "항목"]:
                cell_style += 'text-align: left;'
            else:
                cell_style += 'text-align: right;'
            styles.append(cell_style)
        return styles

    styled_table = (
        st.session_state.df_final
        .style
        .format(format_cell, na_rep="")
        .apply(style_row, axis=1)
    )

    st.write(
        styled_table.to_html(index=False),
        unsafe_allow_html=True
    )
