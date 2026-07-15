#!/usr/bin/env python3
"""加一篇每日開發記錄。

用法:
  python3 add_day.py --date 2026-07-16 --title "Day 17 — XXX" \
      --summary "一句話摘要" --body body.html \
      --category "Hermes" --tags "hermes,ui"

  # body.html 為該日內文(HTML 片段,放在 <article> 內;用 <h3>/<ul>/<pre><code> 等)

會:① 產生 days/<date>.html(套版型,含分類/標籤)② 把該日 prepend 進 entries.json
(首頁自動列出)③ 重算 meta(total/last_date/generated)。重複日期會覆蓋當日頁並更新索引。

資料層 entries.json 為結構化「資料庫」:
  { "meta": {...}, "entries": [ {id,day,date,title,summary,category,tags,file}, ... ] }
`day` 由 date 相對首日自動推算(同日的多篇共享同一 day),故 Day 編號永遠等於日曆天數,
不會再被「同一天多篇」灌水。可用 build_db.py 從 SQLite 重建此檔。
"""
import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
FIRST_DATE = "2026-06-30"  # Day 1

PAGE = """<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — TrustForge 開發記錄</title>
<link rel="stylesheet" href="../style.css">
</head><body><div class="wrap">
<a class="back" href="../index.html">← 回開發記錄首頁</a>
<article>
<h2>{title}</h2>
<p class="sub">{date}</p>
{meta}
{body}
</article>
<footer>TrustForge by HurricaneSoft（颶風軟體）· {date}</footer>
</div></body></html>
"""


def day_of(date_str):
    from datetime import date
    a = date.fromisoformat(FIRST_DATE)
    b = date.fromisoformat(date_str[:10])
    return (b - a).days + 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD（同日多篇可加後綴如 2026-07-11b）")
    p.add_argument("--title", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--body", required=True, help="HTML 片段檔路徑")
    p.add_argument("--category", default="未分類")
    p.add_argument("--tags", default="", help="逗號分隔,如 hermes,ui")
    a = p.parse_args()

    calendar_date = a.date[:10]
    day = day_of(calendar_date)
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    meta_line = (f'<p class="sub" style="margin-top:-.6rem">分類：{a.category}'
                 + (f' ｜ 標籤：' + ' '.join(f'#{t}' for t in tags) if tags else '')
                 + '</p>') if a.category != "未分類" or tags else ''

    body = pathlib.Path(a.body).read_text(encoding="utf-8")
    (ROOT / "days").mkdir(exist_ok=True)
    (ROOT / "days" / f"{a.date}.html").write_text(
        PAGE.format(title=a.title, date=a.date, meta=meta_line, body=body), encoding="utf-8")

    ej = ROOT / "entries.json"
    data = json.loads(ej.read_text(encoding="utf-8")) if ej.exists() else {"meta": {}, "entries": []}
    entries = data.get("entries", [])
    entries = [e for e in entries if e.get("date") != a.date and e.get("id") != a.date]
    entries.insert(0, {
        "id": a.date, "day": day, "date": calendar_date, "title": a.title,
        "summary": a.summary, "category": a.category, "tags": tags, "file": f"{a.date}.html",
    })
    entries.sort(key=lambda e: e["date"], reverse=True)

    data["entries"] = entries
    meta = data.setdefault("meta", {})
    meta["total"] = len(entries)
    meta["last_date"] = entries[0]["date"] if entries else calendar_date
    meta["generated"] = __import__("datetime").date.today().isoformat()
    data["meta"] = meta

    ej.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已加入 {a.date}（Day {day}）：days/{a.date}.html + entries.json（共 {len(entries)} 篇）")


if __name__ == "__main__":
    main()
