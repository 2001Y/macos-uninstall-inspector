from pathlib import Path

from macos_uninstall_inspector.inspector import Inspector


def make_app(tmp_path: Path, name: str, bundle_id: str) -> Path:
    app = tmp_path / f"{name}.app"
    contents = app / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_text(
        f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>{name}</string>
<key>CFBundleIdentifier</key><string>{bundle_id}</string>
</dict></plist>
"""
    )
    return app


def test_candidates_below_aggressive_threshold_have_no_modes(tmp_path: Path):
    app = make_app(tmp_path, "Creative Cloud", "com.adobe.accmac")
    report = Inspector().inspect(
        app,
        context={
            "candidates": [
                {"path": "/Library/Application Support/Adobe", "evidence": ["vendor_suite_path", "shared_support_directory"]}
            ]
        },
    )

    candidate = report.candidates[0]
    assert candidate.score < report.mode_thresholds["aggressive"]
    assert candidate.modes == []
