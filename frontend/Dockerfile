FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Streamlit のデフォルトポート8501で起動
# CMD [ "streamlit", "run", "main.py", "--server.address=0.0.0.0" ]

# ==========================================
# 🌟 魔法の書き換え（OGPタグの強制埋め込み）
# ==========================================
# Streamlitの本体(index.html)を探し出し、</head>の直前にSNSシェア用のタグをねじ込みます
RUN SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])") && \
    sed -i 's|</head>|<meta property="og:title" content="g-book AI English Coach" /><meta property="og:description" content="1年でVersant C1を目指す、あなた専用の伴走者" /><meta property="og:image" content="【ここに画像のURLを貼り付けます】" /><meta name="twitter:card" content="summary_large_image" /></head>|g' $SITE_PACKAGES/streamlit/static/index.html

# --- (元からあるCMDコマンド) ---
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]