import importlib.util
import sys
import types
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "job_search_prefilter", ROOT / "src" / "job_search_prefilter.py"
)
prefilter = importlib.util.module_from_spec(SPEC)
# The classifier itself needs only the standard library. The production module
# imports python-dateutil for unrelated date parsing; stub that dependency here
# so this focused test remains runnable in a minimal local environment.
dateutil_stub = types.ModuleType("dateutil")
date_parser_stub = types.ModuleType("dateutil.parser")
date_parser_stub.parse = lambda *args, **kwargs: None
dateutil_stub.parser = date_parser_stub
sys.modules.setdefault("dateutil", dateutil_stub)
sys.modules.setdefault("dateutil.parser", date_parser_stub)
sys.modules[SPEC.name] = prefilter
SPEC.loader.exec_module(prefilter)


class LanguageClassificationTests(unittest.TestCase):
    def classify(self, text):
        return prefilter.classify_language_requirements(text)

    def test_english_required_and_german_plus_are_kept_separate(self):
        result = self.classify("Very good English (written and verbal); German is a plus.")
        self.assertEqual(result["english"]["requirement"], "required")
        self.assertEqual(result["german"]["requirement"], "preferred")
        self.assertEqual(prefilter.assess_language("Very good English; German is a plus.")[2], "main")

    def test_german_welcome_but_not_required_is_not_a_hard_gate(self):
        result = self.classify("Fluent in English. German is welcome but not a requirement.")
        self.assertEqual(result["english"]["requirement"], "required")
        self.assertEqual(result["german"]["requirement"], "not_required")

    def test_a2_and_cefr_levels_are_extracted(self):
        cases = (
            ("German A2 required.", "A2"),
            ("At least a B1 level of German proficiency is required.", "B1"),
            ("German at B1+ level is mandatory.", "B1+"),
            ("Fluent English; German C1 minimum.", "C1"),
            ("Fluent German (C1 minimum) and English.", "C1"),
            ("Deutschkenntnisse auf Niveau B2 erforderlich.", "B2"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                result = self.classify(text)
                self.assertEqual(result["german"]["requirement"], "required")
                self.assertEqual(result["german"]["cefr_level"], expected)

    def test_confident_english_communication_is_a_requirement(self):
        result = self.classify(
            "Communicate clearly and confidently in English and have at least a B1 level of German proficiency."
        )
        self.assertEqual(result["english"]["requirement"], "required")
        self.assertEqual(result["german"]["requirement"], "required")
        self.assertEqual(result["german"]["cefr_level"], "B1")

    def test_vague_good_german_is_required_without_inventing_a_cefr_level(self):
        result = self.classify("Good German skills are important for this role.")
        self.assertEqual(result["german"]["requirement"], "required")
        self.assertIsNone(result["german"]["cefr_level"])

    def test_explicit_not_required_phrase_is_not_misclassified(self):
        for text in (
            "German is optional.",
            "German is not required.",
            "No German required.",
            "Kein Deutsch erforderlich.",
            "Deutschkenntnisse sind nicht erforderlich.",
            "German is welcome but not a requirement.",
        ):
            with self.subTest(text=text):
                expected = "optional" if text == "German is optional." else "not_required"
                self.assertEqual(self.classify(text)["german"]["requirement"], expected)

    def test_conflicting_statements_are_flagged_for_review(self):
        result = self.classify("German is required. German is not required for this position.")
        self.assertEqual(result["german"]["requirement"], "conflicting")
        self.assertTrue(result["german"]["needs_review"])
        self.assertEqual(prefilter.assess_language("German required. German not required.")[2], "german_required")

    def test_bare_language_context_is_unclear_and_has_evidence(self):
        result = self.classify("You will work with German-speaking customers.")
        self.assertEqual(result["german"]["requirement"], "unclear")
        self.assertTrue(result["german"]["needs_review"])
        self.assertIn("German-speaking customers", result["german"]["evidence"][0])

    def test_evidence_summary_is_bounded_and_safe_for_markdown_output(self):
        classification = self.classify("German is a plus <https://evil.example> *bold* | English is required.")
        summary = prefilter._language_evidence_summary(classification)
        self.assertNotIn("<", summary)
        self.assertNotIn(">", summary)
        self.assertNotIn("*", summary)
        self.assertNotIn("https://", summary)

    def test_no_german_mention_is_distinct_from_english_only_requirement(self):
        no_languages = self.classify("Support process documentation and stakeholder workshops.")
        english_only = self.classify("English is the working language.")
        self.assertEqual(no_languages["german"]["requirement"], "not_mentioned")
        self.assertEqual(english_only["german"]["requirement"], "not_mentioned")
        self.assertEqual(english_only["english"]["requirement"], "required")
        self.assertIn("English required", prefilter.assess_language("English is the working language.")[1])


if __name__ == "__main__":
    unittest.main()
