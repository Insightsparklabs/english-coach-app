import streamlit as st

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
            <p style="color: #6B7280; font-size: 1.1rem;">1年でCEFER C1を目指す、あなた専用の伴走者</p>
        </div>
    """, unsafe_allow_html=True)
    