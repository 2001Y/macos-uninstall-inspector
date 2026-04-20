from pathlib import Path

from macos_uninstall_inspector.schema_tools import load_packaged_schema


def test_packaged_schema_loads_without_repo_relative_path(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    schema = load_packaged_schema()
    assert schema["title"] == "macOS Uninstall Inspection Report"
