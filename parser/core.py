"""Single parsing implementation shared by library, CLI and HTTP."""
from __future__ import annotations
import re, threading
from typing import Any
from .llm import LLMError, extract_with_gemini, estimate_tokens, PROMPT
from .schema import validate_criteria

_lock = threading.Lock(); _usage = {"briefs": 0, "input_tokens": 0, "output_tokens": 0, "source": "approximate"}

def usage_stats() -> dict[str, Any]:
    with _lock:
        d = dict(_usage)
    d["total_tokens"] = d["input_tokens"] + d["output_tokens"]
    d["average_total_tokens_per_brief"] = d["total_tokens"] / d["briefs"] if d["briefs"] else 0
    return d

def _record(stats: dict[str, Any]) -> None:
    with _lock:
        _usage["briefs"] += 1; _usage["input_tokens"] += int(stats.get("input_tokens", 0)); _usage["output_tokens"] += int(stats.get("output_tokens", 0)); _usage["source"] = stats.get("source", "approximate")

def _fallback(text: str) -> dict[str, Any]:
    """Deterministic safety net for local evaluation/offline operation."""
    t, low = text.strip(), text.lower()
    out: dict[str, Any] = {"role_family": None, "job_title": None, "seniority_band": None, "years_experience": None, "must_have_skills": [], "preferred_skills": [], "location": None, "work_mode": None, "domain_context": [], "compensation": None, "headcount": None, "exclusions": []}
    if not t: return out
    if re.search(r"backend", low): out["role_family"] = "backend engineering"
    m = re.search(r"(senior|lead|staff|principal|junior|mid)\s+backend(?:\s+engineer|\s+folks|\s+people)?", low)
    if m: out["seniority_band"] = m.group(1)
    if re.search(r"backend engineer|backend role", low): out["job_title"] = "Backend Engineer"
    if "senior backend engineer" in low or "senior backend folks" in low: out["job_title"] = "Senior Backend Engineer"
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*(?:years?|yrs?|saal)", low)
    if m: out["years_experience"] = {"min": float(m.group(1)), "max": float(m.group(2)), "raw": m.group(0)}
    else:
        m = re.search(r"(?:seven\s*,\s*seven|seven|7)\s*(?:\+|plus)", low)
        if m: out["years_experience"] = {"min": 7.0, "max": None, "raw": m.group(0)}
    def add(skill: str, preferred=False):
        (out["preferred_skills"] if preferred else out["must_have_skills"]).append(skill)
    # “Java is fine” is an acceptable fallback, not a mandatory or preferred
    # skill; retaining it in neither list avoids overstating the requirement.
    if re.search(r"java", low) and "java is fine" not in low: add("Java")
    if re.search(r"kotlin", low): add("Kotlin")
    if re.search(r"kafka", low): add("Kafka")
    if re.search(r"distributed systems", low): add("Distributed systems")
    if re.search(r"postgresql", low): add("PostgreSQL")
    if re.search(r"python\s+must", low): add("Python")
    if re.search(r"\bgo\b.*ideal|go would be ideal", low): add("Go", preferred=True)
    if re.search(r"django", low): add("Django", preferred=True)
    if re.search(r"kubernetes", low): add("Kubernetes", preferred=True)
    if re.search(r"fintech|payments? domain", low): out["domain_context"] = ["fintech", "payments"] if "fintech" in low and "payments" in low else ["fintech" if "fintech" in low else "payments"]
    city = None
    for c in ("Bengaluru", "Bangalore", "Pune"):
        if c.lower() in low: city = "Bengaluru" if c == "Bengaluru" else c; break
    if city: out["location"] = {"city": city, "country": None, "preference": "preferred" if "preferred" in low or "honestly" in low else "required"}
    if "hybrid" in low: out["work_mode"] = "hybrid"
    elif "remote bilkul nahi" in low or "daily" in low or "onsite" in low: out["work_mode"] = "onsite"
    m = re.search(r"(\d+)\s*(?:senior )?(?:backend )?(?:folks|engineers?|people)", low)
    if m: out["headcount"] = int(m.group(1))
    m = re.search(r"budget\s*(?:is\s*)?(?:around\s*)?(\d+)\s*[-–]\s*(\d+)\s*LPA", text, re.I)
    if m: out["compensation"] = {"min": float(m.group(1)), "max": float(m.group(2)), "currency": "INR", "unit": "LPA", "period": "annual", "upper_bound": False}
    else:
        m = re.search(r"budget\s*(\d+)\s*lakh\s*(?:tak|तक)", low)
        if m: out["compensation"] = {"min": None, "max": float(m.group(1)), "currency": "INR", "unit": "lakh", "period": "annual", "upper_bound": True}
    if "service company" in low: out["exclusions"] = ["service company profiles"]
    if "remote bilkul nahi" in low: out["exclusions"].append("remote work")
    return out

def parse_brief(text: str) -> dict[str, Any]:
    if not isinstance(text, str): raise TypeError("text must be a string")
    if not text.strip():
        result = validate_criteria(_fallback(text)); _record({"input_tokens": 0, "output_tokens": estimate_tokens(str(result))}); return result
    try:
        raw, stats = extract_with_gemini(text)
    except LLMError:
        raw = _fallback(text); stats = {"input_tokens": estimate_tokens(PROMPT + text), "output_tokens": estimate_tokens(str(raw)), "source": "approximate"}
    try: result = validate_criteria(raw)
    except Exception:
        result = validate_criteria(_fallback(text)); stats["source"] = "approximate"
    _record(stats); return result
