import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("slack_runner", ROOT / "src" / "slack_runner.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class FakeValidator:
    @staticmethod
    def render_combined_1500(*, student_results, fulltime_results, max_age_days, analytics):
        titles = [item["title"] for item in sorted(student_results, key=lambda x: x.get("_ai_priority", 0))]
        return json.dumps({"titles": titles, "analytics": analytics}, sort_keys=True)


def item(index, section):
    url = f"https://jobs.example/{section}/{index}"
    return {"title": str(index), "url": url, "normalized_url": url}


class RunnerAiTests(unittest.TestCase):
    def test_shadow_mode_keeps_existing_report_and_payload_untouched(self):
        payload = {"student_results": [item(1, "student"), item(2, "student")], "fulltime_results": []}
        before = json.dumps(payload, sort_keys=True)
        report = runner.format_report(payload, FakeValidator, "shadow", {"status": "ok", "rankings": []})
        self.assertEqual(json.dumps(payload, sort_keys=True), before)
        self.assertEqual(json.loads(report)["titles"], ["1", "2"])

    def test_rank_mode_only_orders_existing_display_candidates(self):
        candidates = [item(i, "student") for i in range(1, 10)]
        payload = {"student_results": candidates, "fulltime_results": []}
        rankings = []
        for i, record in enumerate(reversed(candidates[:7]), start=1):
            import hashlib
            cid = hashlib.sha256(record["normalized_url"].lower().encode()).hexdigest()[:24]
            rankings.append({"candidate_id": cid, "section": "student", "priority": i})
        runner.apply_ai_order(payload, {"rankings": rankings})
        self.assertEqual(len(payload["student_results"]), 9)
        self.assertEqual([x["title"] for x in sorted(candidates[:7], key=lambda x: x["_ai_priority"])], ["7", "6", "5", "4", "3", "2", "1"])
        self.assertTrue(all(x["_ai_priority"] == 999 for x in candidates[7:]))

    def test_rank_mode_model_failure_keeps_deterministic_report(self):
        payload = {"student_results": [item(1, "student"), item(2, "student")], "fulltime_results": []}
        shadow = runner.format_report(payload, FakeValidator, "shadow", {"status": "failed"})
        rank_fallback = runner.format_report(payload, FakeValidator, "rank", {"status": "failed"})
        self.assertEqual(rank_fallback, shadow)
        self.assertNotIn("AI note", rank_fallback)


if __name__ == "__main__":
    unittest.main()
