import pytest
from fastapi.testclient import TestClient

from api import main as api_module
from app.routing import RouteResult


@pytest.fixture
def client():
    return TestClient(api_module.app)


@pytest.fixture
def prediction_payload():
    return {
        "pickup": {"latitude": 40.758, "longitude": -73.9855},
        "dropoff": {"latitude": 40.7128, "longitude": -74.006},
        "weekday_1_7": 1,
        "hour_0_23": 14,
    }


@pytest.fixture
def prediction_services(monkeypatch):
    class ZoneMapper:
        def get_zone_id(self, lon, lat):
            if abs(lon + 73.9855) < 0.000001 and abs(lat - 40.758) < 0.000001:
                return 43
            if abs(lon + 74.006) < 0.000001 and abs(lat - 40.7128) < 0.000001:
                return 161
            return None

    def route(pickup, dropoff):
        return RouteResult(distance_m=4260.0, street_names=["Broadway", "7th Avenue"])

    monkeypatch.setattr(api_module, "zone_mapper", ZoneMapper())
    monkeypatch.setattr(api_module, "calculate_route", route)
