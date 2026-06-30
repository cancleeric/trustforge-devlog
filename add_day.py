#!/usr/bin/env python3
"""加一篇每日開發記錄。

用法:
  python3 add_day.py --date 2026-07-01 --title "Day 2 — XXX" \
      --summary "一句話摘要" --body body.html
  # body.html 為該日內文(HTML 片段,放在 <article> 內;用 <h3>/<ul>/<pre><code> 等)

會:① 產生 days/<date>.html(套版型)② 把該日 prepend 進 entries.json(首頁自動列出)。
重複日期會覆蓋當日頁並更新索引。
"""
import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
PAGE = """<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — TrustForge 開發記錄</title>
<link rel="stylesheet" href="../style.css">
</head><body><div class="wrap">
<a class="back" href="../index.html">← 回開發記錄首頁</a>
<article>
<h2>{title}</h2>
<p class="sub">{date}</p>
{body}
</article>
<footer>TrustForge by HurricaneSoft（颶風軟體）· {date}</footer>
</div></body></html>
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--title", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--body", required=True, help="HTML 片段檔路徑")
    a = p.parse_args()

    body = pathlib.Path(a.body).read_text(encoding="utf-8")
    (ROOT / "days").mkdir(exist_ok=True)
    (ROOT / "days" / f"{a.date}.html").write_text(
        PAGE.format(title=a.title, date=a.date, body=body), encoding="utf-8")

    ej = ROOT / "entries.json"
    entries = json.loads(ej.read_text(encoding="utf-8")) if ej.exists() else []
    entries = [e for e in entries if e["date"] != a.date]  # 去重同日
    entries.insert(0, {"date": a.date, "title": a.title,
                       "file": f"{a.date}.html", "summary": a.summary})
    entries.sort(key=lambda e: e["date"], reverse=True)
    ej.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已加入 {a.date}：days/{a.date}.html + entries.json（共 {len(entries)} 篇）")


if __name__ == "__main__":
    main()
