import os
import polars as pl
from shapely import wkt
from shapely.geometry import Point

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_ZONES_PATH = os.path.join(
    BASE_DIR, "data", "processed", "NYC_Taxi_Zones.parquet"
)


class NYCZoneMapper:
    def __init__(self, zones_path: str = DEFAULT_ZONES_PATH):
        if not os.path.exists(zones_path):
            raise FileNotFoundError(f"Zones file not found at: {zones_path}")

        self.zones = self._load_and_prepare_zones(zones_path)

    def _load_and_prepare_zones(self, path: str):
        df = pl.read_parquet(path)
        prepared = []

        for row in df.to_dicts():
            geom = wkt.loads(row["geometry"])
            prepared.append(
                {
                    "id": row["LocationID"],
                    "polygon": geom,
                    "centroid_x": geom.centroid.x,
                    "centroid_y": geom.centroid.y,
                }
            )
        return prepared

    def get_zone_id(self, lon: float, lat: float) -> int:
        point = Point(lon, lat)

        sorted_zones = sorted(
            self.zones,
            key=lambda z: (z["centroid_x"] - lon) ** 2 + (z["centroid_y"] - lat) ** 2,
        )

        for z in sorted_zones:
            if z["polygon"].contains(point):
                return z["id"]

        return None
