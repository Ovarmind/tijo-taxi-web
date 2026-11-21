from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.schemas import GeoPredictionRequest, PredictionResponse
from api.services.model_service import ModelService
from app.routing import calculate_route
from app.zone_mapper import NYCZoneMapper

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(
    title="NYC Taxi Travel Time Prediction — TiJO",
    description="Predykcja czasu przejazdu taksówką na podstawie trasy i modelu Ridge.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")

# Wczytujemy wytrenowany model i nieduży plik stref tylko raz, przy starcie.
model_service = ModelService()
zone_mapper = NYCZoneMapper()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: GeoPredictionRequest) -> PredictionResponse:
    pickup_zone = zone_mapper.get_zone_id(
        lon=request.pickup.longitude, lat=request.pickup.latitude
    )
    dropoff_zone = zone_mapper.get_zone_id(
        lon=request.dropoff.longitude, lat=request.dropoff.latitude
    )

    if pickup_zone is None:
        raise HTTPException(status_code=422, detail="Punkt początkowy jest poza strefami NYC Taxi.")
    if dropoff_zone is None:
        raise HTTPException(status_code=422, detail="Punkt docelowy jest poza strefami NYC Taxi.")

    try:
        route = calculate_route(request.pickup, request.dropoff)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Nie udało się pobrać trasy z serwisu OSRM. Sprawdź internet i spróbuj ponownie.",
        ) from exc

    try:
        predicted_minutes = model_service.predict(
            pickup_zone_id=int(pickup_zone),
            dropoff_zone_id=int(dropoff_zone),
            routing_distance_m=route.distance_m,
            weekday_1_7=request.weekday_1_7,
            hour_0_23=request.hour_0_23,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Wystąpił błąd podczas obliczania predykcji.") from exc

    return PredictionResponse(
        predicted_travel_time_min=round(predicted_minutes, 2),
        pickup_location_id=int(pickup_zone),
        dropoff_location_id=int(dropoff_zone),
        routing_distance_m=round(route.distance_m, 1),
        route_street_names=route.street_names,
    )
