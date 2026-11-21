
from api import main as api_module


def test_home_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "NYC Taxi" in response.text


def test_health_returns_success(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_contains_predict_endpoint(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/predict" in response.json()["paths"]
    assert "post" in response.json()["paths"]["/predict"]


def test_swagger_ui_is_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_static_files_are_served(client):
    response = client.get("/static/styles.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


def test_predict_rejects_get_method(client):
    response = client.get("/predict")
    assert response.status_code == 405


def test_predict_rejects_malformed_json(client):
    response = client.post(
        "/predict",
        content="{invalid-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
