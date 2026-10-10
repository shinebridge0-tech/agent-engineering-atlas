"""Build a local-only source archive from an explicit allowlist; never follow links."""
import hashlib
import json
import shutil
import stat
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ["README.md", "README.zh-CN.md", "CONTRIBUTING.md", "SECURITY.md",
         "CODE_OF_CONDUCT.md", "CHANGELOG.md", ".gitignore", "pyproject.toml", "requirements.lock.txt",
         "content/TEMPLATE.md", "docs/CASE_SCHEMA.json", "docs/SOURCE_ACQUISITION.json",
         "docs/LICENSING.md", "LICENSE", "LICENSE-CONTENT.md", "docs/ROADMAP.md", "docs/ALPHA_PUBLIC_SUMMARY.md",
         "web/package.json", "web/package-lock.json", "web/index.html", "web/tsconfig.json",
         "web/vite.config.ts", "web/vitest.config.ts", "web/playwright.config.ts", "web/eslint.config.js"]
TREES = {"backend": {".py"}, "scripts": {".py"}, "experiments": {".py"},
         "tests": {".py", ".md", ".json", ".sha256"}, "content/cases": {".md"},
         "web/src": {".ts", ".tsx", ".css"}, "web/e2e": {".ts"},
         ".github": {".yml", ".md"}}


def linked(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def collect(root=ROOT):
    included, excluded = [], []

    def walk(path):
        if linked(path):
            excluded.append({"path": path.relative_to(root).as_posix(), "reason": "link/reparse point"})
        elif path.is_dir():
            for child in sorted(path.iterdir()):
                if child.name != "__pycache__":
                    walk(child)
        else:
            included.append(path)

    for name in FILES:
        path = root / name
        if any(linked(p) for p in [path, *list(path.parents)[:len(Path(name).parts)-1]]):
            excluded.append({"path": name, "reason": "link/reparse point"})
        else:
            included.append(path)
    for name, extensions in TREES.items():
        before = len(included)
        walk(root / name)
        included[before:] = [p for p in included[before:] if p.suffix in extensions]
    return sorted(set(included)), excluded


def main():
    target = ROOT / "artifacts/alpha-prep" / datetime.now().strftime("%Y%m%d-%H%M%S")
    target.mkdir(parents=True, exist_ok=False)
    stage = target / "source"
    paths, excluded = collect()
    manifest = []
    for path in paths:
        relative = path.relative_to(ROOT)
        dest = stage / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        manifest.append({"path": relative.as_posix(), "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
    status = "LOCAL PREPARATION ONLY / 未发布 / 许可与发布授权待确认\n"
    (stage / "LOCAL_PREPARATION_ONLY.txt").write_text(status, encoding="utf-8")
    manifest.append({"path": "LOCAL_PREPARATION_ONLY.txt",
                     "sha256": hashlib.sha256((stage / "LOCAL_PREPARATION_ONLY.txt").read_bytes()).hexdigest()})
    metadata = {"status": status.strip(), "files": manifest, "excluded_links": excluded,
                "excluded_categories": [".env/credentials/private data", ".venv/node_modules/web/dist",
                 ".local/caches/index/logs/backups/source snapshots", "starter/prompts/history reports",
                 "unconfirmed third-party mirrors/assets", "artifacts"]}
    (target / "manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    archive = target / "agentatlas-alpha-prep-local-source.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for row in manifest:
            output.write(stage / row["path"], row["path"])
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (target / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(json.dumps({"directory": str(target), "files": len(manifest), "sha256": digest}))


if __name__ == "__main__":
    main()
