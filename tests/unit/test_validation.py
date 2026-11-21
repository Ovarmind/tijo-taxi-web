import pytest
from pydantic import ValidationError

from api.schemas import GeoPredictionRequest, PredictionResponse
from app.models import Point

VALID_REQUEST = {
    "pickup": {"latitude": 40.758, "longitude": -73.9855},
    "dropoff": {"latitude": 40.7128, "longitude": -74.006},
    "weekday_1_7": 1,
    "hour_0_23": 14,
}

def test_point_accepts_valid_new_york_coordinates():
    latitude, longitude = 40.758, -73.9855
    point = Point(latitude=latitude, longitude=longitude)
    assert point.latitude == latitude
    assert point.longitude == longitude

def test_point_accepts_boundary_coordinates():
    latitude, longitude = 90, -180
    point = Point(latitude=latitude, longitude=longitude)
    assert point.latitude == 90
    assert point.longitude == -180

@pytest.mark.parametrize("latitude", [-90.1, 90.1])
def test_point_rejects_out_of_range_latitude(latitude):
    coordinates = {"latitude": latitude, "longitude": -73.9855}
    with pytest.raises(ValidationError):
        Point(**coordinates)

@pytest.mark.parametrize("longitude", [-180.1, 180.1])
def test_point_rejects_out_of_range_longitude(longitude):
    coordinates = {"latitude": 40.758, "longitude": longitude}
    with pytest.raises(ValidationError):
        Point(**coordinates)

def test_request_parses_pickup_and_dropoff_into_points():
    data = VALID_REQUEST.copy()
    request = GeoPredictionRequest.model_validate(data)
    assert isinstance(request.pickup, Point)
    assert isinstance(request.dropoff, Point)
    assert request.pickup.latitude == 40.758
    assert request.dropoff.longitude == -74.006

@pytest.mark.parametrize("weekday", [0, 8])
def test_request_rejects_day_outside_1_to_7(weekday):
    data = {**VALID_REQUEST, "weekday_1_7": weekday}
    with pytest.raises(ValidationError):
        GeoPredictionRequest.model_validate(data)

@pytest.mark.parametrize("hour", [-1, 24])
def test_request_rejects_hour_outside_0_to_23(hour):
    data = {**VALID_REQUEST, "hour_0_23": hour}
    with pytest.raises(ValidationError):
        GeoPredictionRequest.model_validate(data)

def test_request_rejects_missing_destination():
    data = {key: value for key, value in VALID_REQUEST.items() if key != "dropoff"}
    with pytest.raises(ValidationError):
        GeoPredictionRequest.model_validate(data)

def test_prediction_response_keeps_expected_fields():
    data = {
        "predicted_travel_time_min": 15.78,
        "pickup_location_id": 43,
        "dropoff_location_id": 161,
        "routing_distance_m": 4260.0,
        "route_street_names": ["Broadway", "7th Avenue"],
    }
    response = PredictionResponse(**data)
    assert response.model_dump() == data
