from flask import Flask, render_template, jsonify, request
import sqlite3
import os
import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


app = Flask(__name__)

OWNER_HOSTS = {
    "my.comp-books.com",
    "my.comp-books.jp",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data/amazon.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_today_from_tz_env() -> datetime.date:
    tz_name = os.environ.get("TZ")
    if tz_name:
        try:
            return datetime.datetime.now(ZoneInfo(tz_name)).date()
        except ZoneInfoNotFoundError:
            pass
    return datetime.date.today()


@app.route("/")
def index():
    today = get_today_from_tz_env()
    today_str = today.isoformat()
    yesterday_str = (today - datetime.timedelta(days=1)).isoformat()

    host = request.headers.get("Host", "")
    is_owner_host = host in OWNER_HOSTS
    amazon_affiliate_tag = os.environ.get("AMAZON_AFFILIATE_TAG", "")

    return render_template(
        "index.html",
        today=today_str,
        yesterday=yesterday_str,
        timezone_name=os.environ.get("TZ", "Asia/Tokyo"),
        is_owner_host=is_owner_host,
        amazon_affiliate_tag=amazon_affiliate_tag,
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
        target_date = get_today_from_tz_env().isoformat()

    direction = request.args.get("direction", "next")  # next=未来、prev=過去
    if direction not in {"next", "prev"}:
        return jsonify({"error": "Invalid direction"}), 400

    conn = get_db()
    cur = conn.cursor()

    # まず「今回返すべき日付」を決める
    # next: 指定日以降で最も近い日付
    # prev: 指定日以前で最も近い日付
    # 指定日そのものに本が無ければ、該当方向で最初に本が存在する日付を返す。
    if direction == "prev":
        cur.execute(
            """
            SELECT date
            FROM books
            WHERE date <= ?
            GROUP BY date
            ORDER BY date DESC
            LIMIT 1
            """,
            (target_date,),
        )
    else:
        cur.execute(
            """
            SELECT date
            FROM books
            WHERE date >= ?
            GROUP BY date
            ORDER BY date ASC
            LIMIT 1
            """,
            (target_date,),
        )

    current_row = cur.fetchone()
    if not current_row:
        conn.close()
        return jsonify(
            {
                "books": [],
                "current_date": target_date,
                "next_date": None,
            }
        )

    current_date = current_row["date"]

    # その日付の本を返す
    cur.execute(
        """
        SELECT title, author, image, date, asin
        FROM books
        WHERE date = ?
        ORDER BY title
        """,
        (current_date,),
    )
    books = [dict(r) for r in cur.fetchall()]

    # 次に読み込むべき日付を返す
    # prev: 今回返した日付より前
    # next: 今回返した日付より後
    if direction == "prev":
        cur.execute(
            """
            SELECT date
            FROM books
            WHERE date < ?
            GROUP BY date
            ORDER BY date DESC
            LIMIT 1
            """,
            (current_date,),
        )
    else:
        cur.execute(
            """
            SELECT date
            FROM books
            WHERE date > ?
            GROUP BY date
            ORDER BY date ASC
            LIMIT 1
            """,
            (current_date,),
        )

    next_row = cur.fetchone()
    next_date = next_row["date"] if next_row else None

    conn.close()

    return jsonify(
        {
            "books": books,
            "current_date": current_date,
            "next_date": next_date,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
