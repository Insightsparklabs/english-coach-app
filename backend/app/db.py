import os

from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# .envファイルを読み込む
load_dotenv()

# 環境変数からURLとキーを取得
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

# エラーハンドリング: キーがない場合に警告を出す
if not url or not key:
    print("Warning: Supabase credentials not found in .env file")

# クライアントの作成
# ここでエラーが起きても、main.py でキャッチできるように None にしておく
supabase: Client = None

try:
    if url and key:
        supabase = create_client(url, key)
        print("✅ Supabase client initialized in db.py")
except Exception as e:
    print(f"❌ Failed to initialize Supabase: {e}")

# 外部から呼び出すための関数
def get_supabase_client() -> Client:
    return supabase