from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

# 修正1: クラウドでもエラーにならないインポート方法
try:
    from db import get_supabase_client
except ImportError:
    from app.db import get_supabase_client

# .env読み込み (ローカル用)
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

# 1. Supabaseクライアントを取得
supabase = get_supabase_client()

# 修正2: クラウドでの設定名(GOOGLE_API_KEY)にも対応させる
API_KEY = os.environ.get("GOOGLE_API_KEY")
model = None

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        
        # 修正3: エラーの元凶「2.5」を、実在する「1.5-flash」に変更！
        MODEL_NAME = 'gemini-2.5-flash'
        
        instruction = """
        あなたは非常に優秀な第二言語習得論の第一人者の日本人向け英会話コーチです。以下のルールを厳守してください：
        １．返答はまず英語で行い、その後に日本語の翻訳をつけてください。
        ２．ユーザーの英語の文法ミスやもっと自然な言い回しがある場合は、返信の最後に[Coach's Advice]というコーナーを作って優しく解説してください。
        ３．ユーザーの英語レベルが初級だと想定し、難しすぎる単語や複雑な構文は避けてください。
        ４．常に励ましの言葉をかけ、ユーザーが英語を話すのが楽しくなるようにしてください。
        """
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=instruction
        )
        print(f"✅ Gemini ({MODEL_NAME}) initialized")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
else:
    print("⚠️ Warning: API KEY not found")

# チャットのデータ形式
class ChatRequest(BaseModel):
    message: str

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
    if not model:
        raise HTTPException(status_code=500, detail="Gemini API is not configured")

    try:
        # AIに聞く
        response = model.generate_content(request.message)
        ai_text = response.text
        
        # 会話履歴をSupabaseに保存
        if supabase:
            try:
                data ={
                    "user_message": request.message,
                    "ai_response": ai_text
                }
                supabase.table("chat_history").insert(data).execute()
                print("✅ saved to Supabase")
            except Exception as db_err:
                print(f"✖ Database Save Error: {db_err}")

        return {
            "user_message": request.message,
            "ai_response": ai_text
        }
    except Exception as e:
        print(f"✖ Chat Error: {e}")
        # クラウドで原因が特定できるように、エラー詳細を返す
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")
        
    try:
        response = supabase.table("chat_history").select("*").order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"✖ Fetch History Error {e}")
        return {"error": str(e)}