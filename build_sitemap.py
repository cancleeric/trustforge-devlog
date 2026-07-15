#!/usr/bin/env python3
"""由 entries.json 生成 sitemap.xml (SEO 發現用)。

用法:  python3 build_sitemap.py
也會在 add_day.py / build_db.py build 後自動呼叫。
"""
import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
ENTRIES = ROOT / "entries.json"
SITEMAP = ROOT / "sitemap.xml"
SITE = "https://cancleeric.github.io/trustforge-devlog"


def generate():
    data = json.loads(ENTRIES.read_text(encoding="utf-8"))
    urls = [SITE + "/", SITE + "/references.html"]
    for e in data.get("entries", []):
        urls.append(f"{SITE}/days/{e['file']}")
    today = datetime.date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        out += [f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>"]
    out.append("</urlset>")
    SITEMAP.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已生成 {SITEMAP}（{len(urls)} 筆網址）")


if __name__ == "__main__":
    generate()
