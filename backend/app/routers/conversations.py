from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.supabase_service import get_supabase_client


router = APIRouter(
    prefix="/api/conversations",
    tags=["Conversations"],
)


class ConversationCreate(BaseModel):
    title: str = "새로운 대화"
    messages: list[dict[str, Any]] = Field(default_factory=list)


class ConversationUpdate(BaseModel):
    title: str | None = None
    messages: list[dict[str, Any]] | None = None


@router.post("")
def create_conversation(data: ConversationCreate):
    """새로운 대화를 저장한다."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("conversations")
            .insert({
                "title": data.title,
                "messages": data.messages,
            })
            .execute()
        )

        return {
            "message": "대화 저장 성공",
            "data": result.data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"대화 저장 실패: {str(e)}",
        ) from e


@router.get("")
def get_conversations():
    """저장된 대화 목록을 조회한다."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("conversations")
            .select("*")
            .order("updated_at", desc=True)
            .execute()
        )

        return {
            "message": "대화 목록 조회 성공",
            "data": result.data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"대화 목록 조회 실패: {str(e)}",
        ) from e


@router.get("/{conversation_id}")
def get_conversation(conversation_id: int):
    """특정 대화의 내용을 조회한다."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="해당 대화를 찾을 수 없습니다.",
            )

        return {
            "message": "대화 조회 성공",
            "data": result.data[0],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"대화 조회 실패: {str(e)}",
        ) from e


@router.put("/{conversation_id}")
def update_conversation(
    conversation_id: int,
    data: ConversationUpdate,
):
    """대화 제목이나 메시지를 수정한다."""
    try:
        supabase = get_supabase_client()

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="수정할 내용이 없습니다.",
            )

        result = (
            supabase.table("conversations")
            .update(update_data)
            .eq("id", conversation_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="수정할 대화를 찾을 수 없습니다.",
            )

        return {
            "message": "대화 수정 성공",
            "data": result.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"대화 수정 실패: {str(e)}",
        ) from e


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int):
    """특정 대화를 삭제한다."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("conversations")
            .delete()
            .eq("id", conversation_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="삭제할 대화를 찾을 수 없습니다.",
            )

        return {
            "message": "대화 삭제 성공",
            "data": result.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"대화 삭제 실패: {str(e)}",
        ) from e