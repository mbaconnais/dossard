from datetime import date
from pathlib import Path


def test_create_athlete_returns_201_with_category(client):
    birth_date = date(date.today().year - 30, 3, 2)

    response = client.post(
        "/athletes",
        json={
            "first_name": "Inès",
            "last_name": "Morel",
            "birth_date": birth_date.isoformat(),
            "sex": "F",
            "license_number": "DOS-000042",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "SENIOR"
    assert body["club"] is None


def test_create_athlete_rejects_duplicate_license(client, make_athlete):
    athlete = make_athlete()

    response = client.post(
        "/athletes",
        json={
            "first_name": "Hugo",
            "last_name": "Lemaire",
            "birth_date": "1995-05-20",
            "sex": "M",
            "license_number": athlete["license_number"],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_list_athletes_filters_by_club(client, make_athlete):
    make_athlete("Durand", club="AC Rivebelle")
    make_athlete("Petit", club="Stade Nordval")

    response = client.get("/athletes", params={"club": "AC Rivebelle"})

    assert response.status_code == 200
    assert [a["last_name"] for a in response.json()] == ["Durand"]


def test_list_athletes_paginates_with_defaults(client, make_athlete):
    for i in range(51):
        make_athlete(f"Nom{i:02d}")

    response = client.get("/athletes")

    assert response.status_code == 200
    assert len(response.json()) == 50


def test_list_athletes_limit_and_offset(client, make_athlete):
    for name in ("Arnaud", "Blanc", "Carré", "Dupont"):
        make_athlete(name)

    response = client.get("/athletes", params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    assert [a["last_name"] for a in response.json()] == ["Blanc", "Carré"]


def test_list_athletes_offset_beyond_total_returns_empty_list(client, make_athlete):
    make_athlete("Arnaud")

    response = client.get("/athletes", params={"offset": 10})

    assert response.status_code == 200
    assert response.json() == []


def test_list_athletes_accepts_bounds(client, make_athlete):
    make_athlete("Arnaud")

    assert client.get("/athletes", params={"limit": 1, "offset": 0}).status_code == 200
    assert client.get("/athletes", params={"limit": 100}).status_code == 200


def test_list_athletes_paginates_after_club_filter(client, make_athlete):
    make_athlete("Arnaud", club="AC Rivebelle")
    make_athlete("Blanc", club="Stade Nordval")
    make_athlete("Carré", club="AC Rivebelle")
    make_athlete("Dupont", club="AC Rivebelle")

    response = client.get("/athletes", params={"club": "AC Rivebelle", "limit": 1, "offset": 1})

    assert response.status_code == 200
    assert [a["last_name"] for a in response.json()] == ["Carré"]


def test_list_athletes_out_of_range_params_return_422(client):
    for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "abc"}):
        response = client.get("/athletes", params=params)
        assert response.status_code == 422, params


def test_get_athlete_returns_200(client, make_athlete):
    athlete = make_athlete("Durand", club="AC Rivebelle")

    response = client.get(f"/athletes/{athlete['id']}")

    assert response.status_code == 200
    assert response.json() == athlete


def test_get_athlete_unknown_returns_404(client):
    response = client.get("/athletes/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_athlete_invalid_id_returns_422(client):
    response = client.get("/athletes/abc")

    assert response.status_code == 422


CSV_EXEMPLE = Path(__file__).parents[1] / "scripts" / "legacy" / "licencies_exemple.csv"
CSV_HEADERS = {"Content-Type": "text/csv"}


def test_import_athletes_creates_skips_and_reports_errors(client):
    response = client.post(
        "/athletes/import", content=CSV_EXEMPLE.read_bytes(), headers=CSV_HEADERS
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 17
    assert body["skipped"] == 1
    assert [e["line"] for e in body["errors"]] == [15, 16]
    assert len(client.get("/athletes").json()) == 17


def test_import_athletes_twice_skips_everything_valid(client):
    content = CSV_EXEMPLE.read_bytes()
    first = client.post("/athletes/import", content=content, headers=CSV_HEADERS).json()

    response = client.post("/athletes/import", content=content, headers=CSV_HEADERS)

    body = response.json()
    assert (body["created"], body["skipped"]) == (0, 18)
    assert body["errors"] == first["errors"]
    assert [e["line"] for e in body["errors"]] == [15, 16]


def test_import_athletes_missing_columns_returns_400(client):
    response = client.post("/athletes/import", content=b"nom;prenom\nA;B\n", headers=CSV_HEADERS)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_csv"
