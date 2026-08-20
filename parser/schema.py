"""Schema and normalization for extracted hiring criteria."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Seniority = Literal["junior", "mid", "senior", "lead", "staff", "principal"]
WorkMode = Literal["onsite", "hybrid", "remote"]

class Years(BaseModel):
    model_config = ConfigDict(extra="ignore")
    min: float | None = None
    max: float | None = None
    raw: str | None = None

class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")
    city: str | list[str] | None = None
    country: str | None = None
    preference: Literal["required", "preferred", "flexible"] = "required"

class Compensation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    min: float | None = None
    max: float | None = None
    currency: str | None = None
    unit: str | None = None
    period: Literal["annual", "monthly", "hourly", "unknown"] = "unknown"
    upper_bound: bool = False

class Criteria(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role_family: str | None = None
    job_title: str | None = None
    seniority_band: Seniority | None = None
    years_experience: Years | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    acceptable_skills: list[str] = Field(default_factory=list)
    location: Location | None = None
    work_mode: WorkMode | None = None
    domain_context: list[str] = Field(default_factory=list)
    compensation: Compensation | None = None
    headcount: int | None = Field(default=None, ge=1)
    exclusions: list[str] = Field(default_factory=list)

    @field_validator("must_have_skills", "preferred_skills", "acceptable_skills", "domain_context", "exclusions")
    @classmethod
    def clean_lists(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(v.strip() for v in values if isinstance(v, str) and v.strip()))

def validate_criteria(value: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize untrusted provider output; invalid values fail loudly."""
    return Criteria.model_validate(value).model_dump(exclude_none=False)

def normalize_provider_output(value: dict[str, Any]) -> dict[str, Any]:
    """Convert safe provider shape variations to the strict criteria schema."""
    out = dict(value)
    for field in ("must_have_skills", "preferred_skills", "acceptable_skills", "domain_context", "exclusions"):
        if out.get(field) is None:
            out[field] = []
        elif isinstance(out[field], str):
            out[field] = [out[field]]
    if isinstance(out.get("seniority_band"), str):
        seniority = out["seniority_band"].strip().lower().replace("-", " ")
        out["seniority_band"] = "staff" if seniority == "senior staff" else seniority
    if isinstance(out.get("work_mode"), str) and out["work_mode"].strip().lower() in {"office", "in office", "office only"}:
        out["work_mode"] = "onsite"
    if isinstance(out.get("years_experience"), dict):
        years = out["years_experience"]
        if years.get("min") is None and years.get("max") is None and years.get("raw") is None:
            out["years_experience"] = None
    if isinstance(out.get("location"), dict):
        out["location"] = dict(out["location"])
        city = out["location"].get("city")
        if isinstance(city, list):
            out["location"]["city"] = list(dict.fromkeys(item.strip() for item in city if isinstance(item, str) and item.strip()))
            if not out["location"]["city"]:
                out["location"]["city"] = None
        if out["location"].get("city") is None and out["location"].get("country") is None:
            out["location"] = None
        elif out["location"].get("preference") is None:
            out["location"]["preference"] = "required"
    if isinstance(out.get("compensation"), dict):
        out["compensation"] = dict(out["compensation"])
        compensation = out["compensation"]
        if all(compensation.get(field) is None for field in ("min", "max", "currency", "unit")):
            out["compensation"] = None
        elif compensation.get("period") is None:
            out["compensation"]["period"] = "unknown"
        elif compensation.get("period") == "yearly":
            out["compensation"]["period"] = "annual"
        if out.get("compensation") is not None and out["compensation"].get("upper_bound") is None:
            out["compensation"]["upper_bound"] = False
    return out
