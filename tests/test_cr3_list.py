"""CR-3: iesniegumu saraksts darbiniekam (piegādātāja testi)."""

from app import storage


def test_list_received(client):
    storage.reset()
    response = client.get("/submissions?status=RECEIVED")
    assert response.status_code == 200
    assert all(item["status"] == "RECEIVED" for item in response.json())


def test_list_by_topic(client):
    storage.reset()
    response = client.get("/submissions?topic=ROADS")
    assert response.status_code == 200
    assert all(item["topic"] == "ROADS" for item in response.json())


def test_list_all(client):
    storage.reset()
    response = client.get("/submissions")
    assert response.status_code == 200
    assert len(response.json()) == 3


# Regresija: statusa filtrs pieņem tikai līguma vērtības un neveido SQL no ievades.
INJECTION = "RECEIVED' OR '1'='1"


def test_regression_unknown_status_returns_400(client):
    storage.reset()
    response = client.get("/submissions", params={"status": "DONE"})
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"] == [{"field": "status", "issue": "INVALID_FORMAT"}]


def test_regression_status_sql_injection_rejected(client):
    storage.reset()
    response = client.get("/submissions", params={"status": INJECTION})
    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["field"] == "status"
    assert INJECTION not in response.text


def test_regression_storage_status_filter_is_parameterized():
    storage.reset()
    assert storage.list_submissions(status=INJECTION) == []
    assert storage.list_submissions(topic="ROADS' OR '1'='1") == []
    assert [r["status"] for r in storage.list_submissions(status="RECEIVED")] == [
        "RECEIVED"
    ]
