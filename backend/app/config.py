import os
import google.generativeai as genai

from dotenv import load_dotenv

load_dotenv

# 環境変数の取得
API_KEY = os.environ.get("GOOGLE_API_KEY")
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID")

# Model Settings
#MODEL_NAME = 'gemini-2.5-flash'
MODEL_NAME = 'gemini-flash-latest'

# Business Rules
DAILY_LIMIT = 50


model = None        

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)

        # APIキーの有効性チェック用
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        print(f"✅ Gemini ({MODEL_NAME}) initialized")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
else:
    print("⚠️ Warning: API KEY not found")

