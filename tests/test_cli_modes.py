import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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


def test_cli_mode_filters_candidates(tmp_path: Path):
    app = make_app(tmp_path, "Creative Cloud", "com.adobe.accmac")
    context = tmp_path / "context.json"
    context.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "path": "/Library/Application Support/Adobe",
                        "evidence": ["vendor_suite_path", "shared_support_directory"],
                    }
                ]
            }
        )
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "macos_uninstall_inspector.cli",
            "inspect",
            str(app),
            "--context",
            str(context),
            "--mode",
            "safe",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["candidates"] == []
