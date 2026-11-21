import numpy as np
import pytest

from api.services import model_service as service_module
from api.services.model_service import ModelService

class FakeModel:
    def __init__(self, result=15.78):
        self.result = result
        self.received_features = None

    def predict(self, features):
        self.received_features = features.copy()
        return [self.result]

def create_service(tmp_path, monkeypatch, *, metadata=None, prediction=15.78):
    model_path = tmp_path / "fake_model.joblib"
    model_path.write_bytes(b"fake model - file existence check only")
    fake_model = FakeModel(prediction)
    bundle = {"model": fake_model}
    if metadata is not None:
        bundle["metadata"] = metadata
    monkeypatch.setattr(service_module.joblib, "load", lambda path: bundle)
    return ModelService(model_path=model_path), fake_model

def sample_prediction(service):
    return service.predict(
        pickup_zone_id=43,
        dropoff_zone_id=161,
        routing_distance_m=4260.0,
        weekday_1_7=1,
        hour_0_23=14,
    )

def test_model_service_rejects_missing_model_file(tmp_path):
    missing_path = tmp_path / "no_model.joblib"
    with pytest.raises(FileNotFoundError, match="Model file not found"):
        ModelService(model_path=missing_path)

def test_model_service_loads_model_from_given_path(tmp_path, monkeypatch):
    model_path = tmp_path / "fake_model.joblib"
    model_path.write_bytes(b"fake")
    loaded_paths = []
    fake_model = FakeModel()
    monkeypatch.setattr(
        service_module.joblib,
        "load",
        lambda path: loaded_paths.append(path) or {"model": fake_model},
    )
    service = ModelService(model_path=model_path)
    assert loaded_paths == [model_path]
    assert service.model is fake_model

def test_predict_passes_correct_feature_values_to_model(tmp_path, monkeypatch):
    service, fake_model = create_service(tmp_path, monkeypatch)
    sample_prediction(service)
    assert fake_model.received_features.iloc[0].to_dict() == {
        "PULocationID": 43,
        "DOLocationID": 161,
        "weekday_1_7": 1,
        "routing_distance_m": 4260.0,
        "hour_0_23": 14,
    }

def test_predict_uses_feature_order_saved_in_metadata(tmp_path, monkeypatch):
    order = ["hour_0_23", "routing_distance_m", "DOLocationID", "PULocationID", "weekday_1_7"]
    service, fake_model = create_service(
        tmp_path, monkeypatch, metadata={"feature_columns": order}
    )
    sample_prediction(service)
    assert fake_model.received_features.columns.tolist() == order

def test_predict_uses_default_features_without_metadata(tmp_path, monkeypatch):
    service, fake_model = create_service(tmp_path, monkeypatch)
    sample_prediction(service)
    assert fake_model.received_features.columns.tolist() == [
        "PULocationID", "DOLocationID", "weekday_1_7", "routing_distance_m", "hour_0_23"
    ]

def test_predict_returns_float_from_numpy_scalar(tmp_path, monkeypatch):
    service, _ = create_service(tmp_path, monkeypatch, prediction=np.float32(15.78))
    result = sample_prediction(service)
    assert isinstance(result, float)
    assert result == pytest.approx(15.78, abs=0.001)
