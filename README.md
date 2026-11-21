
# NYC Taxi — predykcja czasu przejazdu

## Nazwa kursu

Testowanie i Jakość Oprogramowania II

## Autor

Bartłomiej Danek

## Temat projektu

Aplikacja webowa do predykcji czasu przejazdu taksówką w Nowym Jorku z wykorzystaniem modelu regresji Ridge.

## Opis projektu

Aplikacja pozwala oszacować czas przejazdu taksówką pomiędzy dwoma punktami w Nowym Jorku. Użytkownik wybiera na mapie miejsce rozpoczęcia i zakończenia przejazdu oraz podaje dzień tygodnia i godzinę wyjazdu.

Przebieg predykcji:

1. Frontend przesyła współrzędne i parametry przejazdu do endpointu `POST /predict`.
2. Backend FastAPI sprawdza poprawność danych wejściowych za pomocą Pydantic.
3. Punkty GPS są przypisywane do stref NYC Taxi na podstawie geometrii stref zapisanych w pliku Parquet.
4. Serwis OSRM wyznacza długość trasy drogowej oraz nazwy ulic.
5. Wytrenowany model Ridge przewiduje czas przejazdu na podstawie pięciu cech: `PULocationID`, `DOLocationID`, `weekday_1_7`, `routing_distance_m` i `hour_0_23`.
6. Wynik jest wyświetlany w przeglądarce wraz z dystansem, identyfikatorami stref i nazwami ulic.

## Technologie

- **Backend:** Python 3.12, FastAPI, Pydantic, Uvicorn.
- **Frontend:** HTML, CSS, JavaScript, Leaflet, OpenStreetMap.
- **Predykcja:** scikit-learn (Ridge), pandas, joblib.
- **Dane przestrzenne:** Polars, Shapely, Parquet.
- **Wyznaczanie trasy:** OSRM, routingpy.
- **Testowanie:** pytest, FastAPI TestClient, httpx.
- **Zależności:** `requirements.txt`, opcjonalnie `uv`.

## Struktura projektu

```text
tijo_taxi_web/
├── api/
│   ├── main.py
│   ├── schemas.py
│   └── services/
│       └── model_service.py
├── app/
│   ├── models.py
│   ├── routing.py
│   └── zone_mapper.py
├── data/
│   └── processed/
│       └── NYC_Taxi_Zones.parquet
├── frontend/
│   └── index.html
├── models/
│   └── ridge_travel_time_2025_zones.joblib
├── tests/
│   ├── unit/
│   └── integration/
├── .gitignore
├── requirements.txt
└── README.md
```

## Uruchomienie projektu

Wymagany jest Python 3.12. Poniższe polecenia wykonuje się w katalogu głównym projektu w terminalu CMD w systemie Windows.

### Instalacja zależności z użyciem `uv`

```cmd
uv venv --python 3.12
uv pip install -r requirements.txt
.venv\Scripts\activate
```

### Alternatywnie: instalacja bez `uv`

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Uruchomienie serwera

```cmd
python -m uvicorn api.main:app --reload
```

Po pojawieniu się komunikatu `Application startup complete` otwórz w przeglądarce:

- Aplikacja: <http://127.0.0.1:8000>
- Dokumentacja API (Swagger UI): <http://127.0.0.1:8000/docs>

Aby zatrzymać serwer, naciśnij `Ctrl+C` w terminalu.

### Testy jednostkowe

**Lokalizacja:** [`tests/unit/`](tests/unit/)

Zestaw zawiera 34 przypadki testowe. Sprawdzane są:

- walidacja współrzędnych, dnia tygodnia i godziny;
- przetwarzanie wyniku routingu i obsługa błędów;
- przypisywanie punktów do stref NYC;
- wczytywanie modelu Ridge i przygotowywanie cech wejściowych.

Uruchomienie:

```cmd
python -m pytest tests/unit -v
```

### Testy integracyjne

**Lokalizacja:** [`tests/integration/`](tests/integration/)

Zestaw zawiera 24 przypadki testowe. Sprawdzane są:

- dostępność aplikacji, plików statycznych, endpointu `/health` i dokumentacji API;
- obsługa żądań HTTP do `/predict`, w tym walidacja danych i odpowiedzi błędów;
- współpraca endpointu predykcji z routingiem, mapowaniem stref i modelem Ridge;
- wczytanie testowych stref z pliku Parquet i wykonanie predykcji.

Zależności zewnętrzne, takie jak OSRM, są zastępowane kontrolowanymi odpowiedziami tam, gdzie wymaga tego scenariusz testowy.

Uruchomienie:

```cmd
python -m pytest tests/integration -v
```

### Uruchomienie wszystkich testów

```cmd
python -m pytest tests/unit tests/integration -v
```

## Dokumentacja API

Dokumentacja generowana automatycznie przez FastAPI jest dostępna pod adresem <http://127.0.0.1:8000/docs> po uruchomieniu serwera.

| Metoda | Endpoint | Opis |
| --- | --- | --- |
| `GET` | `/` | Wyświetla interfejs aplikacji. |
| `GET` | `/health` | Zwraca stan działania API. |
| `POST` | `/predict` | Oblicza przewidywany czas przejazdu. |
| `GET` | `/openapi.json` | Udostępnia specyfikację OpenAPI. |

### `GET /health`

Przykładowa odpowiedź:

```json
{
  "status": "ok"
}
```

### `POST /predict`

Przykładowe żądanie JSON:

```json
{
  "pickup": {
    "latitude": 40.758,
    "longitude": -73.9855
  },
  "dropoff": {
    "latitude": 40.7128,
    "longitude": -74.006
  },
  "weekday_1_7": 2,
  "hour_0_23": 14
}
```

Znaczenie parametrów:

| Pole | Opis |
| --- | --- |
| `pickup` | Szerokość i długość geograficzna punktu startowego. |
| `dropoff` | Szerokość i długość geograficzna punktu docelowego. |
| `weekday_1_7` | Dzień tygodnia, wartość od 1 do 7. |
| `hour_0_23` | Godzina rozpoczęcia przejazdu, wartość od 0 do 23. |

Pomyślna odpowiedź zawiera następujące pola:

| Pole | Opis |
| --- | --- |
| `predicted_travel_time_min` | Przewidywany czas przejazdu w minutach. |
| `pickup_location_id` | Identyfikator strefy początkowej NYC Taxi. |
| `dropoff_location_id` | Identyfikator strefy docelowej NYC Taxi. |
| `routing_distance_m` | Długość trasy w metrach. |
| `route_street_names` | Lista nazw ulic na trasie. |

Obsługiwane błędy obejmują:

- `422` — niepoprawne dane wejściowe lub punkt poza strefami NYC Taxi;
- `503` — problem z pobraniem trasy z OSRM;
- `500` — błąd podczas obliczania predykcji.

## Przypadki testowe dla testera manualnego (TestCase)
