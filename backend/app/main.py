from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta


# クラウドでもエラーにならないインポート方法
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

# Supabaseクライアントを取得
supabase = get_supabase_client()




# ==========================================
# チャットのデータ形式
# ==========================================
class ChatRequest(BaseModel):
    message: str
    user_id: str  
    level: str

@app.get("/")
def read_root():
    db_status = "Connected" if supabase else "Disconnected"
    return {
        "status": "ok", 
        "message": "English Coach AI Backend is running",
        "database": db_status
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not gemini_base_model:
        raise HTTPException(status_code=500, detail="Gemini API is not configured")

    try:
        # ==========================================
        # 👑 1日50回制限 ＆ VIPユーザー特別扱いロジック
        # ==========================================
        if request.user_id != ADMIN_USER_ID:
            if supabase:
                try:
                    JST = timezone(timedelta(hours=9), 'JST')
                    now = datetime.now(JST)
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

                    count_res = supabase.table("chat_history") \
                        .select("id", count="exact") \
                        .eq("user_id", request.user_id) \
                        .gte("created_at", today_start) \
                        .execute()
                    
                    daily_count = count_res.count

                    if daily_count >= 50:
                        limit_msg = (
                            "🤖 **コーチからのお知らせ：**\n\n"
                            "本日のアルファ版特別枠（50回）を使い切りました！\n"
                            "ものすごい学習量ですね！無料でここまで使い倒していただき嬉しいです。\n\n"
                            "💡 *本気で学習を加速させたい方へ：*\n"
                            "画面上部の「LIBERTY ENGLISH」の無料カウンセリングで、プロに学習計画を作ってもらうのもおすすめです！続きはまた明日お話ししましょう！"
                        )
                        return {
                            "user_message": request.message,
                            "ai_response": limit_msg
                        }
                except Exception as db_err:
                    print(f"✖ Count Check Error: {db_err}")

        instruction = get_coach_instruction(request.level)
        dynamic_model = genai.GenerativeModel(
            model_name=MODEL_NAME, 
            system_instruction=instruction
        )

        response = dynamic_model.generate_content(request.message)
        ai_text = response.text
        
        # 会話履歴をSupabaseに保存
        if supabase:
            try:
                data ={
                    "user_id": request.user_id, 
                    "user_message": request.message,
                    "ai_response": ai_text
                }
                supabase.table("chat_history").insert(data).execute()
            except Exception as db_err:
                print(f"✖ Database Save Error: {db_err}")

        return {
            "user_message": request.message,
            "ai_response": ai_text
        }
    except Exception as e:
        print(f"✖ Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 履歴取得
# ==========================================
@app.get("/history/{user_id}") 
async def get_history(user_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")
        
    try:
        response = supabase.table("chat_history") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=False) \
            .execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}