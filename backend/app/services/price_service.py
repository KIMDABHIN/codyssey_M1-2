
from pathlib import Path

import pandas as pd


# 프로젝트의 CSV 파일 경로
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "data" / "processed" / "농산물_월별가격.csv"


def load_price_data():
    """정리된 농산물 월별 가격 데이터를 불러온다."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"가격 데이터 파일을 찾을 수 없습니다: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["가격"] = pd.to_numeric(df["가격"], errors="coerce")

    df = df.dropna(subset=["날짜"])
    df = df.sort_values(["품목", "날짜"]).reset_index(drop=True)

    return df


def get_price_report(product: str, target_date: str):
    """선택한 품목과 월의 가격 및 비교 지표를 계산한다."""

    df = load_price_data()

    # 입력한 날짜를 해당 월의 첫날로 변환한다.
    try:
        selected_date = pd.to_datetime(target_date).to_period("M").to_timestamp()
    except (ValueError, TypeError):
        raise ValueError("날짜는 YYYY-MM 형식으로 입력해 주세요. 예: 2026-08")

    product_df = df[df["품목"] == product].copy()

    if product_df.empty:
        available_products = sorted(df["품목"].dropna().unique().tolist())
        raise ValueError(
            f"'{product}' 품목을 찾을 수 없습니다. "
            f"사용 가능한 품목: {', '.join(available_products)}"
        )

    # 선택한 월의 데이터
    current_rows = product_df[product_df["날짜"] == selected_date]

    if current_rows.empty:
        raise ValueError(
            f"{product}의 {selected_date:%Y-%m} 데이터가 없습니다."
        )

    current_price = current_rows.iloc[0]["가격"]

    if pd.isna(current_price):
        raise ValueError(
            f"{product}의 {selected_date:%Y-%m} 가격은 현재 확인할 수 없습니다."
        )

    current_price = float(current_price)

    # 전월 가격
    previous_month = selected_date - pd.DateOffset(months=1)
    previous_rows = product_df[product_df["날짜"] == previous_month]
    previous_price = (
        previous_rows.iloc[0]["가격"] if not previous_rows.empty else None
    )

    # 전년 동월 가격
    previous_year = selected_date - pd.DateOffset(years=1)
    previous_year_rows = product_df[product_df["날짜"] == previous_year]
    previous_year_price = (
        previous_year_rows.iloc[0]["가격"]
        if not previous_year_rows.empty
        else None
    )

    # 최근 3년 같은 달 평균: 선택한 연도는 제외하고 이전 3개 연도를 사용한다.
    same_month_history = product_df[
        (product_df["날짜"].dt.month == selected_date.month)
        & (product_df["날짜"].dt.year >= selected_date.year - 3)
        & (product_df["날짜"].dt.year < selected_date.year)
    ]

    history_prices = same_month_history["가격"].dropna()
    three_year_average = (
        float(history_prices.mean()) if not history_prices.empty else None
    )

    def calculate_change(reference_price):
        """기준 가격이 없거나 0이면 변화율을 계산하지 않는다."""
        if reference_price is None or pd.isna(reference_price):
            return None

        reference_price = float(reference_price)

        if reference_price == 0:
            return None

        return round(
            (current_price - reference_price) / reference_price * 100,
            2,
        )

    return {
        "품목": product,
        "기준월": selected_date.strftime("%Y-%m"),
        "가격": current_price,
        "전월": (
            float(previous_price)
            if previous_price is not None and pd.notna(previous_price)
            else None
        ),
        "전월 대비 변화율(%)": calculate_change(previous_price),
        "전년 동월": (
            float(previous_year_price)
            if previous_year_price is not None
            and pd.notna(previous_year_price)
            else None
        ),
        "전년 동월 대비 변화율(%)": calculate_change(previous_year_price),
        "최근 3년 같은 달 평균": (
            round(three_year_average, 2)
            if three_year_average is not None
            else None
        ),
        "최근 3년 평균 대비 변화율(%)": calculate_change(
            three_year_average
        ),
        "최근 3년 비교에 사용한 연도 수": int(len(history_prices)),
    }
