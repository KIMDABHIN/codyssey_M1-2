import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def generate_chat_response(messages: list[dict]) -> str:
    """OpenAI를 이용해 사용자 질문에 답변한다."""

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해 주세요."
        )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=(
            "너는 AI 농산물 가격 리포트 서비스의 전문 AI 상담사야. "
            "사용자의 질문에 친절하고 이해하기 쉽게 한국어로 답변해 줘. "
            "농산물 가격과 관련된 질문에는 근거가 있는 정보와 "
            "추측을 구분해서 설명해 줘. "
            "제공되지 않은 가격이나 통계는 임의로 만들어 내지 마."
        ),
        input=messages,
    )

    return response.output_text