#!/usr/bin/env python3

import datetime
import sqlite3
import datetime
import time

# 新刊情報を取得する
from scrape_new_books import scrape_new_comp_books, scrape_new_comp_magazines

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

        time.sleep(5)
        for magazines in scrape_new_comp_magazines():
            # SQLiteに新刊情報を保存する。
            sqlite_insert(conn, magazines)
