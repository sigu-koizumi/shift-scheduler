# Python 3.11 をベースにする
FROM python:3.11-slim

# 画面出力のバッファリングを無効化（ログがすぐ出るようにする）
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリを作成
WORKDIR /code

# 必要なライブラリをインストール
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# プロジェクトのコードをコピー
COPY . /code/