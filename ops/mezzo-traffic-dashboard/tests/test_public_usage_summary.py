import importlib.util
import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "traffic_dashboard.py"
SPEC = importlib.util.spec_from_file_location("traffic_dashboard", SCRIPT)
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


class PublicUsageSummaryTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(
            "create table mcp_visits (bucket integer, visitor_hash text, country text, region text, city text, timezone text, colo text, client text, route_group text, method text, status integer, hits integer, primary key(bucket,visitor_hash,route_group,method,status))"
        )
        self.connection.execute(
            "create table mcp (bucket integer primary key, calls integer, initializations integer, errors integer, latency_ms integer)"
        )
        self.now = 1_700_000_000

    def add_visitors(self, count, city, route="landing", client="browser", hits=1, offset=0):
        for index in range(count):
            self.connection.execute(
                "insert into mcp_visits values(?,?,?,?,?,?,?,?,?,?,?,?)",
                (self.now - 60 - offset, f"visitor-{city}-{index}", "DE", "BW", city, "Europe/Berlin", "FRA", client, route, "GET", 200, hits),
            )

    def test_summary_is_30_day_coarse_and_suppresses_small_cities(self):
        self.add_visitors(12, "Heilbronn", hits=2)
        self.add_visitors(10, "Stuttgart", route="docs")
        self.add_visitors(9, "SmallTown")
        self.add_visitors(20, "BotCity", client="bot_or_monitor")
        self.add_visitors(20, "OldTown", offset=31 * 24 * 60 * 60)
        self.add_visitors(20, "AssetCity", route="assets")
        self.connection.executemany(
            "insert into mcp values(?,?,?,?,?)",
            [(self.now - 3_600, 2, 0, 0, 20), (self.now - 120, 1, 0, 0, 10)],
        )

        result = dashboard.public_usage_summary(self.connection, now=self.now)

        self.assertEqual(result["windowDays"], 30)
        self.assertEqual(result["estimatedVisitors"], 30)
        self.assertEqual(result["visits"], 45)
        self.assertEqual(result["citiesReached"], 2)
        self.assertEqual([city["city"] for city in result["topCities"]], ["Heilbronn", "Stuttgart"])
        self.assertEqual(result["topCities"][0]["estimatedVisitors"], 10)
        self.assertEqual(result["topCities"][0]["visits"], 25)
        self.assertEqual(result["lastMcpCallAt"], datetime.fromtimestamp(self.now - 120, timezone.utc).isoformat().replace("+00:00", "Z"))
        self.assertNotIn("visitor_hash", str(result))

    def test_summary_uses_null_when_no_mcp_request_has_been_recorded(self):
        self.add_visitors(10, "Heilbronn")

        result = dashboard.public_usage_summary(self.connection, now=self.now)

        self.assertIsNone(result["lastMcpCallAt"])

    def tearDown(self):
        self.connection.close()


if __name__ == "__main__":
    unittest.main()
