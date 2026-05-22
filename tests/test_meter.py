from ait import compare_forms, default_dictionary, estimate_tokens


def test_ait_is_shorter_than_eap_in_heuristic_meter() -> None:
    results = compare_forms(
        natural="過去ログ4番のXSSを超ガチで見て",
        eap=">SEC:XSS #ctx4 !9",
    )
    by_label = {result.label: result for result in results}

    assert by_label["ait"].text == "s4x9"
    assert by_label["ait"].chars < by_label["eap"].chars
    assert by_label["ait"].heuristic_tokens < by_label["eap"].heuristic_tokens


def test_dictionary_check_is_clean() -> None:
    assert default_dictionary().check() == []


def test_estimate_tokens_handles_short_ascii() -> None:
    assert estimate_tokens("s4x9") == 1

