from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# ルーターをインポート
from app.routers import auth, stocks, ai
from app.core.database import engine
from app.models.database import Base

# 環境変数を読み込み
load_dotenv()

# データベーステーブル作成
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="コトリの株ノート API",
    description="投資初心者向けAI株価分析アプリのAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを追加
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(ai.router)

@app.get("/")
async def root():
    return {
        "message": "コトリの株ノート API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
        "supabase_configured": bool(os.getenv("SUPABASE_URL"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)