# 1. ベースイメージ: 軽量なPython 3.11 (Slim) を使用
#    Alpineは相性問題が出やすいので、初心者はSlimが正解
FROM python:3.11-slim

# 2.0 作業ディレクトリの設定
WORKDIR /app

# 3. 依存ファイルのコピーとインストール
#    キャッシュを効かせるため、ソースコードより先にコピーする。
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. ソースコードのコピー
COPY . .

# 5. Cloud Run はポート8080をリッスンすることを期待する
#    ローカルでもそれに合わせるのがベストプラクティス。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]