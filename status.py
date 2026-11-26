#!/usr/bin/env python3
"""Yahoo!路線情報から対象路線の運行状況を取って status.json に書く。"""
import html, json, re, urllib.request
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
LINES = [
    ("4", "西武池袋線・秩父線", "西武池袋線"),
    ("4", "東武東上線", "東武東上線"),
    ("4", "山手線", "JR山手線"),
    ("4", "埼京川越線[羽沢横浜国大～川越]", "JR埼京線"),
    ("4", "湘南新宿ライン", "JR湘南新宿ライン"),
    ("4", "中央線(快速)[東京～高尾]", "JR中央線快速"),
    ("4", "中央本線[高尾～大月]", "JR中央本線 高尾〜大月"),
    ("5", "中央本線[大月～塩尻]", "JR中央本線 大月〜塩尻"),
]


def area(n):
    req = urllib.request.Request(f"https://transit.yahoo.co.jp/diainfo/area/{n}", headers={"User-Agent": "Mozilla/5.0"})
    s = urllib.request.urlopen(req, timeout=20).read().decode("utf-8")
    rows = {}
    for href, name, status, detail in re.findall(
            r'<tr><td><a href="(/diainfo/[^"]+)">([^<]+)</a></td><td>(?:<[^>]+>)*([^<]+)(?:<[^>]+>)*</td><td>([^<]*)</td></tr>', s):
        rows[html.unescape(name)] = (status.strip(), html.unescape(detail.strip()), "https://transit.yahoo.co.jp" + href)
    return rows


pages = {n: area(n) for n in {a for a, _, _ in LINES}}
out = []
for a, key, label in LINES:
    status, detail, url = pages[a].get(key, ("取得できず", "", "https://transit.yahoo.co.jp/diainfo/area/" + a))
    out.append({"name": label, "status": status, "detail": detail, "url": url})

with open("status.json", "w", encoding="utf-8") as f:
    json.dump({"updated": datetime.now(JST).isoformat(timespec="minutes"), "lines": out}, f, ensure_ascii=False, indent=1)
