from pathlib import Path


def test_readmes_mention_system_integrations():
    root = Path(__file__).resolve().parents[1]
    readme_en = (root / "README.md").read_text()
    readme_ja = (root / "README.ja.md").read_text()
    assert "LaunchAgents / LaunchDaemons / PrivilegedHelperTools" in readme_en
    assert "LaunchAgents` / `LaunchDaemons` / `PrivilegedHelperTools" in readme_ja
