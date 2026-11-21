from pydantic import BaseModel, Field

from app.models import Point


class GeoPredictionRequest(BaseModel):
    pickup: Point
    dropoff: Point
    weekday_1_7: int = Field(..., ge=1, le=7)
    hour_0_23: int = Field(..., ge=0, le=23)


class PredictionResponse(BaseModel):
    predicted_travel_time_min: float
    pickup_location_id: int
    dropoff_location_id: int
    routing_distance_m: float
    route_street_names: list[str]
