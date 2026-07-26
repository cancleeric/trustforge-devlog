#!/usr/bin/env python3
"""Evidence-first audit for TrustForge customer docs.

This script is intentionally stricter than validate_devlog.py and is meant to be
run locally by Isabella before customer handoff changes are reported.

It checks canonical docs against:
- TrustForge source repo origin/main docs/api/openapi.yaml
- production live /api/openapi.yaml
- known stale endpoint spellings
- internal links
- repo file references when the source repo is available

It does not read secrets and only performs GET requests to public read-only URLs.
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_REPO = Path("/opt/data/projects/TrustForge")
LIVE_OPENAPI_URL = "https://trustforge.hurricanesoft.com.tw/api/openapi.yaml"

CANONICAL_DOCS = [
    "index.html",
    "00-evidence-map.html",
    "01-workshop-overview.html",
    "02-architecture.html",
    "03-deployment.html",
    "04-configuration.html",
    "05-api.html",
    "06-data-flow.html",
    "07-operations.html",
    "08-trust-algorithm.html",
    "09-frontend.html",
    "10-security-handover.html",
    "11-testing-qa.html",
    "12-customer-handover.html",
    "13-hands-on-labs.html",
    "14-troubleshooting-faq.html",
    "15-user-manual.html",
    "16-competition-submission.html",
]

STALE_MARKERS = [
    "/api/analysis/flow",
    "/api/analysis/snapshot",
    "/api/analysis/job",
    "/api/analysis/question",
    "/api/analysis/comparison",
    "/api/analysis/requeue",
    "/api/analysis/journey",
    "/api/hermes/upgrades",
    "/api/admin/upgrade-queue",
    "/api/admin/upgrade-action",
    "1982 行",
    "0.18.2",
    "3dac00f",
]

# These are not literal OpenAPI paths.
ALLOWED_API_WILDCARDS = {"/api/*", "/api/admin/*"}
ALLOWED_NON_OPENAPI = {"/healthz", "/api/docs"} | ALLOWED_API_WILDCARDS
GENERATED_OUTPUT_REFS = {"report.md", "evidence.json", "execution_log.jsonl"}

FILE_REF_RE = re.compile(
    r"<code>([^<]*(?:\.py|\.ts|\.tsx|\.yaml|\.yml|\.sh|\.md|\.json|"
    r"package\.json|pyproject\.toml|nginx\.conf|llms\.txt)[^<]*)</code>"
)
API_REF_RE = re.compile(r"/api/[A-Za-z0-9_./{}*-]+|/llms\.txt|/healthz")
OPENAPI_PATH_RE = re.compile(r"^  (/[^:]+):\s*$", re.M)


def run(cmd: str, cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, shell=True, text=True, stderr=subprocess.STDOUT)


def read_live_openapi() -> str:
    with urllib.request.urlopen(LIVE_OPENAPI_URL, timeout=20) as response:
        return response.read().decode("utf-8")


def source_git_files(source_repo: Path) -> set[str]:
    if not (source_repo / ".git").exists():
        return set()
    return set(run("git ls-tree -r --name-only origin/main", source_repo).splitlines())


def ref_exists(ref: str, files: set[str]) -> bool:
    normalized = ref.removeprefix("./")
    if normalized.startswith("out/"):
        # Runtime output examples, not repo files.
        return True
    if normalized in files:
        return True
    return any(path.endswith("/" + normalized) for path in files)


def main() -> int:
    source_repo = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE_REPO
    docs_dir = ROOT / "docs"
    errors: list[str] = []
    warnings: list[str] = []

    origin_openapi = ""
    origin_paths: set[str] = set()
    files: set[str] = set()
    if (source_repo / ".git").exists():
        run("git fetch --all --prune", source_repo)
        origin_openapi = run("git show origin/main:docs/api/openapi.yaml", source_repo)
        origin_paths = set(OPENAPI_PATH_RE.findall(origin_openapi))
        files = source_git_files(source_repo)
    else:
        warnings.append(f"source repo not found: {source_repo}")

    live_openapi = read_live_openapi()
    live_paths = set(OPENAPI_PATH_RE.findall(live_openapi))
    known_paths = origin_paths | live_paths | ALLOWED_NON_OPENAPI
    repo_only = origin_paths - live_paths

    for name in CANONICAL_DOCS:
        path = docs_dir / name
        if not path.exists():
            errors.append(f"docs/{name}: missing canonical doc")
            continue
        text = path.read_text(encoding="utf-8")

        for match in API_REF_RE.finditer(text):
            ref = match.group(0).rstrip(".,;:)</")
            base = ref.split("?", 1)[0]
            if base not in known_paths:
                errors.append(f"docs/{name}: unknown API reference {ref}")

        for stale in STALE_MARKERS:
            if stale in text:
                errors.append(f"docs/{name}: stale marker {stale}")

        if files:
            for raw in FILE_REF_RE.findall(text):
                for part in re.split(r"[、,，\s]+", html.unescape(raw)):
                    ref = part.strip("`。；;:()（）")
                    if not ref or "*" in ref or ref.startswith("/") or "=" in ref:
                        continue
                    if ref in {"GET", "PUT", "POST", ".test.tsx"} or ref in GENERATED_OUTPUT_REFS:
                        continue
                    if re.search(
                        r"(\.py|\.ts|\.tsx|\.yaml|\.yml|\.sh|\.md|\.json|"
                        r"package\.json|pyproject\.toml|nginx\.conf|llms\.txt)$",
                        ref,
                    ) and not ref_exists(ref, files):
                        warnings.append(f"docs/{name}: unresolved file ref {ref}")

    api_doc = (docs_dir / "05-api.html").read_text(encoding="utf-8")
    evidence_doc = (docs_dir / "00-evidence-map.html").read_text(encoding="utf-8")

    if origin_openapi:
        origin_lines = len(origin_openapi.splitlines())
        if f"{origin_lines} 行" not in api_doc:
            errors.append(f"docs/05-api.html: missing origin OpenAPI line count {origin_lines} 行")
    live_lines = len(live_openapi.splitlines())
    if f"{live_lines} 行" not in api_doc:
        errors.append(f"docs/05-api.html: missing live OpenAPI line count {live_lines} 行")

    if repo_only:
        for marker in ["repo 支援／待部署驗證", "production live spec 尚未列出"]:
            if marker not in api_doc:
                errors.append(f"docs/05-api.html: missing repo/live divergence marker {marker!r}")
        if "production live OpenAPI" not in evidence_doc:
            errors.append("docs/00-evidence-map.html: missing source/live OpenAPI divergence note")

    print(f"origin_paths={len(origin_paths)} live_paths={len(live_paths)} repo_only={sorted(repo_only)}")
    print(f"errors={len(errors)} warnings={len(warnings)}")
    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARN: {warning}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
