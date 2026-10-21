def test_create_competition_returns_201_and_draft_status(client):
    response = client.post(
        "/competitions", json={"name": "Meeting de rentrée", "date": "2030-09-14"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "draft"
    assert body["venue"] is None


def test_create_competition_rejects_empty_name(client):
    response = client.post("/competitions", json={"name": "", "date": "2030-09-14"})

    assert response.status_code == 422


def test_list_competitions_filters_by_status(client, make_competition):
    make_competition("A")
    make_competition("B", status="open")

    response = client.get("/competitions", params={"status": "open"})

    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["B"]


def test_get_unknown_competition_uses_project_error_format(client):
    response = client.get("/competitions/999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Compétition 999 introuvable"},
    }


def test_competition_status_follows_allowed_transitions(client, make_competition):
    competition = make_competition()

    for status in ["open", "closed", "finished"]:
        response = client.patch(f"/competitions/{competition['id']}", json={"status": status})
        assert response.status_code == 200
        assert response.json()["status"] == status


def test_competition_rejects_invalid_transition(client, make_competition):
    competition = make_competition()

    response = client.patch(f"/competitions/{competition['id']}", json={"status": "finished"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_transition"
