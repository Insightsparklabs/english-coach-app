import os
import streamlit as st
import requests

from supabase import create_client, Client
from dotenv import load_dotenv # 👈 これを追加！

load_dotenv() # 👈 これを追加！

# --- 環境変数の取得 ---
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8080").rstrip('/')
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

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
# 画面A：ログインしていない時（ログイン画面を表示）
# ==========================================
if st.session_state.user is None:
    st.title("English Coach AI 🤖")
    st.subheader("ログインしてください")
    
    with st.form("login_form"):
        email = st.text_input("メールアドレス (ID)")
        password = st.text_input("パスワード", type="password")
        submit = st.form_submit_button("ログイン")
        
        if submit:
            if not supabase:
                st.error("Supabaseの設定がされていません。")
            else:
                try:
                    # Supabaseに「このIDとパスワード合ってる？」と聞く
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = response.user
                    st.success("ログイン成功！")
                    st.rerun() # 画面をリロードしてチャット画面へ切り替え
                except Exception as e:
                    st.error("ログインに失敗しました。IDかパスワードが間違っています。")

# ==========================================
# 画面B：ログインしている時（いつものチャット画面を表示）
# ==========================================
else:
    # ログアウトボタンをサイドバーに設置
    with st.sidebar:
        st.write(f"👤 ログイン中: {st.session_state.user.email}")
        if st.button("ログアウト"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # --- ここから下はいつものチャットコード ---
    st.title("English Coach AI 🤖")
    st.caption("あなたの優しい英会話コーチです。なんでも英語で話しかけてね！")

    
    
    
    
    
    
    
    
    
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        try:
            response = requests.get(f"{BACKEND_BASE_URL}/history")
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
                response = requests.post(f"{BACKEND_BASE_URL}/chat", json={"message": prompt})
                if response.status_code == 200:
                    ai_response = response.json().get("ai_response")
                    with st.chat_message("assistant"):
                        st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    st.error("コーチが席を外しているようです。(Backend Error)")
        except Exception as e:
            st.error(f"接続に失敗しました：{e}")