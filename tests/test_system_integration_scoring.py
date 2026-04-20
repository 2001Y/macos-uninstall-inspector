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


def test_system_integrations_are_classified_separately(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    report = Inspector().inspect(
        app,
        context={
            "candidates": [
                {
                    "path": "/Library/LaunchDaemons/com.example.sample.daemon.plist",
                    "evidence": ["launchd_exact"],
                },
                {
                    "path": "/Library/PrivilegedHelperTools/com.example.sample.helper",
                    "evidence": ["privileged_helper_exact"],
                },
            ]
        },
    )
    by_path = {c.path: c for c in report.candidates}
    assert by_path["/Library/LaunchDaemons/com.example.sample.daemon.plist"].ownership == "system_integrated"
    assert by_path["/Library/PrivilegedHelperTools/com.example.sample.helper"].ownership == "system_integrated"
    assert by_path["/Library/LaunchDaemons/com.example.sample.daemon.plist"].score >= 70
