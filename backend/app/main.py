from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import traceback

# 設定とプロンプトの読み込み
try:
    from .config import ADMIN_USER_ID, MODEL_NAME, model as gemini_base_model
    from .db import get_supabase_client
    from .prompts import get_coach_instruction
except ImportError:
    from app.config import ADMIN_USER_ID, MODEL_NAME, model as gemini_base_model
    from app.db import get_supabase_client
    from app.prompts import get_coach_instruction

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = get_supabase_client()

# 🌟 起動時にモデル一覧を表示（デバッグ用）
@app.on_event("startup")
async def list_models():
    print("--- 🔍 利用可能なGoogle AIモデル一覧 ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
    except Exception as e:
        print(f"❌ モデルリスト取得失敗: {e}")
    print("---------------------------------------")

# 🌟 ChatRequestを統合（一つにまとめました）
class ChatRequest(BaseModel):
    message: str
    user_id: str  
    level: str
    mode: str = "assessment" 

@app.get("/")
def read_root():
    db_status = "Connected" if supabase else "Disconnected"
    return {"status": "ok", "database": db_status}

@app.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    if not gemini_base_model:
        raise HTTPException(status_code=500, detail="Gemini API is not configured")

    try:
        # 1. 👑 1日50回制限チェック
        if payload.user_id != ADMIN_USER_ID and supabase:
            JST = timezone(timedelta(hours=9), 'JST')
            now = datetime.now(JST)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

            count_res = supabase.table("chat_history") \
                .select("id", count="exact") \
                .eq("user_id", payload.user_id) \
                .gte("created_at", today_start) \
                .execute()
            
            if count_res.count >= 50:
                return {
                    "user_message": payload.message,
                    "ai_response": "🤖 **コーチからのお知らせ：**\n\n本日の無料枠（50回）を使い切りました！また明日お話ししましょう！"
                }

        # 2. 🧠 会話履歴（記憶）の取得（直近5往復分）
        gemini_history = []
        if supabase:
            try:
                hist_res = supabase.table("chat_history") \
                    .select("user_message", "ai_response") \
                    .eq("user_id", payload.user_id) \
                    .order("created_at", desc=False) \
                    .limit(5).execute()
                
                for row in hist_res.data:
                    gemini_history.append({"role": "user", "parts": [str(row["user_message"])]})
                    gemini_history.append({"role": "model", "parts": [str(row["ai_response"])]})
            except Exception as e:
                print(f"✖ History Fetch Error: {e}")

        # 3. 🎭 プロンプトとモデルの準備
        # 🌟 mode を渡して、専用の指示書を取得します
        instruction = get_coach_instruction(payload.level, payload.mode)
        dynamic_model = genai.GenerativeModel(
            model_name=MODEL_NAME, 
            system_instruction=instruction
        )

        # 4. 💬 記憶を持たせたチャットセッションの開始
        chat_session = dynamic_model.start_chat(history=gemini_history)
        response = chat_session.send_message(payload.message)
        ai_text = response.text
        
        # 5. 💾 会話履歴をSupabaseに保存
        if supabase:
            try:
                data ={
                    "user_id": payload.user_id, 
                    "user_message": payload.message,
                    "ai_response": ai_text
                }
                supabase.table("chat_history").insert(data).execute()
            except Exception as e:
                print(f"✖ Database Save Error: {e}")

        return {
            "user_message": payload.message,
            "ai_response": ai_text
        }

    except Exception as e:
        print(f"✖ Chat Error Traceback:\n{traceback.format_exc()}")
        # エラーメッセージを分かりやすく整形
        err_msg = str(e)
        if "429" in err_msg:
            err_msg = "Google APIの回数制限です。少し待ってから再送してください。"
        elif "404" in err_msg:
            err_msg = f"モデル '{MODEL_NAME}' が見つかりません。config.pyを確認してください。"
            
        raise HTTPException(status_code=500, detail=err_msg)

@app.get("/history/{user_id}") 
async def get_history(user_id: str):
    if not supabase: return []
    try:
        response = supabase.table("chat_history").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}