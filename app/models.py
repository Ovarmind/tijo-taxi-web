from pydantic import BaseModel, Field


class Point(BaseModel):
    latitude: float = Field(..., ge=-90, le=90,json_schema_extra={"example": 40.758})
    longitude: float = Field(..., ge=-180, le=180, json_schema_extra={"example": 73.9855})
