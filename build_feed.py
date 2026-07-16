#!/usr/bin/env python3
"""由 entries.json 生成 Atom 1.0 feed (feed.xml),供讀者訂閱開發日誌。

GitHub Pages 是靜態託管,無法即時產 feed,故在「寫入 entries.json」後呼叫本腳本預渲染。
也可單獨執行:  python3 build_feed.py

feed 規格: https://validator.w3.org/feed/docs/atom/
"""
import datetime
import json
import pathlib
import re
import xml.sax.saxutils as su

ROOT = pathlib.Path(__file__).resolve().parent
ENTRIES = ROOT / "entries.json"
DAYS = ROOT / "days"
FEED = ROOT / "feed.xml"
SITE = "https://cancleeric.github.io/trustforge-devlog"
AUTHOR = "HurricaneSoft（颶風軟體）"


def esc(s):
    return su.escape(str(s), {'"': "&quot;"})


def article_body(file_name):
    """從 days/<file> 抓靜態 <article> 內文，供 feed content 使用（不含 JS 注入的 nav/toc/related）。"""
    p = DAYS / file_name
    if not p.exists():
        return ""
    html = p.read_text(encoding="utf-8")
    m = re.search(r"<article>(.*?)</article>", html, re.S)
    if not m:
        return ""
    body = m.group(1)
    # 去掉文末由 day-common.js 注入的「相關文章」section（靜態不含，但防禦性清理 back/footer）
    body = re.sub(r'<a class="back"[^>]*>.*?</a>', "", body, flags=re.S)
    return body.strip()


def generate():
    data = json.loads(ENTRIES.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    meta = data.get("meta", {})
    latest = entries[0]["date"] if entries else datetime.date.today().isoformat()
    updated = f"{latest}T00:00:00+08:00"

    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<feed xmlns="http://www.w3.org/2005/Atom">',
           f"  <title>TrustForge 開發記錄</title>",
           f"  <id>{esc(SITE + '/')}</id>",
           f"  <updated>{updated}</updated>",
           f"  <author><name>{esc(AUTHOR)}</name></author>",
           f'  <link rel="self" href="{esc(SITE + "/feed.xml")}"/>',
           f'  <link rel="alternate" href="{esc(SITE + "/")}"/>',
           f"  <subtitle>{esc(meta.get('site', 'TrustForge 開發記錄') + ' — 開發歷程公開記錄')}</subtitle>"]

    for e in entries:
        d = e["date"]
        url = f"{SITE}/days/{e['file']}"
        out += [
            "  <entry>",
            f"    <title>{esc(e['title'])}</title>",
            f"    <id>{esc(url)}</id>",
            f'    <link rel="alternate" href="{esc(url)}"/>',
            f"    <updated>{d}T00:00:00+08:00</updated>",
            f"    <published>{d}T00:00:00+08:00</published>",
            f"    <summary>{esc(e['summary'])}</summary>",
        ]
        if e.get("category"):
            out.append(f'    <category term="{esc(e["category"])}"/>')
        body = article_body(e["file"])
        if body:
            out.append(f"    <content type=\"html\"><![CDATA[{body}]]></content>")
        out.append("  </entry>")

    out.append("</feed>")
    FEED.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已生成 {FEED}（{len(entries)} 筆）")


if __name__ == "__main__":
    generate()
