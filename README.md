# TrustForge 開發記錄（GitHub Pages）

TrustForge（加密市場分析 AI Agent · HOYA BIT 黑客松）的**每日開發記錄**靜態站。
原始碼為私有 repo（`cancleeric/trustforge`);本站僅公開記錄開發歷程,且力求**詳細到可照做重現**。

## 線上
GitHub Pages: https://cancleeric.github.io/trustforge-devlog/

## 資料庫支援（架構）
GitHub Pages 只能託管靜態檔,瀏覽器無法直接查伺服器資料庫。因此採「**資料庫為來源真相 + 靜態站為預渲染視圖**」：

```
SQLite  devlog.db  (來源真相: id/day/date/title/summary/category/tags/file)
   │  python3 build_db.py build
   ▼
entries.json  (客戶端「資料庫」:首頁 JS 直接查詢/篩選/搜尋)
   │
   ▼
index.html  (靜態渲染:統計/搜尋/分類與標籤篩選/時間軸)
```

- `entries.json` 是結構化資料集:`{ meta:{version,total,categories,…}, entries:[{id,day,date,title,summary,category,tags,file}] }`。
- 想接**真正動態查詢**時,把 `build` 步驟換成後端(Cloudflare Workers / TrustForge 自家 API)即時查 SQLite 回傳 JSON 即可,前端不用改。

## 結構
```
index.html        首頁(JS 讀 entries.json:統計/搜尋/分類+標籤篩選/時間軸)
entries.json      每日索引(結構化資料集,可由 DB 生成)
devlog.db         SQLite 來源真相(可選;build_db.py 管理)
days/<date>.html  每日一頁
style.css         共用樣式(暗色 + 響應式)
add_day.py        加一篇每日記錄(自動算 Day 編號 + 分類/標籤)
build_db.py       資料庫層:init / build / add / shell
.nojekyll         停用 Jekyll(直接服務靜態檔)
```

## Day 編號說明
`day` 由日期相對首日(2026-06-30 = Day 1)自動推算,**同日多篇共享同一 day**,
因此 Day 編號永遠等於日曆天數,不會再被「同一天貼多篇」灌水。

## 每天加一頁
### 方式 A — 直接寫索引(最簡)
```bash
python3 add_day.py --date 2026-07-16 --title "Day 17 — XXX" \
    --summary "一句話摘要" --body body.html \
    --category "Hermes" --tags "hermes,ui"
```

### 方式 B — 走資料庫(推薦,具備資料庫來源)
```bash
# 首次:建 devlog.db 並從現有 entries.json 匯入
python3 build_db.py init
# 新增一篇(寫入 DB 並自動重建 entries.json)
python3 build_db.py add --date 2026-07-16 --title "Day 17 — XXX" \
    --summary "..." --category "Hermes" --tags "hermes,ui" --body body.html
# 任何時候都可從 DB 重建(例如直接改 DB 後)
python3 build_db.py build
```

### 發佈
```bash
git add -A && git commit -m "devlog: 2026-07-16" && git push
```
