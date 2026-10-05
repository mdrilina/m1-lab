"""CR-1: personas koda pārbaude (POST /submissions · personalCode).

Katrai pieņemšanas kritēriju tabulas rindai (#1–#9) viens tests.
Sagaidāmās vērtības ņemtas no tracker/CR-1.md un docs/openapi.yaml.
"""

import pytest


def _create_and_fetch(client, payload):
    response = client.post("/submissions", json=payload)
    assert response.status_code == 201, response.text
    submission_id = response.json()["id"]
    stored = client.get(f"/submissions/{submission_id}")
    assert stored.status_code == 200
    return stored.json()


def _assert_validation_error(response, issue, entered_code=None):
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert {"field": "personalCode", "issue": issue} in error["details"]
    # Precizējums: kļūdas atbildē ievadīto kodu neatkārto.
    if entered_code is not None:
        assert entered_code not in response.text
        digits = "".join(ch for ch in entered_code if ch.isdigit())
        if digits:
            assert digits not in response.text


def test_cr1_k1_eleven_digits_saved(client, valid_payload):
    """Kritērijs #1: 32000000001 -> 201, saglabāts 32000000001."""
    valid_payload["personalCode"] = "32000000001"
    stored = _create_and_fetch(client, valid_payload)
    assert stored["personalCode"] == "32000000001"


def test_cr1_k2_hyphen_normalised(client, valid_payload):
    """Kritērijs #2: 320000-00001 -> 201, saglabāts 32000000001."""
    valid_payload["personalCode"] = "320000-00001"
    stored = _create_and_fetch(client, valid_payload)
    assert stored["personalCode"] == "32000000001"


def test_cr1_k3_surrounding_spaces_stripped(client, valid_payload):
    """Kritērijs #3: " 32000000001 " -> 201 (atstarpes noņemtas)."""
    valid_payload["personalCode"] = " 32000000001 "
    stored = _create_and_fetch(client, valid_payload)
    assert stored["personalCode"] == "32000000001"


def test_cr1_k4_ten_digits_invalid_format(client, valid_payload):
    """Kritērijs #4: 3200000000 (10 cipari) -> 400 INVALID_FORMAT."""
    valid_payload["personalCode"] = "3200000000"
    response = client.post("/submissions", json=valid_payload)
    _assert_validation_error(response, "INVALID_FORMAT", "3200000000")


def test_cr1_k5_twelve_digits_invalid_format(client, valid_payload):
    """Kritērijs #5: 320000000012 (12 cipari) -> 400 INVALID_FORMAT."""
    valid_payload["personalCode"] = "320000000012"
    response = client.post("/submissions", json=valid_payload)
    _assert_validation_error(response, "INVALID_FORMAT", "320000000012")


def test_cr1_k6_letter_o_invalid_format(client, valid_payload):
    """Kritērijs #6: 32000000O01 (burts O) -> 400 INVALID_FORMAT."""
    valid_payload["personalCode"] = "32000000O01"
    response = client.post("/submissions", json=valid_payload)
    _assert_validation_error(response, "INVALID_FORMAT", "32000000O01")


def test_cr1_k7_missing_field_required(client, valid_payload):
    """Kritērijs #7: lauka nav -> 400 REQUIRED."""
    del valid_payload["personalCode"]
    response = client.post("/submissions", json=valid_payload)
    _assert_validation_error(response, "REQUIRED")


def test_cr1_k8_old_format_hyphen_saved(client, valid_payload):
    """Kritērijs #8: vecā formāta 311299-21233 -> 201, saglabāts 31129921233."""
    valid_payload["personalCode"] = "311299-21233"
    stored = _create_and_fetch(client, valid_payload)
    assert stored["personalCode"] == "31129921233"


def test_cr1_k9_misplaced_hyphen_invalid_format(client, valid_payload):
    """Kritērijs #9: 3200-0000001 (defise nepareizā vietā) -> 400 INVALID_FORMAT."""
    valid_payload["personalCode"] = "3200-0000001"
    response = client.post("/submissions", json=valid_payload)
    _assert_validation_error(response, "INVALID_FORMAT", "3200-0000001")


# Precizējumi, ko apstiprināja lietotājs (ārpus kritēriju tabulas).


def test_cr1_spaces_and_hyphen_together_saved(client, valid_payload):
    """Precizējums: " 320000-00001 " -> 201, saglabāts 32000000001."""
    valid_payload["personalCode"] = " 320000-00001 "
    stored = _create_and_fetch(client, valid_payload)
    assert stored["personalCode"] == "32000000001"


def test_cr1_personal_code_not_logged(client, valid_payload, caplog):
    """Precizējums: kodu neatkārto žurnālā; līgums: arī ne iesnieguma tekstu."""
    caplog.set_level("DEBUG")
    valid_payload["personalCode"] = "320000-00001"
    client.post("/submissions", json=valid_payload)
    valid_payload["personalCode"] = "3200000000"
    client.post("/submissions", json=valid_payload)
    for code in ("320000-00001", "32000000001", "3200000000"):
        assert code not in caplog.text
    assert valid_payload["body"] not in caplog.text


@pytest.mark.parametrize("blank", ["", "   "])
def test_cr1_blank_personal_code_required(client, valid_payload, blank):
    """Precizējums: tukša virkne vai tikai atstarpes -> 400 REQUIRED."""
    valid_payload["personalCode"] = blank
    response = client.post("/submissions", json=valid_payload)
    _assert_validation_error(response, "REQUIRED")
