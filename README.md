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

## 功能
- **分頁**：每頁 10 筆 + 頁碼摺疊，扛住 50/100+ 筆不卡。
- **搜尋**：即時過濾標題/摘要/標籤，命中詞 `<mark>` 高亮。
- **篩選**：分類 chips、月份跳轉 chips、標籤雲（按頻率）、點標籤多重疊加。
- **鍵盤快捷**：`/` 聚焦搜尋、`j/k` 上下篇、`Enter` 打開、`Esc` 清除。
- **參考頁** `references.html`：學術論文方法 + 產業大廠真實來源 + 選定技術堆疊。
- **每篇日誌** `day-common.js`：上一篇/下一篇時間軸導覽、文內目錄(TOC)、相關文章(共用標籤)。
- **訂閱** `feed.xml`(Atom) + **SEO** `sitemap.xml` / `robots.txt` / OG meta。

## 結構
```
index.html        首頁(統計/分頁/搜尋/分類+月份+標籤雲篩選)
entries.json      每日索引(結構化資料集,可由 DB 生成)
devlog.db         SQLite 來源真相(可選;build_db.py 管理)
days/<date>.html  每日一頁(自帶 day-common.js 導覽/TOC/相關)
day-common.js     每篇日誌通用行為(客戶端,無後端)
references.html   參考資料:論文 / 大廠來源 / 選定技術堆疊
feed.xml          Atom 訂閱源(build_feed.py 生成)
sitemap.xml       SEO 網址清單(build_sitemap.py 生成)
robots.txt        指向 sitemap
style.css         共用樣式(暗色 + 響應式)
add_day.py        加一篇每日記錄(自動算 Day 編號 + 分類/標籤,並重建 feed/sitemap)
build_db.py       資料庫層:init / build / add / shell(並重建 feed/sitemap)
build_feed.py     由 entries.json 生成 feed.xml
build_sitemap.py  由 entries.json 生成 sitemap.xml
draft_from_git.py 由 trustforge git log 半自動產生日誌草稿(按類型聚合)
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
