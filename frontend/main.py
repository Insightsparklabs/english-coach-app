import os
import streamlit as st
import requests

from supabase import create_client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

from ui_components import apply_custom_css, display_fixed_ad, display_main_header

# 🌟 判定テストの回答数を管理する変数を追加
if "assessment_count" not in st.session_state:
    st.session_state.assessment_count = 0

# 判定テストの最大回数を定義
MAX_ASSESSMENT_QUESTIONS = 5



# ==========================================
# 1. 初期設定とUIパーツの定義
# ==========================================
st.set_page_config(page_title="g-book AI English Coach", page_icon="🎓", layout="centered")

# 🌟 ベースのCSSだけをここで適用（広告はまだ呼ばない）
apply_custom_css()

# --- 環境変数の取得 ---
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://backend:8080").rstrip('/')
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8501").rstrip('/')

# ==========================================
# 🌟 特殊な記憶領域の設定
# ==========================================
@st.cache_resource
def get_global_verifier_store():
    return {}

class SecureStorage:
    def __init__(self):
        self.local_store = {} 
        self.global_store = get_global_verifier_store() 

    def get_item(self, key):
        if "code-verifier" in key:
            return self.global_store.get(key)
        return self.local_store.get(key)

    def set_item(self, key, value):
        if "code-verifier" in key:
            self.global_store[key] = value
        else:
            self.local_store[key] = value

    def remove_item(self, key):
        if "code-verifier" in key:
            self.global_store.pop(key, None)
        else:
            self.local_store.pop(key, None)

# --- Supabaseの準備 ---
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        options = ClientOptions(storage=SecureStorage())
        return create_client(SUPABASE_URL, SUPABASE_KEY, options=options)
    return None

supabase = init_supabase()

# --- 状態管理 ---
if "user" not in st.session_state:
    st.session_state.user = None

# ==========================================
# Googleログインのリダイレクトキャッチ
# ==========================================
if "code" in st.query_params:
    try:
        auth_code = st.query_params["code"]
        if supabase:
            response = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        if response:    
            st.session_state.user = response.user
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.warning("ログインセッションの有効期限が切れました。もう一度お試しください")
        st.query_params.clear()

# ==========================================
# 画面A：ログインしていない時
# ==========================================
if st.session_state.user is None:
    # 🌟 タイトルを表示してから、その直下で広告を呼び出す！（元のあなたの正解ルート）
    display_main_header()
    display_fixed_ad()

    tab_login, tab_signup, tab_reset = st.tabs(["🔑 ログイン", "📝 新規登録", "❓ パスワードを忘れた方"])

    with tab_login:
        st.subheader("ログイン")
        if supabase:
            try:
                res = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"redirect_to": FRONTEND_URL} 
                })
                st.link_button("🌐 Googleでログイン", res.url, use_container_width=True)
                st.divider()
                st.caption("またはメールアドレスでログイン")
            except Exception as e:
                st.error("Google連携の準備中...")

        with st.form("login_form"):
            email = st.text_input("メールアドレス")
            password = st.text_input("パスワード", type="password")
            submit = st.form_submit_button("ログイン")
            if submit and supabase:
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = response.user
                    st.success("ログイン成功！")
                    st.rerun()
                except Exception as e:
                    st.error("ログインに失敗しました。IDかパスワードが間違っています。")

    with tab_signup:
        st.subheader("新規アカウント作成")
        with st.form("signup_form"):
            new_email = st.text_input("新しいメールアドレス")
            new_password = st.text_input("パスワード (6文字以上)", type="password")
            signup_submit = st.form_submit_button("登録する")
            if signup_submit and supabase:
                try:
                    response = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    st.success("🎉 登録が完了しました！メールを確認してリンクをクリックしてください。")
                except Exception as e:
                    st.error(f"登録に失敗しました: {e}")

    with tab_reset:
        st.subheader("パスワードの再設定")
        
        reset_email = st.text_input("登録しているメールアドレス", key="reset_email_input")
        if st.button("確認コードをメールに送信"):
            if supabase:
                try:
                    supabase.auth.reset_password_for_email(reset_email)
                    st.success("✉️ 確認コードを送信しました！メールをご確認ください。")
                except Exception as e:
                    st.error(f"送信エラー: {e}")

        st.divider()

        st.markdown("#### 新しいパスワードの設定")
        otp_code = st.text_input("メールに届いた6桁のコード", key="otp_code")
        new_password = st.text_input("新しいパスワード (6文字以上)", type="password", key="new_pw_reset")

        if st.button("パスワードを更新する"):
            if not otp_code or not new_password:
                st.warning("コードと新しいパスワードを入力してください。")
            elif supabase:
                try:
                    supabase.auth.verify_otp({"email": reset_email, "token": otp_code, "type": "recovery"})
                    supabase.auth.update_user({"password": new_password})
                    st.success("✅ パスワードの変更が完了しました！上の「🔑 ログイン」タブから新しいパスワードでログインしてください。")
                except Exception as e:
                    st.error(f"❌ エラー: コードが間違っているか、有効期限切れです ({e})")

