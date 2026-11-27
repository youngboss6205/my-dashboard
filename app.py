import os  # 파일이 있는지 확인할 때 사용 (파이썬 기본 기능)

import pandas as pd  # 표 데이터를 다루는 라이브러리 (Python 안의 엑셀)
import streamlit as st  # 웹 화면을 만드는 라이브러리

# ── 기본 설정 ─────────────────────────────────────────
DATA_FILE = "sales_sample.csv"  # 내 폴더 기준 상대경로 (배포해도 그대로 동작)
NEED_COLS = ["date", "region", "category", "sales", "quantity"]  # 꼭 있어야 하는 열

st.set_page_config(page_title="영업팀 매출 현황", layout="wide")  # 페이지를 넓게 사용
st.title("영업팀 매출 현황")  # 맨 위 제목
st.caption("데이터 기준: 2026년 1~10월 · 출처: sales_sample.csv")  # 제목 아래 작은 설명


# ── 1) 데이터 불러오기 ─────────────────────────────────
@st.cache_data  # 조건을 바꿔 재실행돼도 파일은 한 번만 읽도록 결과를 기억
def load_data(path):
    df = pd.read_csv(path, parse_dates=["date"])  # CSV 읽기, date 열은 날짜로
    return df


# 방어 코드 ①: 파일이 없으면 안내 후 멈춤
if not os.path.exists(DATA_FILE):
    st.error(f"데이터 파일({DATA_FILE})을 찾을 수 없습니다. 파일 이름과 위치(app.py와 같은 폴더)를 확인해 주세요.")
    st.stop()  # 여기서 화면 그리기를 멈춤

df = load_data(DATA_FILE)

# 방어 코드 ②: 필요한 열이 없으면 어떤 열이 없는지 알려 주고 멈춤
missing = [c for c in NEED_COLS if c not in df.columns]
if missing:
    st.error(f"CSV에 필요한 열이 없습니다: {', '.join(missing)}. 열 이름을 확인해 주세요.")
    st.stop()

# ── 2) 사이드바 조건 위젯 ──────────────────────────────
st.sidebar.header("조건 선택")

# 지역: 여러 개 선택, 기본은 전체 선택
all_regions = sorted(df["region"].unique())
regions = st.sidebar.multiselect("지역", all_regions, default=all_regions)

# 카테고리: 드롭다운 하나 고르기, '전체' 포함
category = st.sidebar.selectbox("카테고리", ["전체"] + sorted(df["category"].unique()))

# 기간: 월 단위 슬라이더 (1월~10월)
min_m, max_m = int(df["date"].dt.month.min()), int(df["date"].dt.month.max())
month_range = st.sidebar.slider("기간(월)", min_m, max_m, (min_m, max_m))

# ── 3) 필터: 조건에 맞는 행만 골라 filtered 만들기 ─────────
filtered = df[
    df["region"].isin(regions)  # 고른 지역 중 하나에 해당
    & df["date"].dt.month.between(month_range[0], month_range[1])  # 기간 범위 안
]
if category != "전체":  # '전체'가 아니면 고른 카테고리만 남김
    filtered = filtered[filtered["category"] == category]

st.sidebar.write(f"선택 조건: {len(filtered)}건 / 전체 {len(df)}건")  # 걸러진 건수 표시

# ── 4) 0건 처리: 필터 아래, 지표·그래프 위에서 검사 ─────────
if filtered.empty:
    st.info("선택한 조건에 맞는 데이터가 0건입니다. 지역을 하나 이상 고르거나 기간·카테고리 조건을 넓혀 보세요.")
    st.stop()  # 지표·그래프·표는 그리지 않음 (nan, 빈 그래프 방지)

# ── 5) 화면: 요약 탭 / 상세 데이터 탭 ─────────────────────
tab1, tab2 = st.tabs(["요약", "상세 데이터"])

with tab1:
    # 지표 카드 3개 (가로 배치)
    total = filtered["sales"].sum()  # 총 매출
    count = len(filtered)  # 주문 건수
    avg = total / count  # 평균 주문액 (0건은 위에서 막았으므로 안전)
    c1, c2, c3 = st.columns(3)
    c1.metric("총 매출", f"{total:,.0f}원")
    c2.metric("주문 건수", f"{count:,}건")
    c3.metric("평균 주문액", f"{avg:,.0f}원")

    # 월별 매출 추이: 선 그래프
    st.subheader("월별 매출 추이")
    monthly = filtered.groupby(filtered["date"].dt.month)["sales"].sum()  # 월별 합계
    monthly.index = [f"{m:02d}월" for m in monthly.index]  # 1 → "01월" (순서 유지)
    st.line_chart(monthly)

    # 지역별 매출: 큰 순서 막대 그래프
    st.subheader("지역별 매출 (큰 순서)")
    by_region = filtered.groupby("region")["sales"].sum().sort_values(ascending=False)
    st.bar_chart(by_region, sort=False)  # sort=False: 정렬해 둔 순서 그대로 표시

with tab2:
    # 상세 표: 화면 폭에 맞추고 행 번호 숨김
    st.dataframe(filtered, width="stretch", hide_index=True)

# ── 6) 경영 판단 한 줄 ──────────────────────────────────
st.divider()
st.markdown(
    "**이 화면으로 내릴 수 있는 경영 판단:** 전자제품은 주문 건수는 적지만 매출 비중이 커서, "
    "지역별 전자제품 실적을 보고 판촉 예산을 배분할 수 있다."
)
