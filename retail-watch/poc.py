"""
1. User inputs
"""

import re
import time

import requests
from bs4 import BeautifulSoup

# ------------------- CONFIGS -------------------
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://shop.danawa.com/virtualestimate/?controller=estimateMain&methods=index&marketPlaceSeq=16",
}

CATEGORY_MAP = {
    "cpu": 873,
    "cool": 887,
    "mb": 875,
    "mem": 874,
    "gpu": 876,
    "ssd": 32617,
    "hdd": 877,
    "case": 879,
    "psu": 880,
}
market_number = 16
search_category = CATEGORY_MAP["cpu"]  # user input 1
search_keyword = "5600"  # user input 2
url = f"https://shop.danawa.com/virtualestimate/?controller=estimateMain&methods=product&marketPlaceSeq={market_number}&categorySeq={search_category}&categoryDepth=2&pseq=2&name={search_keyword}"
CURRENCY = "won"
prod_url_base = f"shop.danawa.com/pc/?controller=estimateDeal&methods=productInformation&marketPlaceSeq={market_number}&productSeq="

r = session.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

# ------------------- LOGIC -------------------
pattern = re.compile(r"^productList_(\d+)$")
rows = soup.find_all("tr", class_=pattern)

# print(soup.prettify()[:2000])

search_results: list[dict[str, str]] = []
for row in rows:
    product_name = "No product name"
    product_price = "-1"
    product_id = None

    # prod id
    cls_list = row.get("class", [])
    for cls in cls_list:
        match = pattern.match(cls)
        if match:
            product_id = match.group(1)
            break

    # prod name
    p_wrapper = row.find("p", class_="subject")
    if p_wrapper:
        a_wrapper = p_wrapper.find("a")
        if a_wrapper:
            product_name = a_wrapper.get_text(strip=True)

    # prod price
    span_wrapper = row.find("span", class_="prod_price")
    if span_wrapper:
        product_price = "".join(span_wrapper.get_text(strip=True).split(","))

    search_results.append(
        {
            "id": product_id,
            "name": product_name,
            "price": product_price,
            "link": f"{prod_url_base}{product_id}",
            "time": time.time(),
        }
    )

# poc only
from pprint import pprint  # noqa

pprint(search_results)
time.sleep(0.5)

# monitor add format
import json  # noqa
from datetime import datetime  # noqa

requests.post(
    "http://localhost:8000/v1/monitor",
    headers={"content-type": "application/json"},
    data=json.dumps(
        {
            "name": "some_item",
            "price": 1.5,
            "link": "yhap",
            "time": datetime.now().isoformat(),
        }
    ),
)
