import polars as pl
from shapely.geometry import box

from api import main as api_module
from app.routing import RouteResult
from app.zone_mapper import NYCZoneMapper


def prepare_test_zones(tmp_path, monkeypatch):
    zones_path = tmp_path / "zones.parquet"
    pl.DataFrame({
        "LocationID": [43, 161],
        "geometry": [
            box(-73.99, 40.75, -73.98, 40.76).wkt,
            box(-74.01, 40.71, -74.00, 40.72).wkt,
        ],
    }).write_parquet(zones_path)
    monkeypatch.setattr(api_module, "zone_mapper", NYCZoneMapper(str(zones_path)))
    monkeypatch.setattr(
        api_module,
        "calculate_route",
        lambda pickup, dropoff: RouteResult(distance_m=4260.0, street_names=["Broadway"]),
    )


def test_predict_integrates_parquet_zone_mapping_with_real_model(client, prediction_payload, tmp_path, monkeypatch):
    prepare_test_zones(tmp_path, monkeypatch)
    response = client.post("/predict", json=prediction_payload)
    assert response.status_code == 200
    assert response.json()["pickup_location_id"] == 43
    assert response.json()["dropoff_location_id"] == 161
    assert isinstance(response.json()["predicted_travel_time_min"], float)


def test_predict_rejects_coordinates_outside_loaded_polygons(client, prediction_payload, tmp_path, monkeypatch):
    prepare_test_zones(tmp_path, monkeypatch)
    payload = {
        **prediction_payload,
        "dropoff": {"latitude": 40.73, "longitude": -74.006},
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "docelowy" in response.json()["detail"]


def test_predict_rejects_point_on_polygon_boundary(client, prediction_payload, tmp_path, monkeypatch):
    prepare_test_zones(tmp_path, monkeypatch)
    payload = {
        **prediction_payload,
        "pickup": {"latitude": 40.75, "longitude": -73.9855},
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "początkowy" in response.json()["detail"]
