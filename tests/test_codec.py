from ait import build_ait, build_eap, decode_to_japanese


def test_build_eap_from_structured_parameters() -> None:
    packet = build_eap(domain="security", action="xss", target=4, priority=9)

    assert packet == ">SEC:XSS #ctx4 !9"


def test_build_ait_from_structured_parameters() -> None:
    packet = build_ait(domain="security", action="xss", target=4, priority=9)

    assert packet == "s4x9"


def test_decode_ait_to_japanese_uses_static_dictionary() -> None:
    text = decode_to_japanese("s4x9")

    assert text == "コンテキスト4に対して、セキュリティ領域のXSS検証を実行します。優先度は最高です。"


def test_decode_eap_to_japanese_uses_static_dictionary() -> None:
    text = decode_to_japanese(">DAT:SUM #ctx7 !3")

    assert text == "コンテキスト7に対して、データ領域の要約を実行します。優先度は低です。"
