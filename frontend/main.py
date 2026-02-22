import os
import streamlit as st
import requests

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# --- 環境変数の取得 ---
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8080").rstrip('/')
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
# 🌟 本番環境とローカル環境を自動で切り替えるためのURL
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8501").rstrip('/')

# --- Supabaseの準備 ---
@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# --- 状態管理（ログインしているかどうか） ---
if "user" not in st.session_state:
    st.session_state.user = None

# ==========================================
# Googleからの帰り道（リダイレクト）をキャッチする
# ==========================================
if "code" in st.query_params:
    try:
        auth_code = st.query_params["code"]
        if supabase:
            response = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
            st.session_state.user = response.user
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Googleログインに失敗しました: {e}")

# ==========================================
# 画面A：ログインしていない時
# ==========================================
if st.session_state.user is None:
    st.title("English Coach AI 🤖")
    
    tab_login, tab_signup, tab_reset = st.tabs(["🔑 ログイン", "📝 新規登録", "❓ パスワードを忘れた方"])

    with tab_login:
        st.subheader("ログイン")
        if supabase:
            try:
                res = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"redirect_to": FRONTEND_URL} # 🌟 変数を使用
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
        st.caption("登録したメールアドレスを入力してください。")
        with st.form("reset_form"):
            reset_email = st.text_input("メールアドレス")
            reset_submit = st.form_submit_button("リセットメールを送信")
            if reset_submit and supabase:
                try:
                    supabase.auth.reset_password_email(
                        reset_email, 
                        options={"redirect_to": FRONTEND_URL} # 🌟 変数を使用
                    )
                    st.success("✉️ パスワード再設定用のメールを送信しました！")
                except Exception as e:
                    st.error(f"メールの送信に失敗しました: {e}")

# ==========================================
# 画面B：ログインしている時
# ==========================================
else:
    with st.sidebar:
        st.write(f"👤 ログイン中: {st.session_state.user.email}")
        if st.button("ログアウト"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

        st.divider()
        st.subheader("⚙️ パスワード変更")
        with st.form("update_password_form"):
            new_pw = st.text_input("新しいパスワードを入力", type="password")
            update_btn = st.form_submit_button("パスワードを更新する")
            if update_btn and supabase:
                try:
                    supabase.auth.update_user({"password": new_pw})
                    st.success("✅ パスワードを更新しました！")
                except Exception as e:
                    st.error(f"更新に失敗しました: {e}")

    # --- チャット画面本体 ---
    st.title("English Coach AI 🤖")
    st.caption("あなたの優しい英会話コーチです。")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        try:
            user_id = st.session_state.user.id
            response = requests.get(f"{BACKEND_BASE_URL}/history/{user_id}")
            if response.status_code == 200:
                past_chats = response.json()
                for chat in past_chats:
                    st.session_state.messages.append({"role": "user", "content": chat["user_message"]} )
                    st.session_state.messages.append({"role": "assistant", "content": chat["ai_response"]})
        except Exception as e:
            st.error(f"履歴の読み込みに失敗しました: {e}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("How are you today?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            with st.spinner("Coach is thinking..."):
                user_id = st.session_state.user.id
                response = requests.post(f"{BACKEND_BASE_URL}/chat", json={"message": prompt, "user_id": user_id})
                if response.status_code == 200:
                    ai_response = response.json().get("ai_response")
                    with st.chat_message("assistant"):
                        st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    st.error("コーチが席を外しているようです。")
        except Exception as e:
            st.error(f"接続に失敗しました：{e}")