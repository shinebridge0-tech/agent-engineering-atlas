from pathlib import Path
import hashlib
import json
import zipfile

from scripts import prepare_alpha


def test_allowlist_excludes_work_data_and_dependencies():
    files, links = prepare_alpha.collect()
    relative = [p.relative_to(prepare_alpha.ROOT).as_posix() for p in files]
    assert "backend/app.py" in relative
    assert "web/package-lock.json" in relative
    assert "docs/SOURCE_ACQUISITION.json" in relative
    assert not links
    assert not any(p.startswith((".local/", "artifacts/", "web/node_modules/", "web/dist/")) for p in relative)
    assert not any(Path(p).name.startswith(".env") for p in relative)


def test_reparse_point_excluded_without_following(tmp_path, monkeypatch):
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend/app.py").write_text("pass")
    (tmp_path / "backend/linked").mkdir()
    (tmp_path / "backend/linked/private.py").write_text("must not copy")
    monkeypatch.setattr(prepare_alpha, "FILES", [])
    monkeypatch.setattr(prepare_alpha, "TREES", {"backend": {".py"}})
    monkeypatch.setattr(prepare_alpha, "linked", lambda p: p.name == "linked")
    files, excluded = prepare_alpha.collect(tmp_path)
    assert [p.name for p in files] == ["app.py"]
    assert excluded == [{"path": "backend/linked", "reason": "link/reparse point"}]


def test_zip_manifest_hashes_actual_bytes(tmp_path, monkeypatch):
    source = tmp_path / "original.txt"
    source.write_text("original\n")
    monkeypatch.setattr(prepare_alpha, "ROOT", tmp_path)
    monkeypatch.setattr(prepare_alpha, "collect", lambda: ([source], []))
    prepare_alpha.main()
    target = next((tmp_path / "artifacts/alpha-prep").iterdir())
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(target / "agentatlas-alpha-prep-local-source.zip") as archive:
        for row in manifest["files"]:
            assert hashlib.sha256(archive.read(row["path"])).hexdigest() == row["sha256"]
