from datetime import date, timedelta


def test_register_assigns_increasing_bibs(
    client, make_competition, make_event, make_athlete, make_registration
):
    competition = make_competition(status="open")
    sprint = make_event(competition["id"], "100 m")
    jump = make_event(competition["id"], "Saut en longueur", unit="distance_m")
    first = make_athlete("Bernard")
    second = make_athlete("Roux")

    bibs = [
        make_registration(sprint["id"], first["id"])["bib"],
        make_registration(jump["id"], first["id"])["bib"],
        make_registration(sprint["id"], second["id"])["bib"],
    ]

    assert bibs == [1, 2, 3]


def test_register_refused_when_competition_not_open(
    client, make_competition, make_event, make_athlete
):
    competition = make_competition(status="draft")
    event = make_event(competition["id"])
    athlete = make_athlete()

    response = client.post(
        f"/events/{event['id']}/registrations", json={"athlete_id": athlete["id"]}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "registration_closed"


def test_register_refused_with_expired_certificate(
    client, make_competition, make_event, make_athlete
):
    competition = make_competition(status="open")
    event = make_event(competition["id"])
    athlete = make_athlete(certificate_valid_until=date.today() - timedelta(days=1))

    response = client.post(
        f"/events/{event['id']}/registrations", json={"athlete_id": athlete["id"]}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "medical_certificate_invalid"
