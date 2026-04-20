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


def test_cli_inspect_outputs_schema_compatible_json(tmp_path: Path):
    app = make_app(tmp_path, "Claude", "com.anthropic.claudefordesktop")
    context = tmp_path / "context.json"
    context.write_text(
        json.dumps(
            {
                "homebrew_casks": {"com.anthropic.claudefordesktop": "claude"},
                "candidates": [
                    {
                        "path": str(app),
                        "evidence": ["homebrew_cask_artifact", "bundle_path_exact"],
                    }
                ],
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
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["distribution"]["kind"] == "homebrew_cask"
    assert payload["candidates"][0]["ownership"] == "app_owned"
