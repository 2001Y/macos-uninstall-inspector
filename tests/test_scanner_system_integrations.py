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


def test_scanner_matches_launchd_programs_by_executable_name(tmp_path: Path):
    app = make_app(tmp_path, "Launcher Sample", "com.example.launchersample")
    info = app / "Contents" / "Info.plist"
    info.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>Launcher Sample</string>
<key>CFBundleIdentifier</key><string>com.example.launchersample</string>
<key>CFBundleExecutable</key><string>LauncherSample</string>
</dict></plist>
"""
    )
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    agent = system_root / "LaunchAgents" / "vendor.launch.agent.plist"
    agent.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>vendor.launch.agent</string>
<key>ProgramArguments</key><array><string>/Library/Application Support/Vendor/bin/LauncherSample</string></array>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(agent) in by_path
    assert "launchd_program_match" in by_path[str(agent)]["evidence"]
    assert "launchd_app_name_match" not in by_path[str(agent)]["evidence"]


def test_scanner_matches_privileged_helper_tools_by_embedded_helper_id(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    info = app / "Contents" / "Info.plist"
    info.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>Sample</string>
<key>CFBundleIdentifier</key><string>com.example.sample</string>
<key>SMPrivilegedExecutables</key><dict>
<key>com.vendor.helperd</key><string>identifier shared by helper</string>
</dict>
</dict></plist>
"""
    )
    system_root = tmp_path / "Library"
    (system_root / "PrivilegedHelperTools").mkdir(parents=True)
    helper = system_root / "PrivilegedHelperTools" / "com.vendor.helperd"
    helper.write_text("binary stub")

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(helper) in by_path
    assert "embedded_helper_id_exact" in by_path[str(helper)]["evidence"]


def test_scanner_ignores_short_name_substring_false_positives_in_launchd(tmp_path: Path):
    app = make_app(tmp_path, "AI", "com.example.ai")
    info = app / "Contents" / "Info.plist"
    info.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>AI</string>
<key>CFBundleIdentifier</key><string>com.example.ai</string>
<key>CFBundleExecutable</key><string>AI</string>
</dict></plist>
"""
    )
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    unrelated = system_root / "LaunchAgents" / "org.random.mailsync.plist"
    unrelated.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>org.random.mailsync</string>
<key>ProgramArguments</key><array><string>/usr/bin/mail</string></array>
</dict></plist>
"""
    )
    unrelated_exact = system_root / "LaunchAgents" / "org.random.ai-runner.plist"
    unrelated_exact.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>org.random.ai-runner</string>
<key>ProgramArguments</key><array><string>/usr/bin/ai</string></array>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(unrelated) not in by_path
    assert str(unrelated_exact) not in by_path


def test_scanner_ignores_bundle_id_prefix_false_positives_in_launchd(tmp_path: Path):
    app = make_app(tmp_path, "App", "com.example.app")
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    unrelated = system_root / "LaunchAgents" / "com.example.application.agent.plist"
    unrelated.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>com.example.application.agent</string>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(unrelated) not in by_path


def test_scanner_matches_compact_launchd_names_for_spaced_app_names(tmp_path: Path):
    app = make_app(tmp_path, "My App", "com.example.myapp")
    info = app / "Contents" / "Info.plist"
    info.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>My App</string>
<key>CFBundleIdentifier</key><string>com.example.myapp</string>
<key>CFBundleExecutable</key><string>MyApp</string>
</dict></plist>
"""
    )
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    compact = system_root / "LaunchAgents" / "com.vendor.myappagent.plist"
    compact.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>com.vendor.myappagent</string>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(compact) in by_path
    assert "launchd_program_match" in by_path[str(compact)]["evidence"]


def test_scanner_matches_compact_launchd_names_for_compact_app_names(tmp_path: Path):
    app = make_app(tmp_path, "MyApp", "com.example.myapp")
    info = app / "Contents" / "Info.plist"
    info.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>MyApp</string>
<key>CFBundleIdentifier</key><string>com.example.myapp</string>
<key>CFBundleExecutable</key><string>MyApp</string>
</dict></plist>
"""
    )
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    compact = system_root / "LaunchAgents" / "com.vendor.myappagent.plist"
    compact.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>com.vendor.myappagent</string>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(compact) in by_path
    assert "launchd_program_match" in by_path[str(compact)]["evidence"]


