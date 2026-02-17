FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Streamlit のデフォルトポート8501で起動
CMD [ "streamlit", "run", "main.py", "--server.address=0.0.0.0" ]