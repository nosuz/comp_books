from flask import Flask, render_template, jsonify, request
import sqlite3
import os
import datetime


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data/amazon.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    today = datetime.date.today()
    today_str = today.isoformat()
    yesterday_str = (today - datetime.timedelta(days=1)).isoformat()
    return render_template(
        "index.html",
        today=today_str,
        yesterday=yesterday_str,
    )


@app.route("/api/books")
def api_books():
    target_date = request.args.get("date")
    if target_date:
        try:
            datetime.datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
    else:
        target_date = datetime.date.today().isoformat()

    direction = request.args.get("direction", "next")  # next=未来、prev=過去

    conn = get_db()
    cur = conn.cursor()

    # 1. ターゲット日のデータ取得
    cur.execute(
        """
        SELECT title, author, image, date, asin
        FROM books
        WHERE date = ?
        ORDER BY title
        """,
        (target_date,),
    )
    books = [dict(r) for r in cur.fetchall()]

    # 2. 次に読み込む日付を取得
    if direction == "prev":
        cur.execute(
            """
            SELECT DISTINCT date
            FROM books
            WHERE date < ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (target_date,),
        )
    else:
        cur.execute(
            """
            SELECT DISTINCT date
            FROM books
            WHERE date > ?
            ORDER BY date ASC
            LIMIT 1
            """,
            (target_date,),
        )

    next_row = cur.fetchone()
    next_date = next_row["date"] if next_row else None

    conn.close()

    return jsonify(
        {
            "books": books,
            "current_date": target_date,
            "next_date": next_date,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
