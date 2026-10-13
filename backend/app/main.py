from fastapi import FastAPI

from app.routers.prices import router as prices_router


app = FastAPI(
    title="AI 농산물 가격 리포트",
    description="월별 농산물 가격을 비교하고 분석하는 API",
    version="1.0.0",
)

app.include_router(prices_router)


@app.get("/")
def read_root():
    return {
        "message": "AI 농산물 가격 리포트 API가 실행 중입니다."
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
