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


def test_competition_stats_of_empty_competition_are_zero(client, make_competition):
    competition = make_competition()

    response = client.get(f"/competitions/{competition['id']}/stats")

    assert response.status_code == 200
    assert response.json() == {"events": 0, "confirmed_registrations": 0, "results": 0}


def test_competition_stats_count_only_confirmed_registrations_and_their_results(
    client, make_competition, make_event, make_athlete, make_registration
):
    competition = make_competition(status="open")
    other = make_competition("Autre meeting", status="open")
    sprint = make_event(competition["id"])
    jump = make_event(competition["id"], name="Longueur", unit="distance_m")
    other_event = make_event(other["id"])
    with_result = make_registration(sprint["id"], make_athlete("Durand")["id"])
    make_registration(jump["id"], make_athlete("Petit")["id"])
    make_registration(jump["id"], make_athlete("Roux")["id"], confirm=False)
    cancelled = make_registration(sprint["id"], make_athlete("Moreau")["id"])
    make_registration(other_event["id"], make_athlete("Blanc")["id"])
    client.patch(f"/competitions/{competition['id']}", json={"status": "closed"})
    response = client.put(f"/registrations/{with_result['id']}/result", json={"performance": 11.2})
    assert response.status_code == 200
    response = client.put(f"/registrations/{cancelled['id']}/result", json={"performance": 11.9})
    assert response.status_code == 200
    response = client.patch(f"/registrations/{cancelled['id']}", json={"status": "cancelled"})
    assert response.status_code == 200

    response = client.get(f"/competitions/{competition['id']}/stats")

    assert response.status_code == 200
    assert response.json() == {"events": 2, "confirmed_registrations": 2, "results": 1}


def test_competition_stats_of_unknown_competition_returns_404(client):
    response = client.get("/competitions/999/stats")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Compétition 999 introuvable"},
    }


def test_competition_stats_rejects_non_integer_id(client):
    response = client.get("/competitions/abc/stats")

    assert response.status_code == 422
