from pathlib import Path

from macos_uninstall_inspector.distribution import DistributionResolver
from macos_uninstall_inspector.identity import IdentityExtractor


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
{extra_plist}
</dict></plist>
"""
    )
    return app


def test_resolve_plain_app_when_no_manager_matches(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    identity = IdentityExtractor().extract(app)

    result = DistributionResolver().resolve(identity)

    assert result.kind == "plain_app"
    assert result.manager_hint is None
    assert result.resolver_priority[0] == "bundle_embedded"


def test_resolve_mas_when_receipt_present(tmp_path: Path):
    app = make_app(tmp_path, "CotEditor", "com.coteditor.CotEditor")
    receipt = app / "Contents" / "_MASReceipt"
    receipt.mkdir()
    (receipt / "receipt").write_text("stub")
    identity = IdentityExtractor().extract(app)

    result = DistributionResolver().resolve(identity)

    assert result.kind == "mas"
    assert result.resolver_priority[0] == "mas_receipt"


def test_resolve_setapp_from_bundle_suffix(tmp_path: Path):
    app = make_app(tmp_path, "CleanShot X", "pl.maketheweb.cleanshotx-setapp")
    identity = IdentityExtractor().extract(app)

    result = DistributionResolver().resolve(identity)

    assert result.kind == "setapp"
    assert "Setapp" in result.manager_hint


def test_resolve_adobe_as_vendor_suite(tmp_path: Path):
    app = make_app(tmp_path, "Creative Cloud", "com.adobe.accmac")
    identity = IdentityExtractor().extract(app)

    result = DistributionResolver().resolve(identity)

    assert result.kind == "vendor_suite"
    assert "Cleaner Tool" in result.manager_hint


def test_resolve_homebrew_from_runtime_context(tmp_path: Path):
    app = make_app(tmp_path, "Claude", "com.anthropic.claudefordesktop")
    identity = IdentityExtractor().extract(app)
    context = {"homebrew_casks": {"com.anthropic.claudefordesktop": "claude"}}

    result = DistributionResolver().resolve(identity, context=context)

    assert result.kind == "homebrew_cask"
    assert result.manager_hint == "brew uninstall --cask claude"


def test_resolve_pkg_from_runtime_context(tmp_path: Path):
    app = make_app(tmp_path, "Jump Desktop Connect", "com.p5sys.jump.connect")
    identity = IdentityExtractor().extract(app)
    context = {"pkg_receipts": {"com.p5sys.jump.connect": ["com.p5sys.jump.connect"]}}

    result = DistributionResolver().resolve(identity, context=context)

    assert result.kind == "pkg"
    assert result.manager_hint == "pkgutil receipts: com.p5sys.jump.connect"
