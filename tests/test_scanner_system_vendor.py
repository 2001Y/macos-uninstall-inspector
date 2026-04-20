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


def test_scanner_checks_system_adobe_shared_path(tmp_path: Path):
    app = make_app(tmp_path, "Creative Cloud", "com.adobe.accmac")
    system_root = tmp_path / "system"
    (system_root / "Application Support" / "Adobe").mkdir(parents=True)
    identity = IdentityExtractor().extract(app)

    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)

    adobe_dir = next(item for item in findings if item["path"].endswith("Application Support/Adobe"))
    assert adobe_dir["evidence"] == ["vendor_suite_path", "shared_support_directory"]
