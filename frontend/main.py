import streamlit as st
import requests

st.set_page_config(page_title="English Coach AI", page_icon="🤖")
st.title("English Coach AI 🤖")
st.caption("あなたの優しい英会話コーチです。なんでも英語で話しかけてね！")

# バックエンドのURL (Dockerネットワーク内での名前を指定)
BACKEND_URL = "http://backend:8080/chat"

#チャット履歴を保持
if "messages" not in st.session_state:
    st.session_state.messages = []

# 履歴を表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 入力欄
if prompt := st.chat_input("How are you today?"):
    # ユーザーの入力を表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # バックエンドへリクエスト
    try:
        with st.spinner("Coach is thinking..."):
            response = requests.post(BACKEND_URL, json={"message": prompt})
            if response.status_code == 200:
                ai_response = response.json().get("ai_response")
                #AIの返答を表示
                with st.chat_message("assistant"):
                    st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                st.error("コーチが席を外しているようです。(Backend Error)")
    except Exception as e:
        st.error(f"接続に失敗しました：{e}")
        