# ==========================================
# 画面B：ログインしている時
# ==========================================
else:
    with st.sidebar:
        st.write(f"👤 ログイン中: {st.session_state.user.email}")

        st.divider()
        st.subheader("🎯 目標レベル設定")
        # 🌟 後でプロンプトに使いやすいよう、短い形式も取得できるようにします
        target_level_map = {
            "初級 (A1-A2: 基礎からやり直し)": "A2",
            "中級 (B1-B2: ビジネスで通用するレベル)": "B2",
            "上級 (CEFER C1: プロフェッショナル)": "C1"
        }
        level_display = st.selectbox(
            "目指す英語レベルを選んでください",
            list(target_level_map.keys()),
            index=0 
        )
        target_level = target_level_map[level_display]
        st.divider()

        if st.button("ログアウト"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # 🌟 ヘッダーと広告
    display_main_header()
    display_fixed_ad()

    # --- 履歴の読み込み（初回のみ） ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
        try:
            resp = requests.get(f"{BACKEND_BASE_URL}/history/{st.session_state.user.id}")
            if resp.status_code == 200:
                past_data = resp.json()
                for item in past_data:
                    st.session_state.messages.append({"role": "user", "content": item["user_message"]})
                    st.session_state.messages.append({"role": "assistant", "content": item["ai_response"]})
        except Exception as e:
            st.error(f"履歴の読み込みエラー: {e}")

    # --- 履歴の表示 ---
    if len(st.session_state.messages) > 4:
        with st.expander("📜 過去のコーチング履歴を表示", expanded=False):
            for message in st.session_state.messages[:-4]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        for message in st.session_state.messages[-4:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    else:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # --- モード選択とプログレスバー ---
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = "assessment"

    st.write("---")
    st.caption("👇 コーチに何を相談しますか？")

    row1_col1, row1_col2, row1_col3 = st.columns(3)
    row2_col1, row2_col2 = st.columns(2)

    quick_prompt = None

    with row1_col1:
        if st.button("📏 実力判定テスト", use_container_width=True):
            st.session_state.current_mode = "assessment"
            st.session_state.assessment_count = 0
            quick_prompt = "現在の英語力を測るための簡単なテストを開始してください。"

    with row1_col2:
        if st.button("📈 CEFR C1特訓", use_container_width=True):
            st.session_state.current_mode = "level_up"
            quick_prompt = "CEFR C1レベルを目指す特訓をお願いします。"

    with row1_col3:
        if st.button("✍️ 英語日記サポート", use_container_width=True):
            st.session_state.current_mode = "diary"
            quick_prompt = "英語日記の作成をサポートしてください。"

    with row2_col1:
        if st.button("📅 今日の学習報告", use_container_width=True):
            st.session_state.current_mode = "default"
            quick_prompt = "今日の学習報告をします。"

    with row2_col2:
        if st.button("🔍 英文の添削依頼", use_container_width=True):
            st.session_state.current_mode = "default"
            quick_prompt = "英文を添削してください。"

    # 📊 実力判定時のみプログレスバーを表示
    if st.session_state.current_mode == "assessment":
        progress = min(st.session_state.assessment_count / MAX_ASSESSMENT_QUESTIONS, 1.0)
        st.write(f"📊 **実力判定の進捗: {st.session_state.assessment_count} / {MAX_ASSESSMENT_QUESTIONS}**")
        st.progress(progress)
        if st.session_state.assessment_count >= MAX_ASSESSMENT_QUESTIONS:
            st.info("💡 十分な情報が集まりました。次の送信で判定結果が出ます！")

# ==========================================
    # チャット入力と送信処理
    # ==========================================
    if prompt := (st.chat_input("メッセージを入力...") or quick_prompt):
        
        # 🌟 送信前にカウントアップ（手動入力の時だけ）
        if st.session_state.current_mode == "assessment" and not quick_prompt:
            st.session_state.assessment_count += 1

        # 1. ユーザーのメッセージを画面に追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. 5回目なら判定を促す指示を追加
        final_prompt = prompt
        if st.session_state.current_mode == "assessment" and st.session_state.assessment_count >= MAX_ASSESSMENT_QUESTIONS:
            final_prompt += "\n(This is my final reply. Please provide my CEFR assessment now.)"

        # 3. AIの思考中スピナーを表示
        try:
            with st.spinner("Coach is thinking..."):
                payload = {
                    "message": final_prompt, 
                    "user_id": st.session_state.user.id,
                    "level": target_level,
                    "mode": st.session_state.current_mode # 🌟 モードを送信
                }
                response = requests.post(f"{BACKEND_BASE_URL}/chat", json=payload)
                
                if response.status_code == 200:
                    ai_response = response.json().get("ai_response")
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    st.rerun() # 🌟 ここで画面を更新
                else:
                    st.error("コーチが一時的に席を外しているようです。")
        except Exception as e:
            st.error(f"接続に失敗しました：{e}")