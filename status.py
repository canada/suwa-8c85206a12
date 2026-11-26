#!/usr/bin/env python3
"""運行情報（Yahoo!路線情報・JR東日本）を取って status.json に書く。"""
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
AZUSA = "https://traininfo.jreast.co.jp/train_info/express.aspx?group=azusa_kaiji_fujiexcursion"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def yahoo_lines():
    pages = {}
    for n in {a for a, _, _ in LINES}:
        rows = {}
        for href, name, status, detail in re.findall(
                r'<tr><td><a href="(/diainfo/[^"]+)">([^<]+)</a></td><td>(.*?)</td><td>(.*?)</td></tr>', get(f"https://transit.yahoo.co.jp/diainfo/area/{n}")):
            rows[html.unescape(name)] = (text(status), text(detail), "https://transit.yahoo.co.jp" + href)
        pages[n] = rows
    out = []
    for a, key, label in LINES:
        status, detail, url = pages[a].get(key, ("取得できず", "", f"https://transit.yahoo.co.jp/diainfo/area/{a}"))
        out.append({"name": label, "status": status, "detail": detail, "url": url})
    return out


def azusa():
    s = get(AZUSA)
    out = []
    for name, status, note in re.findall(r'traininfo-routes__name">([^<]+)</span>.*?traininfo-line-info__status[^>]*>\s*<span>([^<]+)</span>'
                                         r'.*?traininfo-routes__note">(.*?)</div>', s, re.S):
        out.append({"name": "特急" + text(name), "status": text(status), "detail": text(note), "url": AZUSA})
    m = re.search(r"<h2>運休情報</h2>(.*?)</section>", s, re.S)
    note = text(m.group(1)) if m else ""
    return [x for x in out if "あずさ" in x["name"]], note


try:
    prev = json.load(open("status.json", encoding="utf-8"))
except Exception:
    prev = {}
data = {"updated": datetime.now(JST).isoformat(timespec="minutes")}
for key, fn in [("lines", yahoo_lines), ("azusa", azusa)]:
    try:
        data[key] = fn()
    except Exception as e:
        data[key] = None
        data.setdefault("errors", []).append(f"{key}: {e}")
if data["azusa"]:
    data["azusa"], data["azusa_note"] = data["azusa"]
    data["azusa_at"] = data["updated"]
elif prev.get("azusa"):
    # GitHub Actions からは JR東日本が 403 を返すので、N100 で取った前回値を残す
    data["azusa"], data["azusa_note"], data["azusa_at"] = prev["azusa"], prev.get("azusa_note", ""), prev.get("azusa_at", "")

with open("status.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
