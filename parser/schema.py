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
    city: str | None = None
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
