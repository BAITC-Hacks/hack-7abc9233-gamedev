from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

CALENDAR_START = date(2026, 9, 23)
CALENDAR_END = date(2026, 12, 31)
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    city: Text
    event_date: date
    event_type: Text
    category: Text
    budget: Annotated[int, Field(ge=0, strict=True)]
    duration: Annotated[float, Field(gt=0)] | None = None
    language: Text | None = None

    @field_validator("event_date")
    @classmethod
    def supported_date(cls, value: date) -> date:
        if not CALENDAR_START <= value <= CALENDAR_END:
            raise ValueError("Календарь доступен только с 2026-09-23 по 2026-12-31")
        return value


class Contractor(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    id: Text
    anon_name: Text
    categories: tuple[Text, ...] = Field(min_length=1)
    city: Text
    city_imputed: bool
    synthetic: bool
    price_from_kzt: int = Field(ge=0)
    price_imputed: bool
    event_formats: tuple[Text, ...] = Field(min_length=1)
    languages: tuple[Text, ...] = Field(min_length=1)
    max_hours: float | None = Field(default=None, gt=0)
    busy_dates: frozenset[date]
    description: str


class Recommendation(BaseModel):
    id: str
    name: str
    category: str
    city: str
    price: int
    explanation: str
    synthetic: bool
    city_imputed: bool
    price_imputed: bool


class RecommendResponse(BaseModel):
    status: Literal["matches_found", "no_category_in_city", "no_matches"]
    count: int
    results: list[Recommendation]
    message: str
    total_candidates: int
    total_matches: int
    exclusion_counts: dict[str, int]
