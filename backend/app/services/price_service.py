
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


def calculate_change(current_price, reference_price):
    """기준 가격 대비 변화율을 계산한다."""
    if (
        current_price is None
        or reference_price is None
        or pd.isna(current_price)
        or pd.isna(reference_price)
        or float(reference_price) == 0
    ):
        return None

    return round(
        (float(current_price) - float(reference_price))
        / float(reference_price) * 100,
        2,
    )


def get_price_report(product: str, target_date: str):
    """가격 비교 결과와 구매 판단을 계산한다."""
    df = load_price_data()

    try:
        selected_date = pd.to_datetime(
            target_date
        ).to_period("M").to_timestamp()
    except (ValueError, TypeError):
        raise ValueError(
            "날짜는 YYYY-MM 형식으로 입력해 주세요. 예: 2026-08"
        )

    product_df = df[df["품목"] == product].copy()

    if product_df.empty:
        available_products = sorted(
            df["품목"].dropna().unique().tolist()
        )
        raise ValueError(
            f"'{product}' 품목을 찾을 수 없습니다. "
            f"사용 가능한 품목: {', '.join(available_products)}"
        )

    current_rows = product_df[
        product_df["날짜"] == selected_date
    ]

    if current_rows.empty or pd.isna(current_rows.iloc[0]["가격"]):
        raise ValueError(
            f"{product}의 {selected_date:%Y-%m} 가격 데이터를 "
            "확인할 수 없습니다."
        )

    current_price = float(current_rows.iloc[0]["가격"])

    # 전월 및 전년 동월 가격
    previous_month = selected_date - pd.DateOffset(months=1)
    previous_year = selected_date - pd.DateOffset(years=1)

    def get_price_at(date):
        rows = product_df[product_df["날짜"] == date]
        if rows.empty or pd.isna(rows.iloc[0]["가격"]):
            return None
        return float(rows.iloc[0]["가격"])

    previous_price = get_price_at(previous_month)
    previous_year_price = get_price_at(previous_year)

   
    # 최근 3년 같은 달 평균
    # 선택한 월보다 이전 3개 연도의 동일 월만 비교한다.
    start_year = selected_date.year - 3

    same_month_history = product_df.loc[
        product_df["날짜"].dt.month.eq(selected_date.month)
        & product_df["날짜"].dt.year.between(
            start_year, selected_date.year - 1
        ),
        ["날짜", "가격"],
    ].copy()

    history_prices = same_month_history["가격"].dropna()

    three_year_average = (
        float(history_prices.mean())
        if len(history_prices) > 0
        else None
    )

    # 비교 지표
    previous_month_change = calculate_change(
        current_price, previous_price
    )
    previous_year_change = calculate_change(
        current_price, previous_year_price
    )
    average_change = calculate_change(
        current_price, three_year_average
    )

    # 구매 판단
    if average_change is None or len(history_prices) < 2:
        price_status = "판단 자료 부족"
        purchase_opinion = "아직 판단하기 어려워요"
        purchase_reason = (
            "비교에 사용할 과거 가격 자료가 충분하지 않아요."
        )
    elif average_change <= -10:
        price_status = "평균보다 저렴"
        purchase_opinion = "구매하기 좋은 가격대예요"
        purchase_reason = (
            "최근 3년 같은 달 평균보다 10% 이상 낮은 가격이에요."
        )
    elif average_change >= 10:
        price_status = "평균보다 비쌈"
        purchase_opinion = "가격을 조금 더 비교해 보세요"
        purchase_reason = (
            "최근 3년 같은 달 평균보다 10% 이상 높은 가격이에요."
        )
    else:
        price_status = "평균과 비슷"
        purchase_opinion = "평소와 비슷한 가격이에요"
        purchase_reason = (
            "최근 3년 같은 달 평균과 비교해 큰 차이가 없는 편이에요."
        )

    return {
        "품목": product,
        "기준월": selected_date.strftime("%Y-%m"),
        "가격": current_price,
        "전월": previous_price,
        "전월 대비 변화율(%)": previous_month_change,
        "전년 동월": previous_year_price,
        "전년 동월 대비 변화율(%)": previous_year_change,
        "최근 3년 같은 달 평균": (
            round(three_year_average, 2)
            if three_year_average is not None
            else None
        ),
        "최근 3년 평균 대비 변화율(%)": average_change,
        "최근 3년 비교에 사용한 연도 수": int(len(history_prices)),
        "가격 수준": price_status,
        "구매 의견": purchase_opinion,
        "구매 판단 근거": purchase_reason,
    }


