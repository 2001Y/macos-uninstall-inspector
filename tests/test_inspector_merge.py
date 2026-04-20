from pathlib import Path

from macos_uninstall_inspector.inspector import Inspector


def make_app(tmp_path: Path, name: str, bundle_id: str) -> Path:
    app = tmp_path / f"{name}.app"
    contents = app / "Contents"
    (contents / "Library" / "Helpers").mkdir(parents=True)
    (contents / "Info.plist").write_text(
        f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>{name}</string>
<key>CFBundleIdentifier</key><string>{bundle_id}</string>
</dict></plist>
"""
    )
    helper = contents / "Library" / "Helpers" / "helper-tool"
    helper.write_text("x")
    return app


def test_inspector_merges_duplicate_evidence_for_same_path(tmp_path: Path):
    app = make_app(tmp_path, "Claude", "com.anthropic.claudefordesktop")
    report = Inspector().inspect(
        app,
        context={
            "homebrew_casks": {"com.anthropic.claudefordesktop": "claude"},
            "candidates": [
                {
                    "path": str(app / "Contents" / "Library" / "Helpers" / "helper-tool"),
                    "evidence": ["homebrew_cask_artifact"],
                }
            ],
        },
    )

    helper = next(c for c in report.candidates if c.path.endswith("helper-tool"))
    assert "homebrew_cask_artifact" in helper.evidence
    assert "embedded_helper_path" in helper.evidence
    assert helper.score >= 100
