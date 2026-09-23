from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.loader import load_contractors
from backend.main import create_app
from backend.models import RecommendRequest
from backend.service import recommend

QUERY = dict(city="Астана", event_date="2026-10-15", event_type="свадьба",
             category="Ведущий", budget=900000, duration=6, language="казахский")


@pytest.fixture
def client():
    with TestClient(create_app()) as client:
        yield client


def test_actual_csv_and_repeatability(client):
    assert client.get("/health").json() == {"status": "ok", "profiles": 66}
    response = client.post("/recommend", json=QUERY)
    assert response.status_code == 200
    data = response.json()
    assert data == client.post("/recommend", json=QUERY).json()
    assert data["status"] == "matches_found"
    assert 0 < data["count"] <= 3
    assert "HK-80581" in [r["id"] for r in data["results"]]
    profiles = {c.id: c for c in load_contractors()}
    for result in data["results"]:
        c = profiles[result["id"]]
        assert date(2026, 10, 15) not in c.busy_dates
        assert c.price_from_kzt <= QUERY["budget"]
        assert "казахский" in c.languages
        assert "свадьба" in c.event_formats
        assert c.max_hours is None or c.max_hours >= 6


@pytest.mark.parametrize("change,reason", [
    ({"busy_dates": frozenset({date(2026, 10, 15)})}, "busy_date"),
    ({"price_from_kzt": 900001}, "over_budget"),
    ({"event_formats": ("конференция",)}, "event_type"),
    ({"languages": ("русский",)}, "language"),
    ({"max_hours": 5}, "duration"),
])
def test_each_hard_filter(change, reason):
    c = next(c for c in load_contractors() if c.id == "HK-80581")
    response = recommend((c.model_copy(update=change),), RecommendRequest(**QUERY))
    assert response.status == "no_matches"
    assert response.exclusion_counts == {reason: 1}


def test_date_changes_availability(client):
    data = client.post("/recommend", json={**QUERY, "event_date": "2026-10-16"}).json()
    assert "HK-80581" not in [r["id"] for r in data["results"]]
    assert data["exclusion_counts"]["busy_date"] > 0


def test_three_outcomes_and_normalization(client):
    assert client.post("/recommend", json={**QUERY, "category": "нет такой категории"}).json()["status"] == "no_category_in_city"
    empty = client.post("/recommend", json={**QUERY, "budget": 0}).json()
    assert empty["status"] == "no_matches"
    assert empty["count"] == 0 and empty["message"]
    assert client.post("/recommend", json={**QUERY, "city": " АСТАНА ", "category": " ведущий "}).json()["count"] > 0


def test_null_hours_optional_filters_and_multiple_categories():
    c = load_contractors()[0].model_copy(update={
        "categories": ("Флорист", "Декоратор"), "max_hours": None,
        "busy_dates": frozenset(),
    })
    q = RecommendRequest(city=c.city, category="Декоратор", budget=c.price_from_kzt,
                         event_date="2026-09-23", event_type=c.event_formats[0], duration=100)
    response = recommend((c,), q)
    assert response.count == 1
    assert response.results[0].category == "Декоратор"
    assert "Меньше трёх" in response.message


@pytest.mark.parametrize("change", [
    {"event_date": "2027-01-01"}, {"event_date": "2026-09-22"},
    {"event_date": "bad-date"}, {"budget": -1}, {"budget": True},
    {"duration": 0}, {"city": " "}, {"language": " "}, {"typo": 1},
])
def test_invalid_requests(client, change):
    assert client.post("/recommend", json={**QUERY, **change}).status_code == 422


def test_calendar_boundaries_and_optional_fields(client):
    for day in ("2026-09-23", "2026-12-31"):
        q = {k: v for k, v in QUERY.items() if k not in ("duration", "language")}
        assert client.post("/recommend", json={**q, "event_date": day}).status_code == 200


def test_loader_rejects_bad_schema(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("id,anon_name\nx,name\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        load_contractors(source)
