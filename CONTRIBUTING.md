# TrustForge Devlog 文案規範（自動接寫必遵守）

本檔由 `software-development` skill 驅動的 cron 接寫流程（job `c405843b91d5`）在每班
接寫前必讀。違反任一條即視為該班輸出不合格，須修正後再 commit。

來源：2026-07-28 / 07-28b / 07-29 三篇人工「語病／文案合理性」review 結論
（靜態 validate_devlog.py passed、線上三頁 200 確認）。

## 1. 禁止危險 git 指令

- **禁止**在「下一步 checklist」或任何建議指令中寫 `git push origin --tags`。
  該指令會推本地**所有** tag，風險過大。
- 須推 tag 時，**明列具體 tag**，例如：
  `git push origin v0.27.0 v0.27.1 v0.27.2 v0.27.3 v0.27.4`
- 同一 checklist 項若含 `git push`，應緊接一句禁止 `--tags` 的註記。

## 2. 「版本譜系未閉合」須講白

- 凡出現「v0.27.x 遠端 tag 為零／版本譜系未閉合」類表述，風險表「原因」欄
  **必須補一句白話**：
  > 目前 v0.27.x 仍只是主線 commit／VERSION 檔宣稱，尚未成為可由遠端 tag 稽核的正式版本節點。
- 目的：避免讀者誤以為版號已具備可稽核的正式節點地位。

## 3. 「本班無運維變更」與「補發滯留稿」不矛盾，須註明

- 當某班記「本班無運維變更（已實際查證）」，而後續班次補發了前班滯留稿時，
  該「無變更」班**必須在段落末補註**：
  > 因原班未進入 commit／push 流程，故原觀測窗內仍記為 devlog repo 無運維變更；
  > 後續由 X 班補發之前班滯留稿，不影響本班「觀測窗內無變更」之結論。
- 目的：避免讀者把「當班無變更」與「後來補發前班稿」誤讀為矛盾。

## 維護慣例（與生成物相關）

- `days/*.html` 與 `_body_*.html` 為**手寫源頭**；`feed.xml` / `entries.json` /
  `sitemap.xml` / `index.html` 皆由腳本生成，**禁止手改生成物**。
- 改完源頭後，重跑 `python3 build_feed.py`（會連帶重建 entries.json），
  必要時 `python3 build_sitemap.py` + `python3 add_day.py`（重建 index/feed/sitemap）。
- `sitemap.xml` 一律經 `build_sitemap.py` 生成，從不手編。
- 提交前跑 `python3 validate_devlog.py`，須 passed。
- devlog 由 cron 接寫，使用者視其輸出為「我（Hermes）寫的」——對外不聲稱
  「cron 寫的、不是我」。
