
from fastapi import APIRouter, HTTPException, Query

from app.services.price_service import (
    get_price_report,
    get_price_forecast,
)
from app.services.ai_service import explain_price_report


router = APIRouter(
    prefix="/api/prices",
    tags=["농산물 가격"],
)


@router.get("")
def read_price_report(
    product: str = Query(..., description="조회할 농산물 품목"),
    month: str = Query(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="조회할 월 (예: 2026-08)",
    ),
):
    """품목과 월을 받아 농산물 가격 분석 결과를 반환한다."""

    try:
        return get_price_report(product, month)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail="가격 데이터 파일을 찾을 수 없습니다.",
        ) from e


@router.get("/explain")
def read_price_explanation(
    product: str = Query(..., description="조회할 농산물 품목"),
    month: str = Query(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="조회할 월 (예: 2026-08)",
    ),
):
    """가격 비교 결과를 계산하고 Gemini AI 해설을 반환한다."""

    # 먼저 가격 분석 결과를 계산한다.
    try:
        report = get_price_report(product, month)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail="가격 데이터 파일을 찾을 수 없습니다.",
        ) from e

   
    # Gemini AI 해설 생성 중 발생한 오류 처리
    try:
        explanation = explain_price_report(report)

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=(
                "AI 해설 생성에 실패했습니다. "
                f"오류 유형: {type(e).__name__}, "
                f"오류 내용: {str(e)}"
            ),
        ) from e

    return {
        "분석 결과": report,
        "AI 해설": explanation,
    }

@router.get("/forecast")
def read_price_forecast(
    product: str = Query(..., description="조회할 농산물 품목"),
    month: str = Query(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="예측 기준 월 (예: 2026-08)",
    ),
):
    """과거 가격 데이터를 이용해 다음 달 가격을 예측한다."""

    try:
        return get_price_forecast(product, month)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail="가격 데이터 파일을 찾을 수 없습니다.",
        ) from e

@router.get("/history")
def read_price_history(
    product: str = Query(..., description="조회할 농산물 품목"),
):
    """선택한 농산물의 월별 가격 이력을 반환한다."""
    from app.services.price_service import load_price_data

    try:
        df = load_price_data()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail="가격 데이터 파일을 찾을 수 없습니다.",
        ) from e

    product_df = df[df["품목"] == product].copy()

    if product_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"'{product}' 품목을 찾을 수 없습니다.",
        )

    product_df = product_df.dropna(subset=["가격"]).sort_values("날짜")

    return {
        "품목": product,
        "데이터": [
            {
                "날짜": row["날짜"].strftime("%Y-%m"),
                "가격": float(row["가격"]),
            }
            for _, row in product_df.iterrows()
        ],
    }
