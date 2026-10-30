
import os

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()


def get_supabase_client() -> Client:
    """환경변수에서 Supabase 설정을 읽어 연결 객체를 반환한다."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다. "
            ".env 파일이나 Codespaces 환경변수를 확인해 주세요."
        )

    return create_client(url, key)
