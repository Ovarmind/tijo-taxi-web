from types import SimpleNamespace

import pytest
from shapely.geometry import Polygon

from app import zone_mapper as zone_module
from app.zone_mapper import NYCZoneMapper

def make_mapper(*items):
    mapper = NYCZoneMapper.__new__(NYCZoneMapper)
    mapper.zones = [
        {
            "id": zone_id,
            "polygon": polygon,
            "centroid_x": polygon.centroid.x,
            "centroid_y": polygon.centroid.y,
        }
        for zone_id, polygon in items
    ]
    return mapper

SQUARE = Polygon([(-74.1, 40.6), (-73.9, 40.6), (-73.9, 40.8), (-74.1, 40.8)])

def test_mapper_raises_when_zone_file_does_not_exist(tmp_path):
    missing_file = tmp_path / "missing_zones.parquet"
    with pytest.raises(FileNotFoundError, match="Zones file not found"):
        NYCZoneMapper(str(missing_file))

def test_mapper_finds_zone_for_point_inside_polygon():
    mapper = make_mapper((101, SQUARE))
    result = mapper.get_zone_id(lon=-74.0, lat=40.7)
    assert result == 101

def test_mapper_returns_none_for_point_outside_all_polygons():
    mapper = make_mapper((101, SQUARE))
    result = mapper.get_zone_id(lon=0.0, lat=0.0)
    assert result is None

def test_mapper_does_not_treat_polygon_boundary_as_inside():
    mapper = make_mapper((101, SQUARE))
    result = mapper.get_zone_id(lon=-74.1, lat=40.7)
    assert result is None

def test_mapper_selects_polygon_with_closer_centroid_when_zones_overlap():
    large = Polygon([(-75, 40), (-72, 40), (-72, 43), (-75, 43)])
    small = Polygon([(-74.2, 40.5), (-73.8, 40.5), (-73.8, 40.9), (-74.2, 40.9)])
    mapper = make_mapper((1, large), (2, small))
    result = mapper.get_zone_id(lon=-74, lat=40.7)
    assert result == 2

def test_mapper_converts_geometry_wkt_to_polygon_and_centroid(monkeypatch):
    calls = []
    rows = [{"LocationID": 101, "geometry": SQUARE.wkt}]
    monkeypatch.setattr(
        zone_module.pl,
        "read_parquet",
        lambda path: calls.append(path) or SimpleNamespace(to_dicts=lambda: rows),
    )
    mapper = NYCZoneMapper.__new__(NYCZoneMapper)
    zones = mapper._load_and_prepare_zones("example.parquet")
    assert calls == ["example.parquet"]
    assert len(zones) == 1
    assert zones[0]["id"] == 101
    assert zones[0]["polygon"].equals(SQUARE)
    assert zones[0]["centroid_x"] == pytest.approx(-74.0)
    assert zones[0]["centroid_y"] == pytest.approx(40.7)
