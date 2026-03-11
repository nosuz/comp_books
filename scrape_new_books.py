# pip install selenium webdriver-manager

from pathlib import Path
import time
import re
import logging
from bs4 import BeautifulSoup
import requests

URL = "https://www.amazon.co.jp/s?i=stripbooks&rh=n%3A466298%2Cp_n_publication_date%3A2285919051&s=date-asc-rank&dc&qid=1771997277&rnid=82836051&ref=sr_st_date-asc-rank&ds=v1%3ABCx%2FYdfUfZira6wYEePCPFeQKnWpeDaRQ13IzFF3Geg"
html_file_base = "html_page"


def zero_pad_date(old_date: str) -> str:
    parts = old_date.split("/")
    if len(parts) != 3:
        raise ValueError(f"日付形式が不正です: {old_date}")
    year, month, day = parts
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

# --------------------------
# HTMLパースを共通化
# --------------------------


def parse_books(html, page_num):
    books = []
    # HTML保存
    file_path = Path(f"{html_file_base}{page_num}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTMLを保存: {file_path}")

    soup = BeautifulSoup(html, "html.parser")
    list_items = soup.select('div[role="listitem"]')

    if not list_items:
        print("商品が見つかりません")
        return [], None

    for item in list_items:
        data_asin = item.get("data-asin")
        date_span = item.find(
            "span", class_="a-size-base a-color-secondary a-text-normal")
        type_div = item.find(
            "div", class_="a-row a-spacing-mini a-size-base a-color-base")
        h2_tag = item.find(
            "h2", class_="a-size-medium a-spacing-none a-color-base a-text-normal")
        title = item.select_one("h2")
        img_tag = item.select_one("img.s-image")

        if not date_span:
            continue

        try:
            date_text = zero_pad_date(date_span.get_text(strip=True))
        except:
            continue

        type_text = type_div.get_text(strip=True) if type_div else None
        aria_label = h2_tag.get("aria-label") if h2_tag else None

        # 著者抽出
        inner_row = date_span.find_parent("div", class_="a-row")
        author_parts = []
        for elem in inner_row.contents:
            if elem == date_span:
                break
            if hasattr(elem, "get_text"):
                text = elem.get_text(strip=True)
                if text and text != "|" and text != "":
                    author_parts.append(text)
        author_text = " ".join(author_parts).strip()

        title_text = title.get_text(strip=True) if title else ""
        label_text = str(aria_label)
        img_url = img_tag["src"] if img_tag else ""

        if re.match("スポンサー広告", label_text):
            logging.info(f"SKIP(広告): {title_text}")
        elif type_text and re.match("Kindle版|ペーパーバック", type_text):
            logging.info(f"SKIP(Kindle or ペーパー): {title_text}")
        else:
            logging.info(f"Get: {title_text}")
            books.append({
                "date": date_text,
                "title": title_text,
                "author": author_text,
                "asin": data_asin,
                "image": img_url
            })

    # 次ページURL
    next_link = soup.select_one("a.s-pagination-next")
    next_url = None
    if next_link and "href" in next_link.attrs:
        next_url = next_link["href"]
        if not next_url.startswith("http"):
            next_url = "https://www.amazon.co.jp" + next_url

    return books, next_url

# --------------------------
# requests版
# --------------------------


def requests_scrape_new_books(url):
    page_num = 1
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja-JP,ja;q=0.9"
    }

    while True:
        print(f"GET: {url}")
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            logging.error(f"HTTP Error: {response.status_code}")
            break

        html = response.text
        books, next_url = parse_books(html, page_num)
        yield books

        if not next_url:
            print("最終ページ到達")
            break

        url = next_url
        page_num += 1
        time.sleep(5)

# --------------------------
# 共通呼び出し
# --------------------------


def scrape_new_books(url):
    for books in requests_scrape_new_books(url):
        yield books


def scrape_new_comp_books():
    return scrape_new_books(URL)


if __name__ == "__main__":
    # for books in scrape_new_books(URL, browser="requests"):
    for books in scrape_new_books(URL):
        print(books)
