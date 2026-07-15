#!/usr/bin/env python3
"""從 TrustForge 主 repo 的 git commit 流,半自動產生開發日誌草稿。

它不是替你寫文案,而是把當天的真實提交按類型聚合成一篇 HTML 草稿,
你再潤飾成「誠實的開發記錄」。這就是「資料庫/真實來源 → 日誌」的實踐。

用法:
  python3 draft_from_git.py --date 2026-07-15
  python3 draft_from_git.py --since 2026-07-13 --until 2026-07-15 --repo ../trustforge --out draft.html

相依: 需能 `git -C <repo> log`(本地有 trustforge repo)。
"""
import argparse
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
GROUPS = [
    ("新功能 / 產品", ("feat",)),
    ("修正 / 誠實性", ("fix",)),
    ("文件 / 方法論", ("docs",)),
    ("測試 / 回歸鎖", ("test",)),
    ("部署 / 基礎設施", ("ci", "infra", "build", "release")),
]


def git_log(repo, since, until):
    # 只用 hash + subject(單行),用 \x1f 分隔、\x1e 作記錄終結,避免 body 換行破壞解析
    cmd = ["git", "-C", repo, "log", f"--since={since}", f"--until={until}",
           "--format=%x1f%H%x1f%s%x1e"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    rows = []
    for blk in out.split("\x1e"):
        blk = blk.strip("\x1f").strip()
        if not blk or "\x1f" not in blk:
            continue
        h, s = blk.split("\x1f", 1)
        rows.append((h[:8], s.strip()))
    return rows


def classify(subject):
    low = subject.lower()
    for label, keys in GROUPS:
        for k in keys:
            if low.startswith(k + ":") or low.startswith(k + " "):
                return label
    return "其他"


def render(rows):
    by = {}
    for h, s in rows:
        by.setdefault(classify(s), []).append((h, s))
    html = ['<p>本日實際提交紀錄自動彙整（待潤飾為誠實開發記錄）：</p>']
    order = [g[0] for g in GROUPS] + ["其他"]
    for label in order:
        items = by.get(label)
        if not items:
            continue
        html.append(f"<h3>{label}（{len(items)} 筆）</h3><ul>")
        for h, s in items:
            html.append(f"<li><code>{h}</code> {s}</li>")
        html.append("</ul>")
    return "\n".join(html)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=str(ROOT.parent / "trustforge"))
    p.add_argument("--date", help="單日,如 2026-07-15")
    p.add_argument("--since", help="起始日 YYYY-MM-DD")
    p.add_argument("--until", help="結束日 YYYY-MM-DD (含)")
    p.add_argument("--out", help="輸出檔(預設印到 stdout)")
    a = p.parse_args()

    if a.date:
        since = f"{a.date} 00:00:00 +0800"
        until = f"{a.date} 23:59:59 +0800"
    else:
        s = a.since or "1970-01-01"
        u = a.until or "2999-01-01"
        # 強制 +0800 解讀,避免本機 TZ 把提交排在 since 之前而漏掉
        since = s if " " in s else f"{s} 00:00:00 +0800"
        until = u if " " in u else f"{u} 23:59:59 +0800"

    rows = git_log(a.repo, since, until)
    if not rows:
        print(f"（{a.repo} 在 {since} ~ {until} 無提交）")
        return
    html = render(rows)
    if a.out:
        pathlib.Path(a.out).write_text(html, encoding="utf-8")
        print(f"已寫入草稿 {a.out}（{len(rows)} 筆提交）")
    else:
        print(html)


if __name__ == "__main__":
    main()
