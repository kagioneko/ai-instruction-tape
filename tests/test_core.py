import pytest

from ait import AitError, decode_ait, encode_eap, parse_eap


def test_encode_eap_to_ait() -> None:
    assert encode_eap(">SEC:XSS #ctx4 !9") == "s4x9"


def test_decode_ait_to_eap() -> None:
    assert decode_ait("s4x9").to_eap() == ">SEC:XSS #ctx4 !9"


def test_base36_target() -> None:
    assert encode_eap(">PRED:BRANCH #ctx10 !7") == "pab7"
    packet = decode_ait("pab7")
    assert packet.domain == "prediction"
    assert packet.target == 10
    assert packet.action == "branch"


def test_unknown_eap_domain_fails() -> None:
    with pytest.raises(AitError):
        parse_eap(">DOG:XSS #ctx4 !9")


def test_unknown_ait_code_fails() -> None:
    with pytest.raises(AitError):
        decode_ait("z4x9")

