from pathlib import Path
from types import SimpleNamespace

from macos_uninstall_inspector.identity import IdentityExtractor


def test_extract_identity_from_app_bundle(tmp_path: Path):
    app = tmp_path / "Sample App.app"
    contents = app / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>Sample App</string>
<key>CFBundleDisplayName</key><string>Sample App</string>
<key>CFBundleIdentifier</key><string>com.example.sample</string>
<key>CFBundleExecutable</key><string>SampleApp</string>
<key>SMPrivilegedExecutables</key><dict>
  <key>com.example.sample.helper</key><string>identifier helper</string>
</dict>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)

    assert identity.path == app
    assert identity.display_name == "Sample App"
    assert identity.bundle_id == "com.example.sample"
    assert identity.executable_name == "SampleApp"
    assert identity.vendor == "example"
    assert identity.search_tokens.exact_names == ["Sample App", "SampleApp"]
    assert "sample app" in identity.search_tokens.normalized_names
    assert "sampleapp" in identity.search_tokens.normalized_names
    assert identity.embedded_bundle_ids == ["com.example.sample.helper"]


def test_setapp_bundle_marks_distribution_hint(tmp_path: Path):
    app = tmp_path / "CleanShot X.app"
    contents = app / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>CleanShot X</string>
<key>CFBundleIdentifier</key><string>pl.maketheweb.cleanshotx-setapp</string>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)

    assert identity.is_setapp is True
    assert identity.vendor == "maketheweb"
    assert "pl.maketheweb.cleanshotx-setapp" in identity.search_tokens.bundle_ids


def test_extracts_app_groups_from_entitlements_file(tmp_path: Path):
    app = tmp_path / "Sample App.app"
    contents = app / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>Sample App</string>
<key>CFBundleIdentifier</key><string>com.example.sample</string>
</dict></plist>
"""
    )
    (contents / "Entitlements.plist").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>com.apple.security.application-groups</key>
<array>
  <string>group.com.example.shared</string>
  <string>ABCDE12345.com.example.cache</string>
</array>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)

    assert identity.app_groups == ["ABCDE12345.com.example.cache", "group.com.example.shared"]


def test_ignores_invalid_app_group_values(tmp_path: Path):
    app = tmp_path / "Sample App.app"
    contents = app / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>Sample App</string>
<key>CFBundleIdentifier</key><string>com.example.sample</string>
</dict></plist>
"""
    )
    (contents / "Entitlements.plist").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>com.apple.security.application-groups</key>
<array>
  <string>group.com.example.shared</string>
  <string>../Library/Secrets</string>
  <string>group/com/example</string>
  <string>.</string>
  <string>..</string>
  <string>group..example</string>
</array>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)

    assert identity.app_groups == ["group.com.example.shared"]


def test_extracts_app_groups_from_codesign_dict_output(tmp_path: Path, monkeypatch):
    app = tmp_path / "Sample App.app"
    contents = app / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>Sample App</string>
<key>CFBundleIdentifier</key><string>com.example.sample</string>
</dict></plist>
"""
    )

    def fake_run(command, capture_output, check):
        assert command[:3] == ["codesign", "-d", "--entitlements"]
        return SimpleNamespace(
            stdout=(
                b"[Dict]\n"
                b"\t[Key] com.apple.security.application-groups\n"
                b"\t[Value]\n"
                b"\t\t[Array]\n"
                b"\t\t\t[String] group.com.example.shared\n"
                b"\t\t\t[String] ABCDE12345.com.example.cache\n"
            ),
            stderr=b"",
            returncode=0,
        )

    monkeypatch.setattr("macos_uninstall_inspector.identity.subprocess.run", fake_run)

    identity = IdentityExtractor().extract(app)

    assert identity.app_groups == ["ABCDE12345.com.example.cache", "group.com.example.shared"]
