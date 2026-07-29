# TrustForge Devlog — 自動接寫規範

本倉庫由 cron 接寫流程（Hermes job `c405843b91d5`，每 12h 一班）自動維護。
任何在此倉庫執行的自動接寫代理，開始前**必須**先讀取並嚴格遵守
[`CONTRIBUTING.md`](./CONTRIBUTING.md) 的文案規範與生成物維護慣例。

## 強制摘要（完整條文見 CONTRIBUTING.md）

1. **禁止 `git push origin --tags`**——須推 tag 時明列具體 tag（如 `v0.27.0 v0.27.1 ...`）。
2. **「版本譜系未閉合」類表述，風險表原因欄須補白話**：
   v0.27.x 仍只是主線 commit／VERSION 檔宣稱，尚未成為可由遠端 tag 稽核的正式版本節點。
3. **「本班無運維變更」與後續「補發滯留稿」須註明不矛盾**（見 CONTRIBUTING.md 第 3 條範本）。

## 生成物維護

- 手寫源頭：`days/*.html`、`_body_*.html`。
- 生成物（**禁止手改**）：`feed.xml`、`entries.json`、`sitemap.xml`、`index.html`。
- 改完源頭後：`python3 build_feed.py`（重建 feed + entries），必要時
  `python3 build_sitemap.py` 與 `python3 add_day.py`（重建 index/feed/sitemap）。
- 提交前：`python3 validate_devlog.py` 須 passed。
- sitemap.xml 一律經 `build_sitemap.py` 生成，從不手編。

## 對外口徑

devlog 由本接寫流程產出，使用者視其為「我（Hermes）寫的」——對外不聲稱
「cron 寫的、不是我」。
