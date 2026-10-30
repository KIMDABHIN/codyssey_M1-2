from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.supabase_service import get_supabase_client


router = APIRouter(
    prefix="/api/user-data",
    tags=["사용자 데이터"],
)


class UserDataCreate(BaseModel):
    date: date
    value: float
    memo: Optional[str] = None


class UserDataUpdate(BaseModel):
    date: Optional[str] = None
    value: Optional[float] = None
    memo: Optional[str] = None


@router.post("")
def create_user_data(data: UserDataCreate):
    """새로운 데이터를 저장한다."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("user_data")
            .insert(data.model_dump(mode="json"))
            .execute()
        )

        return {
            "message": "데이터 저장 성공",
            "data": result.data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"데이터 저장 실패: {str(e)}",
        ) from e


@router.get("")
def read_user_data():
    """저장된 데이터 목록을 조회한다."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("user_data")
            .select("*")
            .order("date", desc=True)
            .execute()
        )

        return {
            "count": len(result.data),
            "data": result.data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"데이터 조회 실패: {str(e)}",
        ) from e


@router.put("/{data_id}")
def update_user_data(data_id: int, data: UserDataUpdate):
    """기존 데이터를 수정한다."""
    try:
        supabase = get_supabase_client()

        update_values = data.model_dump(
            mode="json",
            exclude_unset=True,
        )

        if not update_values:
            raise HTTPException(
                status_code=400,
                detail="수정할 데이터를 입력해 주세요.",
            )

        result = (
            supabase.table("user_data")
            .update(update_values)
            .eq("id", data_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="해당 데이터를 찾을 수 없습니다.",
            )

        return {
            "message": "데이터 수정 성공",
            "data": result.data,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"데이터 수정 실패: {str(e)}",
        ) from e


@router.delete("/{data_id}")
def delete_user_data(data_id: int):
    """기존 데이터를 삭제한다."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("user_data")
            .delete()
            .eq("id", data_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="해당 데이터를 찾을 수 없습니다.",
            )

        return {
            "message": "데이터 삭제 성공",
            "data": result.data,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"데이터 삭제 실패: {str(e)}",
        ) from e