from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "ridge_travel_time_2025_zones.joblib"


class ModelService:
    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        bundle = joblib.load(model_path)

        self.model = bundle["model"]
        self.metadata = bundle.get("metadata", {})
        self.feature_columns = self.metadata.get(
            "feature_columns",
            [
                "PULocationID",
                "DOLocationID",
                "weekday_1_7",
                "routing_distance_m",
                "hour_0_23",
            ],
        )

    def predict(
        self,
        *,
        pickup_zone_id: int,
        dropoff_zone_id: int,
        routing_distance_m: float,
        weekday_1_7: int,
        hour_0_23: int,
    ) -> float:
        input_data = pd.DataFrame(
            [
                {
                    "PULocationID": pickup_zone_id,
                    "DOLocationID": dropoff_zone_id,
                    "weekday_1_7": weekday_1_7,
                    "routing_distance_m": routing_distance_m,
                    "hour_0_23": hour_0_23,
                }
            ]
        )

        input_data = input_data[self.feature_columns]
        prediction = self.model.predict(input_data)[0]

        return float(prediction)
