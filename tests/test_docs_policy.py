from pathlib import Path


def test_generic_vendor_formulas_doc_exists_and_mentions_reusable_policy():
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs" / "generic-vendor-formulas.md").read_text()
    assert "official manager first" in text
    assert "structured provenance first" in text
    assert "vendor_shared" in text


def test_readmes_mention_entitlements_and_group_containers():
    root = Path(__file__).resolve().parents[1]
    readme_en = (root / "README.md").read_text()
    readme_ja = (root / "README.ja.md").read_text()
    assert "entitlements" in readme_en.lower()
    assert "group containers" in readme_en.lower()
    assert "entitlements" in readme_ja.lower()
    assert "group containers" in readme_ja.lower()
