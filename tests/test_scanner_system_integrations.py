from pathlib import Path

from macos_uninstall_inspector.identity import IdentityExtractor
from macos_uninstall_inspector.scanner import ConventionalScanner


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


def test_scanner_finds_launch_agents_and_daemons_by_bundle_id(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    (system_root / "LaunchDaemons").mkdir(parents=True)

    agent = system_root / "LaunchAgents" / "com.example.sample.agent.plist"
    agent.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>com.example.sample.agent</string>
<key>ProgramArguments</key><array><string>/Applications/Sample.app/Contents/MacOS/Sample</string></array>
</dict></plist>
"""
    )
    daemon = system_root / "LaunchDaemons" / "com.example.sample.daemon.plist"
    daemon.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>com.example.sample.daemon</string>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(agent) in by_path
    assert str(daemon) in by_path
    assert "launchd_exact" in by_path[str(agent)]["evidence"]
    assert "launchd_exact" in by_path[str(daemon)]["evidence"]


def test_scanner_finds_privileged_helper_tools_generically(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    system_root = tmp_path / "Library"
    (system_root / "PrivilegedHelperTools").mkdir(parents=True)
    helper = system_root / "PrivilegedHelperTools" / "com.example.sample.helper"
    helper.write_text("binary stub")

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(helper) in by_path
    assert by_path[str(helper)]["evidence"] == ["privileged_helper_exact"]
