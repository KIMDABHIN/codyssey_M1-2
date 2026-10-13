
from fastapi import APIRouter, HTTPException, Query

from app.services.price_service import get_price_report
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

    # 계산 결과를 Gemini AI에 전달한다.
    try:
        explanation = explain_price_report(report)

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=(
                "AI 해설 생성에 실패했습니다. "
                ".env의 API 키, 모델 이용 가능 여부, 사용량 한도를 확인해 주세요."
                f" 오류 유형: {type(e).__name__}"
            ),
        ) from e

    return {
        "분석 결과": report,
        "AI 해설": explanation,
    }
