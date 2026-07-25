#!/usr/bin/env python3
"""TrustForge 開發日誌接管腳本（Hermes 版，不跑測試）。

每 12 小時跑一次（台灣 11:00 / 23:00 = UTC 03:00 / 15:00）：
  1. 動態取 gh token（不落盤），fetch trustforge + devlog 最新
  2. 算近 13h 的 non-merge commit 差異（清單）
  3. 用 add_day.py 套版生成 HTML + 更新 entries.json
  4. commit + push 到 cancleeric/trustforge-devlog（公開 GitHub Pages）

不執行 pytest / npm build（依據 boss 指示：不要跑測試）。
只產生開發「記錄」，不修改 trustforge 主 repo、不部署、不改模型權重。
"""
import datetime
import pathlib
import subprocess

ROOT = pathlib.Path("/opt/data/devlog")
TF = pathlib.Path("/opt/data/trustforge")
ADD_DAY = ROOT / "add_day.py"

SLOT_SUFFIX = {"03:00": "", "15:00": "-night"}  # UTC -> 同日多篇後綴


def run(cmd, cwd=None, timeout=300, capture=True):
    res = subprocess.run(cmd, cwd=cwd, text=True,
                         capture_output=capture, timeout=timeout)
    return res.returncode, res.stdout, res.stderr


def gh_token():
    code, out, err = run(["gh", "auth", "token"])
    if code != 0 or not out.strip():
        raise RuntimeError(f"gh auth token 失敗: {err.strip()}")
    return out.strip()


def authed_url(repo_https, token):
    return repo_https.replace("https://", "https://x-access-token:" + token + "@")


def git_fetch(repo_path, token):
    url = authed_url("https://github.com/cancleeric/TrustForge.git", token) \
        if repo_path == TF else \
        authed_url("https://github.com/cancleeric/trustforge-devlog.git", token)
    code, out, err = run(["git", "fetch", "--prune", url], cwd=repo_path, timeout=300)
    return code, out + err


def main():
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    slot = "03:00" if now.hour < 12 else "15:00"
    suffix = SLOT_SUFFIX.get(slot, "")
    date_id = today + suffix

    print(f"[gen] {now.isoformat()} slot={slot} date_id={date_id}", flush=True)
    token = gh_token()

    # 1. fetch 雙邊
    for label, p in (("trustforge", TF), ("devlog", ROOT)):
        code, msg = git_fetch(p, token)
        print(f"[fetch {label}] exit={code} {msg.strip()[:120]}", flush=True)

    # 2. heads
    _, omain, _ = run(["git", "rev-parse", "origin/main"], cwd=TF)
    _, odev, _ = run(["git", "rev-parse", "origin/develop"], cwd=TF)
    main_head = (omain.strip() or "unknown")[:10]
    dev_head = (odev.strip() or main_head)[:10]

    # 近 13h non-merge commit
    since = (now - datetime.timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%S")
    _, log_out, _ = run(
        ["git", "-C", str(TF), "log", f"--since={since}", "--no-merges",
         "--format=%h %s"])
    commits = [l.strip() for l in log_out.strip().splitlines() if l.strip()]
    n_commit = len(commits)

    # 3. body
    commit_items = "\n".join(
        f"<li><code>{c.split(' ',1)[0]}</code> {c.split(' ',1)[1] if ' ' in c else ''}</li>"
        for c in commits[:40]) or "<li>（本班無新 non-merge commit）</li>"
    body = f"""<section>
  <h3>本班自動產出概要</h3>
  <ul>
    <li><strong>執行時間：</strong>{now.strftime('%Y-%m-%d %H:%M:%S')}（本地）</li>
    <li><strong>main HEAD：</strong><code>{main_head}</code> ｜ <strong>develop HEAD：</strong><code>{dev_head}</code></li>
    <li><strong>近 13h non-merge commit：{n_commit} 筆（不跑測試，依 boss 指示）</strong></li>
  </ul>
</section>

<section>
  <h3>提交清單（近 13h）</h3>
  <ul>
{commit_items}
  </ul>
</section>

<section>
  <h3>驗證／測試狀態</h3>
  <p>依 boss 指示，本班<strong>不執行 pytest / npm build</strong>。僅記錄 git 差異與提交清單。</p>
</section>

<section>
  <h3>誠實邊界</h3>
  <ul>
    <li>本篇由 Hermes 接管排程自動產出，僅記錄 git 差異與提交清單，不修改 trustforge 主 repo、不部署、不調權重、不跑測試。</li>
    <li>若本班無新 commit，仍保留紀錄以利追溯；不虛構進度。</li>
    <li>未執行測試不代表程式碼綠燈；如需驗證狀態請另行手動跑 gate。</li>
  </ul>
</section>
"""
    body_path = ROOT / f"_body_{date_id}.html"
    body_path.write_text(body, encoding="utf-8")

    title = f"Day auto · {today} {'午' if slot=='03:00' else '夜'}班自動記錄"
    summary = (f"TrustForge main={main_head} develop={dev_head}；"
               f"近13h {n_commit} 筆 non-merge commit（不跑測試）。")
    tags = "trustforge,continuous-analysis,auto-devlog"

    code, out, err = run(
        ["python3", str(ADD_DAY), "--date", date_id, "--title", title,
         "--summary", summary, "--body", str(body_path),
         "--category", "Continuous Analysis", "--tags", tags], cwd=ROOT)
    print(f"[add_day] exit={code} {out.strip()[:160]} {err.strip()[:160]}", flush=True)

    # 4. commit + push devlog
    run(["git", "add", "-A"], cwd=ROOT)
    run(["git", "commit", "-m", f"devlog {date_id} auto by Hermes"], cwd=ROOT)
    push_url = authed_url("https://github.com/cancleeric/trustforge-devlog.git", token)
    code, out, err = run(["git", "push", push_url, "HEAD:refs/heads/main"], cwd=ROOT, timeout=300)
    print(f"[push devlog] exit={code} {out.strip()[:100]} {err.strip()[:100]}", flush=True)

    body_path.unlink(missing_ok=True)
    print("[done]", flush=True)


if __name__ == "__main__":
    main()
