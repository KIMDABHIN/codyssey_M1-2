
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


# 프로젝트 최상위 폴더의 .env 파일 읽기
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")


def explain_price_report(report: dict) -> str:
    """가격 분석 결과를 Gemini AI가 자연어로 설명한다."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY가 없습니다. 프로젝트 최상위 폴더의 .env 파일을 확인해 주세요."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
너는 농산물 가격 데이터를 설명하는 AI 도우미야.

아래 가격 분석 결과만 근거로 한국어 해설을 작성해 줘.

분석 결과:
{report}

작성 규칙:
1. 현재 가격과 전월 대비 변화를 설명해.
2. 전년 동월 대비 변화도 설명해.
3. 최근 3년 같은 달 평균과 비교해.
4. 비교 데이터가 없는 항목은 추측하지 말고 생략해.
5. 가격 변화의 원인을 근거 없이 단정하지 마.
6. 이해하기 쉬운 자연스러운 문장으로 3~5문장 작성해.
7. 입력된 수치와 변화율을 임의로 바꾸지 마.
8. 가격 단위가 제공되지 않았다면 임의로 단위를 붙이지 마.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
        )
    except Exception as e:
        print(f"Gemini 오류 종류: {type(e).__name__}")
        print(f"Gemini 오류 내용: {e}")
        raise

    if not response.text:
        raise RuntimeError("Gemini에서 해설을 받아오지 못했습니다.")

    return response.text.strip()
