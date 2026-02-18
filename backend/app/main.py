from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
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
        # model = genai.GenerativeModel('gemini-2.5-flash')
        MODEL_NAME='gemini-2.5-flash'
        instruction = """
        あなたは非常に優秀な　第二言語習得論の第一人者の日本人向け英会話コーチです。以下のルールを厳守してください：
        １．　返答はまず英語で行い、その後に日本語の翻訳をつけてください。
        ２．　ユーザーの英語の文法みすやもっと自然な言い回しがある場合は、返信の最後に[Coach's Advice]というコーナーを作って優しく解説してください。
        ３．　ユーザーの英語レベルが初級だと想定し、難しすぎる単語や複雑な構文は避けてください。
        ４．　常に励ましの言葉をかけ、ユーザーが英語を話すのが楽しくなるようにしてください。

        """
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=instruction # ここで役割をあたえています。
        )
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
        ai_text = response.text
        # 将来的にここで「会話履歴をSupabaseに保存」するコードを追加できます
        if supabase:
            try:
                data ={
                    "user_message": request.message,
                    "ai_response": ai_text
                }
                # SQLで作成した[chat_histor]という名前に合わせます。
                supabase.table("chat_history").insert(data).execute()
                print("✅ saved to Supabase")
            except Exception as db_err:
                # DB保存でエラーが出ても、AIの返答は止めたくないのでPrintのみ
                print(f"✖ Database Save Error: {db_err}")

        return {
            "user_message": request.message,
            "ai_response": response.text
        }
    except Exception as e:
        print(f"✖ Chat Error: {e}")
        return {"error": str(e)}
    

# 既存の@app.post("/chat")の下あたりに追加
@app.get("/history")
async def get_history():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configued")
        
    try:
        # chat_historyテーブルから、作成日時(created_at)の古い順に全件取得
        response = supabase.table("chat_history").select("*").order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"✖ Fetch History Error {e}")
        return{"error": str(e)}
        
        