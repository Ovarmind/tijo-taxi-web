import pytest

from api import main as api_module
from app.routing import RouteResult


def test_predict_uses_real_model_and_returns_complete_response(client, prediction_payload, prediction_services):
    response = client.post("/predict", json=prediction_payload)
    data = response.json()
    expected = api_module.model_service.predict(
        pickup_zone_id=43,
        dropoff_zone_id=161,
        routing_distance_m=4260.0,
        weekday_1_7=1,
        hour_0_23=14,
    )
    assert response.status_code == 200
    assert data == {
        "predicted_travel_time_min": round(expected, 2),
        "pickup_location_id": 43,
        "dropoff_location_id": 161,
        "routing_distance_m": 4260.0,
        "route_street_names": ["Broadway", "7th Avenue"],
    }


def test_predict_passes_route_and_time_features_to_model(client, prediction_payload, prediction_services, monkeypatch):
    received = []
    original_predict = api_module.model_service.predict

    def record_predict(**features):
        received.append(features)
        return original_predict(**features)

    monkeypatch.setattr(api_module.model_service, "predict", record_predict)
    payload = {**prediction_payload, "weekday_1_7": 5, "hour_0_23": 22}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert received == [{
        "pickup_zone_id": 43,
        "dropoff_zone_id": 161,
        "routing_distance_m": 4260.0,
        "weekday_1_7": 5,
        "hour_0_23": 22,
    }]


def test_predict_passes_correct_points_to_routing(client, prediction_payload, prediction_services, monkeypatch):
    received = []

    def capture_route(pickup, dropoff):
        received.append((pickup, dropoff))
        return RouteResult(distance_m=2300.0, street_names=["5th Avenue"])

    monkeypatch.setattr(api_module, "calculate_route", capture_route)
    response = client.post("/predict", json=prediction_payload)
    assert response.status_code == 200
    assert received[0][0].latitude == prediction_payload["pickup"]["latitude"]
    assert received[0][0].longitude == prediction_payload["pickup"]["longitude"]
    assert received[0][1].latitude == prediction_payload["dropoff"]["latitude"]
    assert received[0][1].longitude == prediction_payload["dropoff"]["longitude"]
    assert response.json()["routing_distance_m"] == 2300.0
    assert response.json()["route_street_names"] == ["5th Avenue"]


def test_predict_rounds_model_result_and_distance(client, prediction_payload, prediction_services, monkeypatch):
    monkeypatch.setattr(api_module.model_service, "predict", lambda **features: 15.7865)
    monkeypatch.setattr(
        api_module,
        "calculate_route",
        lambda pickup, dropoff: RouteResult(distance_m=4260.76, street_names=[]),
    )
    response = client.post("/predict", json=prediction_payload)
    assert response.status_code == 200
    assert response.json()["predicted_travel_time_min"] == 15.79
    assert response.json()["routing_distance_m"] == 4260.8
    assert response.json()["route_street_names"] == []


@pytest.mark.parametrize("weekday", [0, 8])
def test_predict_rejects_invalid_weekday(client, prediction_payload, prediction_services, weekday):
    payload = {**prediction_payload, "weekday_1_7": weekday}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("hour", [-1, 24])
def test_predict_rejects_invalid_hour(client, prediction_payload, prediction_services, hour):
    payload = {**prediction_payload, "hour_0_23": hour}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_rejects_invalid_coordinates(client, prediction_payload, prediction_services):
    payload = {
        **prediction_payload,
        "pickup": {"latitude": 100, "longitude": -73.9855},
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_rejects_missing_destination(client, prediction_payload, prediction_services):
    payload = {key: value for key, value in prediction_payload.items() if key != "dropoff"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_rejects_pickup_outside_zones(client, prediction_payload, prediction_services):
    payload = {
        **prediction_payload,
        "pickup": {"latitude": 0, "longitude": 0},
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "początkowy" in response.json()["detail"]


def test_predict_rejects_dropoff_outside_zones(client, prediction_payload, prediction_services):
    payload = {
        **prediction_payload,
        "dropoff": {"latitude": 0, "longitude": 0},
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "docelowy" in response.json()["detail"]


def test_predict_returns_503_when_osrm_is_unavailable(client, prediction_payload, prediction_services, monkeypatch):
    def failing_route(pickup, dropoff):
        raise ConnectionError("OSRM unavailable")

    monkeypatch.setattr(api_module, "calculate_route", failing_route)
    response = client.post("/predict", json=prediction_payload)
    assert response.status_code == 503
    assert "OSRM" in response.json()["detail"]


def test_predict_returns_500_when_model_fails(client, prediction_payload, prediction_services, monkeypatch):
    def failing_prediction(**features):
        raise RuntimeError("Prediction error")

    monkeypatch.setattr(api_module.model_service, "predict", failing_prediction)
    response = client.post("/predict", json=prediction_payload)
    assert response.status_code == 500
    assert "predykcji" in response.json()["detail"]
