from pathlib import Path

from macos_uninstall_inspector.inspector import Inspector


def make_app(tmp_path: Path, name: str, bundle_id: str, extra_plist: str = "") -> Path:
    app = tmp_path / f"{name}.app"
    contents = app / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_text(
        f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>{name}</string>
<key>CFBundleIdentifier</key><string>{bundle_id}</string>
<key>CFBundleExecutable</key><string>{name}</string>
{extra_plist}
</dict></plist>
"""
    )
    return app


def test_inspector_prefers_structured_evidence_and_filters_modes(tmp_path: Path):
    app = make_app(tmp_path, "Claude", "com.anthropic.claudefordesktop")
    report = Inspector().inspect(
        app,
        context={
            "homebrew_casks": {"com.anthropic.claudefordesktop": "claude"},
            "candidates": [
                {
                    "path": str(app),
                    "evidence": ["homebrew_cask_artifact", "bundle_path_exact"],
                },
                {
                    "path": str(tmp_path / "Library" / "Preferences" / "com.anthropic.claudefordesktop.plist"),
                    "evidence": ["bundle_id_exact", "preferences_conventional_path"],
                },
                {
                    "path": str(tmp_path / "Library" / "Logs" / "Claude"),
                    "evidence": ["app_name_exact", "logs_conventional_path"],
                },
                {
                    "path": str(tmp_path / "Library" / "Application Support" / "Anthropic"),
                    "evidence": ["vendor_token_match"],
                },
            ],
        },
    )

    assert report.distribution.kind == "homebrew_cask"
    by_path = {candidate.path: candidate for candidate in report.candidates}

    assert by_path[str(app)].ownership == "app_owned"
    assert by_path[str(app)].score >= 90
    assert by_path[str(tmp_path / "Library" / "Preferences" / "com.anthropic.claudefordesktop.plist")].modes == ["safe", "balanced", "aggressive"]
    assert by_path[str(tmp_path / "Library" / "Logs" / "Claude")].modes == ["balanced", "aggressive"]
    assert by_path[str(tmp_path / "Library" / "Application Support" / "Anthropic")].ownership == "heuristic_only"
    assert by_path[str(tmp_path / "Library" / "Application Support" / "Anthropic")].modes == ["aggressive"]


def test_inspector_marks_vendor_shared_assets(tmp_path: Path):
    app = make_app(tmp_path, "Creative Cloud", "com.adobe.accmac")
    report = Inspector().inspect(
        app,
        context={
            "candidates": [
                {
                    "path": "/Library/Application Support/Adobe",
                    "evidence": ["vendor_suite_path", "shared_support_directory"],
                }
            ]
        },
    )

    candidate = report.candidates[0]
    assert report.distribution.kind == "vendor_suite"
    assert candidate.ownership == "vendor_shared"
    assert "likely_shared_across_suite" in candidate.warnings
