import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# さっき作った db.py から関数をインポート！
from .db import get_supabase_client

# .env読み込み
load_dotenv()

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Supabaseクライアントを取得（db.pyにお任せ）
supabase = get_supabase_client()

# 2. Gemini接続設定（ここはmain.pyでやる）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Gemini initialized")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
else:
    print("⚠️ Warning: GEMINI_API_KEY not found in .env")

# チャットのデータ形式
class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    # データベースの状態も確認して表示
    db_status = "Connected" if supabase else "Disconnected"
    return {
        "status": "ok", 
        "message": "English Coach AI Backend is running",
        "database": db_status
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Gemini API is not configured")

    try:
        # AIに聞く
        response = model.generate_content(request.message)
        
        # 将来的にここで「会話履歴をSupabaseに保存」するコードを追加できます
        # if supabase:
        #     supabase.table("chats").insert({...})

        return {
            "user_message": request.message,
            "ai_response": response.text
        }
    except Exception as e:
        return {"error": str(e)}