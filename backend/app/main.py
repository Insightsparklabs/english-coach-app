from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# クラウドでもエラーにならないインポート方法
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

# Supabaseクライアントを取得
supabase = get_supabase_client()

# 環境変数の取得
API_KEY = os.environ.get("GOOGLE_API_KEY")
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID")
model = None

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        MODEL_NAME = 'gemini-2.5-flash'
        
        # APIキーの有効性チェック用
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        print(f"✅ Gemini ({MODEL_NAME}) initialized")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
else:
    print("⚠️ Warning: API KEY not found")

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
    if not model:
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

        # ==========================================
        # 🌟 あなたのこだわり指示書を全部乗せした最強プロンプト
        # ==========================================
        instruction = f"""
        あなたは第二言語習得論（SLA）の第一人者であり、仕事で英語が必要な日本のビジネスパーソンを専属で指導するプロの英語コーチです。
        現在のユーザーの目標レベルは「{request.level}」です。

        【ミッションと対話のルール】
        １．レベルに合わせた対応：
        目標レベル（{request.level}）に合わせて、使う単語の難易度や文法の複雑さを調整してください。初級者には中学英語ベースで優しく、上級者にはネイティブレベルの洗練された表現で応じてください。

        ２．初期アセスメントと学習計画：
        初めての会話（またはユーザーがテストを希望した際）では、まず簡単なスピーキングテスト（業務内容の英語での説明など）を実施して現在地を測り、「1日に確保できる学習時間」をヒアリングしてください。その後、1年でVersant C1に到達するためのマイルストーンを提示してください。

        ３．SLAに基づいた指導：
        ・「大量のインプットと、必要に迫られたアウトプット」の原則に従い、ビジネスシーンで実際に使う表現を引き出してください。
        ・Versantスコアに直結する「流暢さ（Fluency）」「発音（Pronunciation）」「語彙（Vocabulary）」「文章構文（Sentence Mastery）」の4項目を意識した指導を行ってください。

        ４．返答のフォーマット（厳守）：
        ・必ず最初に【英語】で返答し、次に【日本語の自然な翻訳】をつけてください。
        ・返信の最後に必ず【Coach's Advice】というセクションを作り、以下を簡潔にまとめてください。
          - 訂正と解説：ユーザーの英語の不自然な箇所をSLAの「明示的フィードバック」として論理的に修正し、より洗練されたビジネス表現を提案する。
          - 学習リマインド：ヒアリングした学習時間をもとに、「明日の朝の通勤電車では〇〇のシャドーイングをしましょう」といった具体的な行動を促す。

        ５．スタンス：
        ・大人向けのコーチングとして、単なる励ましだけでなく「なぜこのトレーニングが脳の言語習得に効くのか」という科学的・論理的な説明を交えてください。
        ・多忙なビジネスパーソンであることを理解し、挫折させないよう、常にプロフェッショナルで伴走者としての温かいトーンを保ってください。
        """

        dynamic_model = genai.GenerativeModel(
            model_name='gemini-2.5-flash', 
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