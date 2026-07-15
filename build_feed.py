#!/usr/bin/env python3
"""由 entries.json 生成 Atom 1.0 feed (feed.xml),供讀者訂閱開發日誌。

GitHub Pages 是靜態託管,無法即時產 feed,故在「寫入 entries.json」後呼叫本腳本預渲染。
也可單獨執行:  python3 build_feed.py

feed 規格: https://validator.w3.org/feed/docs/atom/
"""
import datetime
import json
import pathlib
import xml.sax.saxutils as su

ROOT = pathlib.Path(__file__).resolve().parent
ENTRIES = ROOT / "entries.json"
FEED = ROOT / "feed.xml"
SITE = "https://cancleeric.github.io/trustforge-devlog"
AUTHOR = "HurricaneSoft（颶風軟體）"


def esc(s):
    return su.escape(str(s), {'"': "&quot;"})


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
        out.append("  </entry>")

    out.append("</feed>")
    FEED.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已生成 {FEED}（{len(entries)} 筆）")


if __name__ == "__main__":
    generate()
