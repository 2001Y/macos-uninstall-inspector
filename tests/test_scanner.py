from pathlib import Path

from macos_uninstall_inspector.identity import IdentityExtractor
from macos_uninstall_inspector.scanner import ConventionalScanner


def make_app(tmp_path: Path, name: str, bundle_id: str, extra_plist: str = "") -> Path:
    app = tmp_path / f"{name}.app"
    contents = app / "Contents"
    (contents / "Library" / "LoginItems").mkdir(parents=True)
    (contents / "Library" / "LoginItems" / "Helper.app").mkdir(parents=True)
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


def test_conventional_scanner_finds_embedded_and_library_state(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    home = tmp_path / "home"
    (home / "Library" / "Preferences").mkdir(parents=True)
    (home / "Library" / "Caches").mkdir(parents=True)
    (home / "Library" / "Preferences" / "com.example.sample.plist").write_text("x")
    (home / "Library" / "Caches" / "com.example.sample").mkdir()

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=home).scan(identity)
    found_paths = {item["path"] for item in findings}

    assert str(app / "Contents" / "Library" / "LoginItems" / "Helper.app") in found_paths
    assert str(home / "Library" / "Preferences" / "com.example.sample.plist") in found_paths
    assert str(home / "Library" / "Caches" / "com.example.sample") in found_paths


def test_conventional_scanner_marks_vendor_token_matches_as_heuristic(tmp_path: Path):
    app = make_app(tmp_path, "Creative Cloud", "com.adobe.accmac")
    home = tmp_path / "home"
    (home / "Library" / "Application Support" / "Adobe").mkdir(parents=True)

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=home).scan(identity)

    adobe_dir = next(item for item in findings if item["path"].endswith("Application Support/Adobe"))
    assert adobe_dir["evidence"] == ["vendor_suite_path", "shared_support_directory"]


def test_conventional_scanner_finds_app_group_containers_and_scripts(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    contents = app / "Contents"
    (contents / "Entitlements.plist").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>com.apple.security.application-groups</key>
<array><string>group.com.example.shared</string></array>
</dict></plist>
"""
    )
    home = tmp_path / "home"
    group_container = home / "Library" / "Group Containers" / "group.com.example.shared"
    app_scripts = home / "Library" / "Application Scripts" / "group.com.example.shared"
    group_container.mkdir(parents=True)
    app_scripts.mkdir(parents=True)

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=home).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(group_container) in by_path
    assert str(app_scripts) in by_path
    assert by_path[str(group_container)]["evidence"] == ["app_group_entitlement_exact", "group_container_exact"]
    assert by_path[str(app_scripts)]["evidence"] == ["app_group_entitlement_exact", "application_scripts_exact"]


def test_conventional_scanner_finds_application_scripts_by_bundle_id(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    home = tmp_path / "home"
    app_scripts = home / "Library" / "Application Scripts" / "com.example.sample"
    app_scripts.mkdir(parents=True)

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=home).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(app_scripts) in by_path
    assert by_path[str(app_scripts)]["evidence"] == ["bundle_id_exact", "application_scripts_exact"]
