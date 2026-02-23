import os
import streamlit as st
import requests

from supabase import create_client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. 初期設定とUIパーツの定義
# ==========================================
st.set_page_config(page_title="g-book AI English Coach", page_icon="🎓", layout="centered")

def apply_custom_css():
    """不要なヘッダーを隠し、広告用のスタイルを適用する"""
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* 画面上部に固定するコンテナ */
        .fixed-ad-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #001f3f;
            z-index: 99999; /* 念のためZインデックスをさらに強くしました */
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 5px 0;
            border-bottom: 2px solid #c9a063;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.3);
        }
        .pr-label {
            color: #ffffff;
            font-size: 10px;
            opacity: 0.8;
            margin-bottom: 2px;
            letter-spacing: 1px;
        }
        .main .block-container {
            padding-top: 100px !important;
        }
        .fixed-ad-container img {
            max-height: 50px;
            width: auto;
        }
        </style>
    """, unsafe_allow_html=True)

def display_fixed_ad():
    """画面上部に常に表示される広告バナー"""
    st.markdown("""
        <div class="fixed-ad-container">
            <div class="pr-label">【PR】</div>
            <a href="https://px.a8.net/svt/ejp?a8mat=3TLJ5G+1PCPWA+4MWC+601S1" rel="nofollow">
            <img border="0" width="320" height="50" alt="" src="https://www27.a8.net/svt/bgt?aid=231111988103&wid=050&eno=01&mid=s00000021630001008000&mc=1"></a>
            <img border="0" width="1" height="1" src="https://www12.a8.net/0.gif?a8mat=3TLJ5G+1PCPWA+4MWC+601S1" alt="">        
        </div>
    """, unsafe_allow_html=True)

def display_main_header():
    """アプリのメインタイトル"""
    st.markdown("""
        <div style="text-align: center;">
            <h1 style="color: #1E3A8A; margin-bottom: 0;">g-book AI English Coach</h1>
            <p style="color: #6B7280; font-size: 1.1rem;">1年でVersant C1を目指す、あなた専用の伴走者</p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

# 🌟 ベースのCSSだけをここで適用（広告はまだ呼ばない）
apply_custom_css()

# --- 環境変数の取得 ---
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8080").rstrip('/')
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
        target_level = st.selectbox(
            "目指す英語レベルを選んでください",
            [
                "初級 (A1-A2: 基礎からやり直し)", 
                "中級 (B1-B2: ビジネスで通用するレベル)", 
                "上級 (Versant C1: プロフェッショナル)"
            ],
            index=2 
        )
        st.divider()

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

    # 🌟 タイトルを表示してから、その直下で広告を呼び出す！（元のあなたの正解ルート）
    display_main_header()
    display_fixed_ad()

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
                payload = {
                    "message": prompt, 
                    "user_id": user_id,
                    "level": target_level 
                }
                response = requests.post(f"{BACKEND_BASE_URL}/chat", json=payload)
                
                if response.status_code == 200:
                    ai_response = response.json().get("ai_response")
                    with st.chat_message("assistant"):
                        st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    st.error("コーチが席を外しているようです。")
        except Exception as e:
            st.error(f"接続に失敗しました：{e}")