from macos_uninstall_inspector.runtime import receipt_matches_identity


def test_receipt_match_accepts_exact_component_sequence():
    assert receipt_matches_identity("com.tailscale.ipn.macsys", "io.tailscale.ipn.macsys") is True


def test_receipt_match_rejects_loose_suffix_false_positive():
    assert receipt_matches_identity("com.vendor.vpnconnect.helper", "com.example.connect") is False