def test_scanner_ignores_single_word_compact_false_positives_in_launchd(tmp_path: Path):
    app = make_app(tmp_path, "Notes", "com.example.notes")
    info = app / "Contents" / "Info.plist"
    info.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>Notes</string>
<key>CFBundleIdentifier</key><string>com.example.notes</string>
<key>CFBundleExecutable</key><string>Notes</string>
</dict></plist>
"""
    )
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    unrelated = system_root / "LaunchAgents" / "com.apple.keynotesync.plist"
    unrelated.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>com.apple.keynotesync</string>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(unrelated) not in by_path


def test_scanner_ignores_compact_substring_false_positives_for_spaced_names(tmp_path: Path):
    app = make_app(tmp_path, "Note S", "com.example.note-s")
    info = app / "Contents" / "Info.plist"
    info.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>Note S</string>
<key>CFBundleIdentifier</key><string>com.example.note-s</string>
<key>CFBundleExecutable</key><string>NoteS</string>
</dict></plist>
"""
    )
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    unrelated = system_root / "LaunchAgents" / "com.apple.keynotesync.plist"
    unrelated.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>Label</key><string>com.apple.keynotesync</string>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(unrelated) not in by_path


def test_scanner_ignores_hyphenated_executable_false_positives_in_launchd(tmp_path: Path):
    app = make_app(tmp_path, "MyApp", "com.example.myapp")
    info = app / "Contents" / "Info.plist"
    info.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>CFBundleName</key><string>MyApp</string>
<key>CFBundleIdentifier</key><string>com.example.myapp</string>
<key>CFBundleExecutable</key><string>MyApp</string>
</dict></plist>
"""
    )
    system_root = tmp_path / "Library"
    (system_root / "LaunchAgents").mkdir(parents=True)
    unrelated = system_root / "LaunchAgents" / "org.vendor.helper.plist"
    unrelated.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> 
<plist version=\"1.0\"><dict>
<key>ProgramArguments</key><array><string>/Library/PrivilegedHelperTools/myapp-helper</string></array>
</dict></plist>
"""
    )

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=system_root).scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(unrelated) not in by_path


def test_scanner_marks_embedded_login_items_as_system_integrated(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    login_item = app / "Contents" / "Library" / "LoginItems" / "SampleLauncher.app"
    login_item.mkdir(parents=True)

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=tmp_path / "Library").scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(login_item) in by_path
    assert "login_item_embedded" in by_path[str(login_item)]["evidence"]


def test_scanner_ignores_non_bundle_login_items(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    stray_file = app / "Contents" / "Library" / "LoginItems" / "README.txt"
    stray_file.parent.mkdir(parents=True)
    stray_file.write_text("not a login item bundle")

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=tmp_path / "Library").scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(stray_file) not in by_path


def test_scanner_ignores_login_item_named_app_that_is_not_directory(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    fake_bundle = app / "Contents" / "Library" / "LoginItems" / "Fake.app"
    fake_bundle.parent.mkdir(parents=True)
    fake_bundle.write_text("not actually an app bundle")

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=tmp_path / "Library").scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(fake_bundle) not in by_path


def test_scanner_marks_embedded_system_extensions_as_system_integrated(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    system_extension = app / "Contents" / "Library" / "SystemExtensions" / "com.example.sample.network-extension.systemextension"
    system_extension.mkdir(parents=True)

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=tmp_path / "Library").scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(system_extension) in by_path
    assert "system_extension_embedded" in by_path[str(system_extension)]["evidence"]


def test_scanner_ignores_non_bundle_system_extensions(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    stray_dir = app / "Contents" / "Library" / "SystemExtensions" / "tmp"
    stray_dir.mkdir(parents=True)

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=tmp_path / "Library").scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(stray_dir) not in by_path


def test_scanner_ignores_system_extension_named_bundle_that_is_not_directory(tmp_path: Path):
    app = make_app(tmp_path, "Sample", "com.example.sample")
    fake_bundle = app / "Contents" / "Library" / "SystemExtensions" / "Fake.systemextension"
    fake_bundle.parent.mkdir(parents=True)
    fake_bundle.write_text("not actually a system extension bundle")

    identity = IdentityExtractor().extract(app)
    findings = ConventionalScanner(home=tmp_path / "home", system_root=tmp_path / "Library").scan(identity)
    by_path = {item["path"]: item for item in findings}

    assert str(fake_bundle) not in by_path
