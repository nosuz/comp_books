#!/usr/bin/env python3

from pathlib import Path
import argparse
import time
import re
from bs4 import BeautifulSoup
import requests

BOOKS_URL = "https://www.amazon.co.jp/s?i=stripbooks&rh=n%3A466298%2Cp_n_publication_date%3A2285919051&s=date-asc-rank&dc&qid=1771997277&rnid=82836051&ref=sr_st_date-asc-rank&ds=v1%3ABCx%2FYdfUfZira6wYEePCPFeQKnWpeDaRQ13IzFF3Geg"
MAGAZINES_URL = "https://www.amazon.co.jp/s?i=stripbooks&rh=n%3A46423011%2Cp_n_publication_date%3A2285539051&s=date-asc-rank&dc&qid=1773742766&rnid=82836051&ref=sr_st_date-asc-rank&ds=v1%3AVDRvoy00oEuRfLqBEHXj%2Byulxt2QJn%2Fy0Bp%2B2PJBrgc"

HTML_FILE_BASE_BOOKS = "html/books"
HTML_FILE_BASE_MAGAZINES = "html/magazines"


def zero_pad_slash_date(old_date: str) -> str:
    parts = old_date.split("/")
    if len(parts) != 3:
        raise ValueError(f"日付形式が不正です: {old_date}")
    year, month, day = parts
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def find_date_text_books(item):
    """
    本ページ用:
    YYYY/MM/DD の表示から取得
    """
    date_span = item.find(
        "span", class_="a-size-base a-color-secondary a-text-normal")
    if not date_span:
        return None

    text = date_span.get_text(strip=True)
    if not re.match(r"\d{4}/\d{1,2}/\d{1,2}$", text):
        return None

    return zero_pad_slash_date(text)


def extract_author_from_date_span(date_span):
    """
    元コードに近い形で、日付spanより前のテキストを著者として拾う
    """
    if not date_span:
        return ""

    inner_row = date_span.find_parent("div", class_="a-row")
    if not inner_row:
        return ""

    author_parts = []
    for elem in inner_row.contents:
        if elem == date_span:
            break
        if hasattr(elem, "get_text"):
            text = elem.get_text(strip=True)
            if text and text != "|" and text != "":
                author_parts.append(text)

    return " ".join(author_parts).strip()


def parse_items(html, page_num, target):
    books = []

    html_file_base = (
        HTML_FILE_BASE_BOOKS if target == "books" else HTML_FILE_BASE_MAGAZINES
    )
    file_path = Path(f"{html_file_base}_{page_num}.html")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTMLを保存: {file_path}")

    soup = BeautifulSoup(html, "html.parser")

    # data-asin がある listitem に限定
    list_items = soup.select('div[role="listitem"][data-asin]')

    if not list_items:
        print("商品が見つかりません")
        return [], None

    for item in list_items:
        data_asin = (item.get("data-asin") or "").strip()
        if not data_asin:
            continue

        title_tag = item.select_one("h2")
        title_text = title_tag.get_text(strip=True) if title_tag else ""

        img_tag = item.select_one("img.s-image")
        img_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

        h2_tag = item.find(
            "h2", class_="a-size-medium a-spacing-none a-color-base a-text-normal"
        )
        aria_label = h2_tag.get("aria-label") if h2_tag else ""
        label_text = str(aria_label)

        type_div = item.find(
            "div", class_="a-row a-spacing-mini a-size-base a-color-base"
        )
        type_text = type_div.get_text(strip=True) if type_div else None

        if re.match(r"スポンサー広告", label_text):
            print(f"SKIP(広告): {title_text}")
            continue

        if target == "books" and type_text and re.match(r"Kindle版|ペーパーバック", type_text):
            print(f"SKIP(Kindle or ペーパー): {title_text}")
            continue

        date_text = find_date_text_books(item)
        date_span = item.find(
            "span", class_="a-size-base a-color-secondary a-text-normal"
        )
        author_text = extract_author_from_date_span(date_span)

        if not date_text:
            print(f"SKIP(日付なし): {title_text}")
            continue

        print(f"Get: {title_text}")

        record = {
            "date": date_text,
            "title": title_text,
            "author": author_text,
            "asin": data_asin,
            "image": img_url,
        }

        books.append(record)

    next_link = soup.select_one("a.s-pagination-next")
    next_url = None
    if next_link and "href" in next_link.attrs:
        next_url = next_link["href"]
        if not next_url.startswith("http"):
            next_url = "https://www.amazon.co.jp" + next_url

    return books, next_url


def requests_scrape(url, target):
    page_num = 1
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja-JP,ja;q=0.9",
    }

    while True:
        print(f"GET: {url}")
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            print(f"HTTP Error: {response.status_code}")
            break

        html = response.text
        books, next_url = parse_items(html, page_num, target)
        yield books

        if not next_url:
            print("最終ページ到達")
            break

        url = next_url
        page_num += 1
        time.sleep(5)


def scrape_new_books(url):
    for books in requests_scrape(url, target="books"):
        yield books


def scrape_new_magazines(url):
    for books in requests_scrape(url, target="magazines"):
        yield books


def scrape_new_comp_books():
    return scrape_new_books(BOOKS_URL)


def scrape_new_comp_magazines():
    return scrape_new_magazines(MAGAZINES_URL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        choices=["books", "magazines"],
        default="books",
        help="取得対象を指定: books or magazines",
    )
    args = parser.parse_args()

    if args.target == "books":
        for books in scrape_new_comp_books():
            print(books)
    else:
        for books in scrape_new_comp_magazines():
            print(books)


if __name__ == "__main__":
    main()