def _predict_from_history(history, forecast_date):
    """
    예측 기준일 이전 데이터만 사용한다.

    우선 전년도 같은 달 가격을 사용하고,
    없으면 직전의 관측 가격 최대 3개의 평균을 사용한다.
    """
    history = history[
        (history["날짜"] < forecast_date)
        & history["가격"].notna()
    ].sort_values("날짜")

    if history.empty:
        return None, "사용 가능한 과거 가격 자료 없음"

    seasonal_date = forecast_date - pd.DateOffset(years=1)
    seasonal_rows = history[history["날짜"] == seasonal_date]

    if not seasonal_rows.empty:
        return (
            float(seasonal_rows.iloc[0]["가격"]),
            "전년도 같은 달 가격을 사용한 계절성 기준 예측",
        )

    recent_prices = history["가격"].tail(3)

    return (
        float(recent_prices.mean()),
        "최근 관측 가격 최대 3개의 평균을 사용한 기준 예측",
    )


def get_price_forecast(product: str, target_month: str):
    """
    선택한 월까지의 가격 데이터로 다음 달 가격을 예측한다.
    과거 예측 성능도 같은 기준 모델로 검증한다.
    """
    df = load_price_data()

    try:
        selected_date = pd.to_datetime(
            target_month
        ).to_period("M").to_timestamp()
    except (ValueError, TypeError):
        raise ValueError(
            "날짜는 YYYY-MM 형식으로 입력해 주세요. 예: 2026-08"
        )

    product_df = df[df["품목"] == product].copy()

    if product_df.empty:
        available_products = sorted(
            df["품목"].dropna().unique().tolist()
        )
        raise ValueError(
            f"'{product}' 품목을 찾을 수 없습니다. "
            f"사용 가능한 품목: {', '.join(available_products)}"
        )

    selected_rows = product_df[
        product_df["날짜"] == selected_date
    ]

    if selected_rows.empty or pd.isna(selected_rows.iloc[0]["가격"]):
        raise ValueError(
            f"{product}의 {selected_date:%Y-%m} 가격 데이터를 "
            "확인할 수 없습니다."
        )

    # 선택한 월 이후의 데이터는 예측에 사용하지 않는다.
    history = product_df[
        (product_df["날짜"] <= selected_date)
        & product_df["가격"].notna()
    ].copy()

    forecast_date = selected_date + pd.DateOffset(months=1)

    predicted_price, method = _predict_from_history(
        history, forecast_date
    )

    if predicted_price is None:
        raise ValueError("예측에 사용할 과거 가격 자료가 부족합니다.")

    # 과거 각 월을 예측 시점으로 삼아 성능을 검증한다.
    actual_values = []
    predicted_values = []

    evaluation_rows = history.sort_values("날짜")

    for _, row in evaluation_rows.iterrows():
        evaluation_date = row["날짜"]

        earlier_history = product_df[
            (product_df["날짜"] < evaluation_date)
            & product_df["가격"].notna()
        ]

        historical_prediction, _ = _predict_from_history(
            earlier_history, evaluation_date
        )

        if historical_prediction is not None:
            actual_values.append(float(row["가격"]))
            predicted_values.append(float(historical_prediction))

    if actual_values:
        errors = [
            abs(actual - predicted)
            for actual, predicted in zip(
                actual_values, predicted_values
            )
        ]
        mae = sum(errors) / len(errors)

        percentage_errors = [
            abs(actual - predicted) / abs(actual) * 100
            for actual, predicted in zip(
                actual_values, predicted_values
            )
            if actual != 0
        ]

        mape = (
            sum(percentage_errors) / len(percentage_errors)
            if percentage_errors
            else None
        )
    else:
        mae = None
        mape = None

    return {
        "품목": product,
        "기준월": selected_date.strftime("%Y-%m"),
        "예측월": forecast_date.strftime("%Y-%m"),
        "예측 가격": round(predicted_price, 2),
        "예측 방법": method,
        "과거 검증 건수": len(actual_values),
        "평균 절대 오차(MAE)": (
            round(mae, 2) if mae is not None else None
        ),
        "평균 절대 백분율 오차(MAPE, %)": (
            round(mape, 2) if mape is not None else None
        ),
        "안내": (
            "과거 가격을 이용한 기준 예측이며 실제 가격을 보장하지 않습니다. "
            "MAE와 MAPE는 과거 검증 구간에서 계산한 오차 지표입니다."
        ),
    }


