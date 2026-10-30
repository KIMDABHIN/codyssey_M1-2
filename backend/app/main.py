
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routers.prices import router as prices_router
from app.routers import user_data, conversations, chat


app = FastAPI(
    title="AI 농산물 가격 리포트",
    description="월별 농산물 가격을 비교하고 분석하는 API",
    version="1.0.0",
)

app.include_router(prices_router)
app.include_router(user_data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


# 프로젝트 폴더와 웹페이지 파일 위치 설정
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_FILE = PROJECT_ROOT / "frontend" / "index.html"


@app.get("/")
def read_root():
    return FileResponse(FRONTEND_FILE)


@app.get("/health")
def health_check():
    return {"status": "ok"}
