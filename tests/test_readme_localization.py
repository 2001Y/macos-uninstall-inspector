from pathlib import Path


def test_bilingual_readmes_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "README.md").exists()
    assert (root / "README.ja.md").exists()


def test_bilingual_readmes_reference_generic_vendor_formulas():
    root = Path(__file__).resolve().parents[1]
    readme_en = (root / "README.md").read_text()
    readme_ja = (root / "README.ja.md").read_text()
    assert "generic-vendor-formulas" in readme_en
    assert "generic-vendor-formulas" in readme_ja


def test_readmes_link_to_each_other():
    root = Path(__file__).resolve().parents[1]
    readme_en = (root / "README.md").read_text()
    readme_ja = (root / "README.ja.md").read_text()
    assert "README.ja.md" in readme_en
    assert "README.md" in readme_ja
