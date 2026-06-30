# TrustForge 開發記錄（GitHub Pages）

TrustForge（加密市場分析 AI Agent · HOYA BIT 黑客松）的**每日開發記錄**靜態站。
原始碼為私有 repo（`cancleeric/trustforge`);本站僅公開記錄開發歷程,且力求**詳細到可照做重現**。

## 線上
GitHub Pages: https://cancleeric.github.io/trustforge-devlog/

## 結構
```
index.html        首頁(JS 讀 entries.json 列出每日)
entries.json      每日索引(date/title/file/summary)
days/<date>.html  每日一頁
style.css         共用樣式
add_day.py        加一篇每日記錄的工具
.nojekyll         停用 Jekyll(直接服務靜態檔)
```

## 每天加一頁
```bash
# 1) 把當日內文寫成 HTML 片段(<h3>/<ul>/<pre><code> …)存成 body.html
# 2) 產頁 + 更新索引
python3 add_day.py --date 2026-07-01 --title "Day 2 — XXX" \
    --summary "一句話摘要" --body body.html
# 3) push(GitHub Pages 自動更新)
git add -A && git commit -m "devlog: 2026-07-01" && git push
```
