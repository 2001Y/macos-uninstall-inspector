from pathlib import Path

from macos_uninstall_inspector.identity import IdentityExtractor
from macos_uninstall_inspector.runtime import RuntimeContextCollector


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


def test_runtime_context_collector_supports_homebrew_target_rename(tmp_path: Path):
    app = make_app(tmp_path, "Renamed", "com.example.renamed")
    app = app.rename(tmp_path / "Renamed.app")
    identity = IdentityExtractor().extract(app)

    def fake_run(command: list[str]) -> str:
        if command[:3] == ["brew", "list", "--cask"]:
            return "renamed-cask\n"
        if command[:4] == ["brew", "info", "--cask", "--json=v2"]:
            return '{"casks":[{"token":"renamed-cask","full_token":"renamed-cask","artifacts":[{"app":["Original.app", {"target":"Renamed.app"}]}]}]}'
        if command[:2] == ["pkgutil", "--pkgs"]:
            return ""
        return ""

    context = RuntimeContextCollector(command_runner=fake_run).collect(identity)

    assert context["homebrew_casks"]["com.example.renamed"] == "renamed-cask"
