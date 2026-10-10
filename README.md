# Agent Engineering Atlas — Agent engineering fieldnotes and decision workbench

[中文](README.zh-CN.md). Agent engineering Alpha v0.1.0-alpha.1. Maintained by [@shinebridge0-tech](https://github.com/shinebridge0-tech). [Repository](https://github.com/shinebridge0-tech/agent-engineering-atlas) · [Issues](https://github.com/shinebridge0-tech/agent-engineering-atlas/issues) · [Releases](https://github.com/shinebridge0-tech/agent-engineering-atlas/releases).

Question + project constraints → candidates → hard exclusions → comparison → evidence → Markdown / JSON implementation and validation material.
The core uses local keyword/rule assistance, needs no model key, and runs offline after dependencies/content are prepared. It does not execute external tools or pretend to offer model chat.

## Windows quick start

Verified with Python 3.11.9 and Node 24.18.0 in a Windows path containing spaces. Use already installed runtimes.

```powershell
# Enter the extracted source directory / 进入解压后的源码目录
Set-Location '<your extracted source directory>'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --cache-dir .local/pip-cache -r requirements.lock.txt
Push-Location web
npm ci --cache ../.local/npm-cache
npm run build
Pop-Location
.\.venv\Scripts\python.exe -m backend validate
.\.venv\Scripts\python.exe -m backend rebuild
.\.venv\Scripts\python.exe -m scripts.serve
```

Open [localhost](http://127.0.0.1:18765). Keep the terminal open; **Ctrl+C** stops its own foreground process. Re-run the last command to restart.
An occupied/unavailable port aborts startup without terminating its owner or changing system settings. Windows refused port 8765; 18765 was verified. Automated background lifecycle was approval-blocked; the delivered foreground lifecycle needs no process termination privileges.

## Acceptance

Choose the recovery cluster for the default duplicate-ticket question. Explicitly set approval policy to yes, then toggle idempotency unknown/yes/no and recompute: the stable-key card becomes conditional/compatible/incompatible. Forbid sqlite to exclude its dependent proposals. Compare 2–3 non-excluded cards, inspect claim kinds and pinned sources, then download Markdown and JSON. Changed inputs require recomputation before export. A question outside the corpus reports insufficient evidence. Stop/restart and refresh: content/index return; private questions and selections are intentionally not persisted.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check backend tests scripts experiments
.\.venv\Scripts\python.exe -m scripts.run_experiments
.\.venv\Scripts\python.exe -m scripts.evaluate
Push-Location web
npm run build
npm run lint
npm test
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\..\.local\browsers"
npx playwright install chromium
# With the server running in another terminal:
npx playwright test
Pop-Location
```

For Unix-like shells (not tested here), substitute `.venv/bin/python`, `cd web` / `cd ..`, and `PLAYWRIGHT_BROWSERS_PATH="$PWD/../.local/browsers" npx playwright test`. Python and npm module commands are otherwise the same. No Linux/macOS acceptance claim.

## Evidence and limitations

Markdown + YAML is canonical; SQLite is rebuildable. Safe parsing, bounded queries, bilingual aliases/Chinese short-word fallback, hard exclusions and critical-unknown gates are implemented. FTS5 is detected but not required for ranking. Rebuild failures preserve the last usable index and expose a health diagnostic. Relevance is not a probability, and absent latency measurements cannot establish budget compliance.

10 checked source-backed summaries: recovery 4 / retrieval 3 / safety 3. source_checked 10, draft/reviewed 0; all upstream card validations are not_run. The two separate project-authored experiments demonstrate only local simulated mechanisms. Release-version compatibility is unknown. Source licensing is not verified: metadata, links and original summaries only; no upstream executable code redistribution.

The 12 frozen scenarios are self-built development regression, not independent review or an industry benchmark. Paid model comparison NOT_RUN. Project model API calls/cost: 0. No private uploads, telemetry, external repository execution or other-project scanning.

Real Windows escaping-symlink creation test was skipped for missing privilege; traversal/root checks remain implemented. Reports and browser assets are ignored in `.local`. See [validation](docs/ALPHA_PUBLIC_SUMMARY.md), [status](docs/ALPHA_PUBLIC_SUMMARY.md), [contributing](CONTRIBUTING.md), [security](SECURITY.md), [conduct](CODE_OF_CONDUCT.md), [license scope](docs/LICENSING.md) and [roadmap](docs/ROADMAP.md).

CI checks the exact pushed commit and does not publish automatically. See the commit-specific Actions run for results; independent human content review remains unperformed.

## Alpha v0.1.0-alpha.1

Software/original executable examples: Apache-2.0; original explanatory content: CC BY 4.0. [License scope](docs/LICENSING.md).Enter your extracted source directory instead of the author's drive. Dependencies are not bundled; initial pip/npm installation needs registry access or populated caches. Runtime needs no model key. 不声称安装全过程无网络。

Approval means project policy, not actual tool authorization or proof of an approval service. With approval unknown and idempotency yes, stable-idempotency remains conditional; inspect missing approval confirmation. 明确确认政策后重查；输入变化禁用导出，索引内容变化使旧导出409，必须重新查询。Compare two non-excluded cards, inspect evidence and download both Markdown and JSON. 导出保留输入/内容修订、review/validation/freshness和unknown。

Frozen target retrieval 6/6; confirmed applicability 4/6; conditional 2/6 (approval missing); retained old probes 11/13. 显式确认变体单独登记，不替换原冻结输入。10 cards are zh-CN: recovery4/retrieval3/safety3; source_checked/current/not_run10; reviewed0. English queries/aliases work, formal English card translations are absent. Original experiments are local simulations; upstream execution/version compatibility/production validation remain unverified.

Raw snapshots/private reports are excluded from the ZIP; cards retain public URLs, commits, paths, locations, dates and hashes. [Evidence summary](docs/ALPHA_PUBLIC_SUMMARY.md). Browser automation is optional and Chromium installation is a separate download; an authorized browser cache may be selected with PLAYWRIGHT_BROWSERS_PATH. The stale-content browser test needs explicit isolated AGENTATLAS_R1_BROWSER_WORKSPACE and AGENTATLAS_R1_PYTHON, otherwise skips. Manual demonstration uses an existing browser. Same-machine Windows ZIP isolation does not establish independent or Linux/macOS reproduction. Real symlink/junction validation remains unverified.
