from pathlib import Path


def test_generic_vendor_formulas_doc_exists_and_mentions_reusable_policy():
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs" / "generic-vendor-formulas.md").read_text()
    assert "official manager first" in text
    assert "structured provenance first" in text
    assert "vendor_shared" in text
