from dataclasses import dataclass
from typing import Any
from routingpy.routers import OSRM
from app.models import Point


@dataclass
class RouteResult:
    distance_m: float
    street_names: list[str]


def extract_street_names(data: dict[str, Any]) -> list[str]:
    names = []
    seen = set()

    routes = data.get("routes", [])
    if not routes:
        return names

    for leg in routes[0].get("legs", []):
        for step in leg.get("steps", []):
            name = step.get("name")
            if name and name not in seen:
                seen.add(name)
                names.append(name)

    return names


def calculate_route(
    point_a: Point,
    point_b: Point,
    base_url: str = "http://router.project-osrm.org",
) -> RouteResult:
    router = OSRM(base_url=base_url, timeout=15)

    route = router.directions(
        locations=[
            [point_a.longitude, point_a.latitude],
            [point_b.longitude, point_b.latitude],
        ],
        steps=True,
    )

    data = route.raw or {}

    if not data.get("routes"):
        raise ValueError(f"No route found: {data}")

    street_names = extract_street_names(data)

    return RouteResult(
        distance_m=route.distance,
        street_names=street_names,
    )
