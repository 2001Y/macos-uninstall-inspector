from pathlib import Path

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
