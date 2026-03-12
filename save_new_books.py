# https://developers.google.com/workspace/sheets/api/quickstart/python?hl=ja
# python3 -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

# サービスアカウントを作成
#    「APIとサービス」→「認証情報」
#    「認証情報を作成」→ サービスアカウント
#    名前を入力（例：amazon-sheets-bot）
#    ロールは空でOK（後からでも可）
#    作成

# JSONキーを作る（重要）
#    作成したサービスアカウントをクリック
#    「キー」タブ
#    「鍵を追加」→「新しい鍵を作成」
#    JSONを選択
#    ダウンロード

# 共有
#    JSON内の "client_email" を確認
#    スプレッドシートを開く
#    右上の「共有」ボタンをクリック
#    その "client_email" を追加

import sys
import datetime
import sqlite3
import datetime

# 新刊情報を取得する
from scrape_new_books import scrape_new_comp_books

# 今日の日付
today = datetime.date.today()
today_str = today.isoformat()


def sqlite_insert(conn, books):
    c = conn.cursor()

    c.execute("""
CREATE TABLE IF NOT EXISTS books (
    asin TEXT PRIMARY KEY,
    title TEXT,
    author TEXT,
    date TEXT,
    image TEXT
)
""")

    new_entries = []
    for book in books:
        # 発売日	書名	著者	ASIN	IMAGE
        new_entries.append((
            book["asin"],
            book["title"],
            book["author"],
            book["date"],
            book["image"]
        ))

    # INSERT OR IGNORE で重複は無視
    c.executemany("""
    INSERT OR IGNORE INTO books (asin, title, author, date, image)
    VALUES (?, ?, ?, ?, ?)
    """, new_entries)


if __name__ == "__main__":
    with sqlite3.connect("data/amazon.db") as conn:
        c = conn.cursor()
        print("処理を実行します")
        # 新刊情報を取得
        for books in scrape_new_comp_books():
            # SQLiteに新刊情報を保存する。
            sqlite_insert(conn, books)
