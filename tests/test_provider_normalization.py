import unittest
from unittest.mock import patch

import parser.core as core
from parser.llm import LLMError


ADISH_BRIEF = (
    "backend hiring for the platform team. NOT looking for anyone from consulting or services firms. "
    "no fresh grads. and we don't want pure Java people — we need someone who has actually worked "
    "with Go or Rust. Bangalore or Pune both work."
)


class ProviderNormalizationTests(unittest.TestCase):
    def setUp(self):
        core._usage = {"briefs": 0, "input_tokens": 0, "output_tokens": 0, "source": "approximate"}

    def test_preserves_multi_city_provider_semantics(self):
        raw = {
            "role_family": "Engineering", "job_title": "Backend Engineer", "seniority_band": None,
            "years_experience": {"min": None, "max": None, "raw": None},
            "must_have_skills": ["Go", "Rust"], "preferred_skills": [], "acceptable_skills": [],
            "location": {"city": ["Bangalore", "Pune"], "country": None, "preference": None},
            "work_mode": None, "domain_context": "Platform",
            "compensation": {"min": None, "max": None, "currency": None, "unit": None, "period": None, "upper_bound": None},
            "headcount": None,
            "exclusions": ["consulting firms", "services firms", "fresh grads", "pure Java people"],
        }
        with patch.object(core, "extract_with_gemini", return_value=(raw, {"input_tokens": 210, "output_tokens": 260, "source": "provider"})):
            result = core.parse_brief(ADISH_BRIEF)
        self.assertEqual(result["must_have_skills"], ["Go", "Rust"])
        self.assertNotIn("Java", result["must_have_skills"])
        self.assertEqual(result["location"]["city"], ["Bangalore", "Pune"])
        self.assertEqual(result["domain_context"], ["Platform"])
        self.assertEqual(result["exclusions"], ["consulting firms", "services firms", "fresh grads", "pure Java people"])
        self.assertEqual(core.usage_stats()["source"], "provider")

    def test_normalizes_senior_staff_without_fallback(self):
        raw = {
            "role_family": "Engineering", "job_title": "Senior Staff Backend Architect", "seniority_band": "Senior Staff",
            "years_experience": {"min": 1, "max": 2, "raw": "1-2 years"},
            "must_have_skills": ["Node.js", "MongoDB"], "preferred_skills": [], "acceptable_skills": [],
            "location": {"city": "Hyderabad", "country": None, "preference": None}, "work_mode": None,
            "domain_context": None, "compensation": None, "headcount": None, "exclusions": [],
        }
        with patch.object(core, "extract_with_gemini", return_value=(raw, {"input_tokens": 1, "output_tokens": 1, "source": "provider"})):
            result = core.parse_brief("Senior Staff Backend Architect — Hyderabad. Experience required: 1-2 years. Skills: Node.js, MongoDB.")
        self.assertEqual(result["seniority_band"], "staff")
        self.assertEqual(result["job_title"], "Senior Staff Backend Architect")
        self.assertEqual(result["years_experience"], {"min": 1.0, "max": 2.0, "raw": "1-2 years"})
        self.assertEqual(result["must_have_skills"], ["Node.js", "MongoDB"])
        self.assertEqual(core.usage_stats()["source"], "provider")

    def test_preserves_acceptable_skill_classification(self):
        raw = {
            "role_family": "Engineering", "job_title": "Backend", "seniority_band": None,
            "years_experience": {"min": 7, "max": None, "raw": "7+"},
            "must_have_skills": [], "preferred_skills": ["Go"], "acceptable_skills": ["Java"],
            "location": {"city": "Bangalore", "country": None, "preference": "preferred"},
            "work_mode": None, "domain_context": None, "compensation": None, "headcount": None, "exclusions": [],
        }
        with patch.object(core, "extract_with_gemini", return_value=(raw, {"input_tokens": 1, "output_tokens": 1, "source": "provider"})):
            result = core.parse_brief("Go would be ideal, Java is fine too.")
        self.assertEqual(result["preferred_skills"], ["Go"])
        self.assertEqual(result["acceptable_skills"], ["Java"])
        self.assertNotIn("Java", result["must_have_skills"])
        self.assertNotIn("Java", result["preferred_skills"])
        self.assertEqual(core.usage_stats()["source"], "provider")

    def test_uses_fallback_only_for_llm_failure(self):
        with patch.object(core, "extract_with_gemini", side_effect=LLMError("offline")):
            core.parse_brief("backend role")
        self.assertEqual(core.usage_stats()["source"], "approximate")


if __name__ == "__main__":
    unittest.main()
