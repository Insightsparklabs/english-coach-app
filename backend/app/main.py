from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# アプリケーションの初期化
app = FastAPI()

# CORS設定 (超重要)
# Frontend (Next.js) からのアクセスを許可するために必要です。
# 本番環境では特定のドメインのみに絞りますが、開発中は全許可(*)で進めます。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ヘルスチェック用エンドポイント
# これが動けば、Dockerの設定は成功です。
@app.get("/")
def read_root():
    return {"status": "ok", "message": "English Coach Backend is running" }
    