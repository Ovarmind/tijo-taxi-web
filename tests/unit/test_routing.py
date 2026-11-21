from types import SimpleNamespace

import pytest

from app.models import Point
from app.routing import RouteResult, calculate_route, extract_street_names

PICKUP = Point(latitude=40.758, longitude=-73.9855)
DROPOFF = Point(latitude=40.7128, longitude=-74.006)

def test_street_names_are_unique_and_keep_first_occurrence_order():
    data = {"routes": [{"legs": [{"steps": [
        {"name": "Broadway"}, {"name": "7th Avenue"},
        {"name": "Broadway"}, {"name": "West Street"},
    ]}]}]}
    result = extract_street_names(data)
    assert result == ["Broadway", "7th Avenue", "West Street"]

def test_street_names_ignore_empty_and_missing_names():
    data = {"routes": [{"legs": [{"steps": [
        {"name": ""}, {"name": None}, {}, {"name": "Broadway"},
    ]}]}]}
    result = extract_street_names(data)
    assert result == ["Broadway"]

def test_street_names_return_empty_list_when_no_routes():
    data = {"routes": []}
    result = extract_street_names(data)
    assert result == []

def test_street_names_return_empty_list_when_routes_key_is_missing():
    data = {"code": "NoRoute"}
    result = extract_street_names(data)
    assert result == []

def test_street_names_handle_legs_without_steps():
    data = {"routes": [{"legs": [{}]}]}
    result = extract_street_names(data)
    assert result == []

def test_street_names_are_collected_from_multiple_legs():
    data = {"routes": [{"legs": [
        {"steps": [{"name": "First"}]},
        {"steps": [{"name": "Second"}, {"name": "First"}]},
    ]}]}
    result = extract_street_names(data)
    assert result == ["First", "Second"]

def test_calculate_route_uses_longitude_latitude_and_returns_distance(monkeypatch):
    captured = {}

    class FakeOSRM:
        def __init__(self, base_url, timeout):
            captured["base_url"] = base_url
            captured["timeout"] = timeout

        def directions(self, locations, steps):
            captured["locations"] = locations
            captured["steps"] = steps
            return SimpleNamespace(
                distance=4260.0,
                raw={"routes": [{"legs": [{"steps": [{"name": "Broadway"}]}]}]},
            )

    monkeypatch.setattr("app.routing.OSRM", FakeOSRM)
    result = calculate_route(PICKUP, DROPOFF)
    assert isinstance(result, RouteResult)
    assert result.distance_m == 4260.0
    assert result.street_names == ["Broadway"]
    assert captured == {
        "base_url": "http://router.project-osrm.org",
        "timeout": 15,
        "locations": [[-73.9855, 40.758], [-74.006, 40.7128]],
        "steps": True,
    }

def test_calculate_route_raises_value_error_when_osrm_finds_no_route(monkeypatch):
    class FakeOSRM:
        def __init__(self, base_url, timeout):
            pass

        def directions(self, locations, steps):
            return SimpleNamespace(distance=0, raw={"routes": [], "code": "NoRoute"})

    monkeypatch.setattr("app.routing.OSRM", FakeOSRM)
    with pytest.raises(ValueError, match="No route found"):
        calculate_route(PICKUP, DROPOFF)

def test_calculate_route_propagates_osrm_error(monkeypatch):
    class FakeOSRM:
        def __init__(self, base_url, timeout):
            pass

        def directions(self, locations, steps):
            raise RuntimeError("OSRM unavailable")

    monkeypatch.setattr("app.routing.OSRM", FakeOSRM)
    with pytest.raises(RuntimeError, match="OSRM unavailable"):
        calculate_route(PICKUP, DROPOFF)
