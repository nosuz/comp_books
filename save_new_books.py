# https://developers.google.com/workspace/sheets/api/quickstart/python?hl=ja
# python3 -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

#サービスアカウントを作成
#    「APIとサービス」→「認証情報」
#    「認証情報を作成」→ サービスアカウント
#    名前を入力（例：amazon-sheets-bot）
#    ロールは空でOK（後からでも可）
#    作成

#JSONキーを作る（重要）
#    作成したサービスアカウントをクリック
#    「キー」タブ
#    「鍵を追加」→「新しい鍵を作成」
#    JSONを選択
#    ダウンロード

#共有
#    JSON内の "client_email" を確認
#    スプレッドシートを開く
#    右上の「共有」ボタンをクリック
#    その "client_email" を追加

import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import sqlite3
import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
# 新刊情報を取得する
from scrape_new_books import scrape_new_comp_books


# これ以降の未捕捉例外も app.log に記録される
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# Sheets読み取り用スコープ
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# サービスアカウントJSONを指定
SERVICE_ACCOUNT_FILE = r"E:\client_secret_AmazonNewBooks.json"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

# 追加したいスプレッドシートIDとシート名
SPREADSHEET_ID = "1ZKPK4KtCSWoRJ8UDZXyyemV7-rwdkCGUC2Rnrfblcjo"
RANGE_NAME = "シート1"  # シート名だけでOK

# Sheets APIサービスを作成
service = build("sheets", "v4", credentials=credentials)

# 今日の日付
today = datetime.date.today()
today_str = today.isoformat()

# root ロガーを取得
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# ローテートハンドラ作成
handler = RotatingFileHandler(
    "save_new_books.log",
    maxBytes=1*1024*1024,
    backupCount=3,
    encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)

# root ロガーに追加
root_logger.addHandler(handler)


def google_sheet_append(books):
    # 追加するデータ（リストの中にリストで1行分）
    # new_row = [
    #     ["タイトル", "著者", "出版日", "価格", "URL"]
    # ]

    new_row = []
    for book in books:
        date_obj = datetime.datetime.strptime(book["date"], "%Y-%m-%d").date()

        # 今日出版の本のみを抽出する。
        if date_obj == today:
            # 発売日	書名	著者	ASIN	IMAGE
            new_row.append([
                book["date"],
                book["title"],
                book["author"],
                book["asin"],
                "https://www.amazon.co.jp/dp/" + book["asin"],
                book["image"]
            ])

    # append リクエスト
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="RAW",      # ユーザー入力のまま反映
        insertDataOption="INSERT_ROWS",  # 新しい行を追加
        body={"values": new_row}
    ).execute()

    logging.info(f"{result.get('updates').get('updatedRows')} 行を追加しました。")

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

def log_uncaught_exceptions(exctype, value, tb):
    import traceback
    logging.critical("未捕捉例外", exc_info=(exctype, value, tb))

if __name__ == "__main__":
    sys.excepthook = log_uncaught_exceptions


    with sqlite3.connect("amazon.db") as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS run_log(date TEXT PRIMARY KEY)")


        # 今日の記録があるかチェック
        c.execute("SELECT 1 FROM run_log WHERE date=?", (today_str,))
        if c.fetchone():
            logging.error("今日の処理はすでに実行済みです")
        else:
            logging.info("処理を実行します")
            # 新刊情報を取得
            for books in scrape_new_comp_books():
                # 今日の新刊情報をGoogle Sheetに保存する。
                google_sheet_append(books)
                # SQLiteに新刊情報を保存する。
                sqlite_insert(conn, books)

            c.execute("INSERT INTO run_log(date) VALUES(?)", (today_str,))
