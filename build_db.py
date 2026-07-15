#!/usr/bin/env python3
"""TrustForge 開發記錄的資料庫層。

GitHub Pages 只能託管靜態檔,無法在瀏覽器直接查詢伺服器資料庫。因此架構為:

    SQLite (來源真相 / source of truth)
            │  build  ← 本腳本
            ▼
    entries.json (客戶端「資料庫」,首頁 JS 直接查詢/篩選/搜尋)
            │
            ▼
    index.html (靜態渲染)

也就是:「資料庫」是開發記錄的真正存放處,靜態站只是它的預渲染視圖。
想接真正的動態查詢時,只要把 build 步驟換成在後端(如 Cloudflare Workers /
信任 Forge 自家 API)即時查 SQLite 並回傳 JSON 即可,前端不用改。

用法:
  python3 build_db.py init    # 建 devlog.db 並從現有 entries.json 匯入(首次)
  python3 build_db.py build   # 由 devlog.db 重建 entries.json
  python3 build_db.py add --date 2026-07-16 --title "Day 17 — X" \
      --summary "..." --category "Hermes" --tags "hermes,ui" --body body.html
  python3 build_db.py shell   # 開 sqlite3 互動(若有 sqlite3 命令)
"""
import argparse
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DB = ROOT / "devlog.db"
ENTRIES = ROOT / "entries.json"
FIRST_DATE = "2026-06-30"
CATEGORIES = ["信任演算法", "誠實性", "產品體驗", "生產穩定", "部署營運", "Hermes", "基礎建設"]


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_schema(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS devlog (
        id        TEXT PRIMARY KEY,   -- 同 entries.json 的 id (日期,可含後綴)
        day       INTEGER,            -- 由 date 相對首日推算
        date      TEXT,               -- 日曆日期 YYYY-MM-DD
        title     TEXT NOT NULL,
        summary   TEXT NOT NULL,
        category  TEXT DEFAULT '未分類',
        tags      TEXT DEFAULT '',    -- 逗號分隔
        file      TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_devlog_date ON devlog(date DESC);
    """)


def day_of(date_str):
    from datetime import date
    return (date.fromisoformat(date_str[:10]) - date.fromisoformat(FIRST_DATE)).days + 1


def init():
    c = conn()
    init_schema(c)
    if ENTRIES.exists():
        data = json.loads(ENTRIES.read_text(encoding="utf-8"))
        rows = data.get("entries", [])
        for e in rows:
            c.execute(
                "INSERT OR REPLACE INTO devlog (id,day,date,title,summary,category,tags,file) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (e["id"], e.get("day", day_of(e["date"])), e["date"], e["title"],
                 e["summary"], e.get("category", "未分類"),
                 ",".join(e.get("tags", [])), e["file"]))
        c.commit()
        print(f"已從 entries.json 匯入 {len(rows)} 篇到 {DB}")
    else:
        print(f"已建立空資料庫 {DB}")


def build():
    c = conn()
    init_schema(c)
    rows = c.execute("SELECT * FROM devlog ORDER BY date DESC").fetchall()
    entries = [dict(r) for r in rows]
    for e in entries:
        e["tags"] = [t for t in (e["tags"] or "").split(",") if t]
    dates = [e["date"] for e in entries]
    meta = {
        "site": "TrustForge 開發記錄",
        "version": "v0.14.15",
        "generated": __import__("datetime").date.today().isoformat(),
        "total": len(entries),
        "first_date": min(dates) if dates else FIRST_DATE,
        "last_date": max(dates) if dates else FIRST_DATE,
        "categories": CATEGORIES,
    }
    ENTRIES.write_text(json.dumps({"meta": meta, "entries": entries},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已由 {DB} 重建 entries.json（{len(entries)} 篇）")
    try:
        import build_feed
        build_feed.generate()
        import build_sitemap
        build_sitemap.generate()
    except Exception as ex:
        print(f"（跳過 feed/sitemap 重建：{ex}）")


def add(args):
    body = pathlib.Path(args.body).read_text(encoding="utf-8") if args.body else ""
    if args.body:
        (ROOT / "days").mkdir(exist_ok=True)
        (ROOT / "days" / f"{args.date}.html").write_text(
            f"<!doctype html><html lang=zh-Hant><head><meta charset=utf-8>"
            f"<link rel=stylesheet href=../style.css></head><body><div class=wrap>"
            f"<a class=back href=../index.html>← 回開發記錄首頁</a><article>"
            f"<h2>{args.title}</h2><p class=sub>{args.date}</p>{body}</article>"
            f"<footer>TrustForge by HurricaneSoft·{args.date}</footer></div></body></html>",
            encoding="utf-8")
    c = conn()
    init_schema(c)
    c.execute(
        "INSERT OR REPLACE INTO devlog (id,day,date,title,summary,category,tags,file) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (args.date, day_of(args.date), args.date[:10], args.title, args.summary,
         args.category, args.tags, f"{args.date}.html"))
    c.commit()
    print(f"已寫入資料庫 {args.date}（Day {day_of(args.date)}）")
    build()


def shell():
    if not DB.exists():
        init()
    if subprocess.run(["which", "sqlite3"], capture_output=True).returncode != 0:
        print("未安裝 sqlite3 命令,可用 python3 -c \"import sqlite3...\" 操作 devlog.db")
        return
    os.execvp("sqlite3", ["sqlite3", str(DB)])


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("build")
    sub.add_parser("shell")
    pa = sub.add_parser("add")
    pa.add_argument("--date", required=True)
    pa.add_argument("--title", required=True)
    pa.add_argument("--summary", required=True)
    pa.add_argument("--body", default="")
    pa.add_argument("--category", default="未分類")
    pa.add_argument("--tags", default="")
    a = p.parse_args()
    if a.cmd == "add":
        add(a)
    else:
        {"init": init, "build": build, "shell": shell}[a.cmd]()


if __name__ == "__main__":
    main()
