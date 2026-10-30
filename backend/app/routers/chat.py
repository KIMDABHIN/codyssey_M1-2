from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.gemini_chat_service import generate_chat_response
from app.services.supabase_service import get_supabase_client


router = APIRouter(
    prefix="/api/chat",
    tags=["AI Chat"],
)


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


@router.post("")
def chat(data: ChatRequest):
    try:
        supabase = get_supabase_client()

        # 사용자가 보낸 질문
        user_message = {
            "role": "user",
            "content": data.message,
        }

        # 기존 대화인지 새 대화인지 확인
        if data.conversation_id is not None:
            result = (
                supabase.table("conversations")
                .select("*")
                .eq("id", data.conversation_id)
                .execute()
            )

            if not result.data:
                raise HTTPException(
                    status_code=404,
                    detail="해당 대화를 찾을 수 없습니다.",
                )

            conversation = result.data[0]
            messages = conversation["messages"] + [user_message]
            conversation_id = data.conversation_id

        else:
            messages = [user_message]
            conversation_id = None

        # OpenAI에 질문 전달
        answer = generate_chat_response(messages)

        # AI 답변 추가
        assistant_message = {
            "role": "assistant",
            "content": answer,
        }

        messages.append(assistant_message)

        # 대화 제목 생성
        title = data.message[:30]

        # 현재 시간
        now = datetime.now(timezone.utc).isoformat()

        # 새 대화 저장
        if conversation_id is None:
            result = (
                supabase.table("conversations")
                .insert({
                    "title": title,
                    "messages": messages,
                    "updated_at": now,
                })
                .execute()
            )

            conversation_id = result.data[0]["id"]

        # 기존 대화 업데이트
        else:
            supabase.table("conversations").update({
                "messages": messages,
                "updated_at": now,
            }).eq("id", conversation_id).execute()

        return {
            "message": "AI 답변 생성 성공",
            "conversation_id": conversation_id,
            "answer": answer,
            "messages": messages,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 채팅 처리 실패: {str(e)}",
        ) from e