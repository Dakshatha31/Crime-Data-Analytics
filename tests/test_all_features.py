"""
Comprehensive Test Suite for Crime Data Analytics Platform.
Verifies all 5 Big Data workings and all 10 project features.
"""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.datacenter_to_hdfs import import_datacenter_to_hdfs, export_hdfs_to_datacenter
from ingestion.sql_to_hdfs import export_sql_to_hdfs, import_hdfs_to_sql
from ingestion.mongodb_to_hdfs import export_mongodb_to_hdfs
from ingestion.multi_source_integration import run_multi_source_integration
from nosql.mongo_service import mongo_service
from pig.pig_runner import pig_runner
from hive.hive_runner import hive_runner
from analytics.safe_route import safe_route_engine
from analytics.hotspot_engine import hotspot_engine
from analytics.time_patterns import time_pattern_engine
from analytics.area_comparisons import area_comparison_engine
from analytics.forecasting import crime_forecast_engine
from analytics.benchmark_runner import benchmark_engine
from analytics.report_generator import report_generator


class TestCrimeAnalyticsPlatform(unittest.TestCase):

    def test_01_datacenter_to_hdfs(self):
        """Working 1: Datacenter to HDFS Import & Export."""
        res_import = import_datacenter_to_hdfs()
        self.assertEqual(res_import["status"], "success")
        self.assertGreaterEqual(res_import["total_records"], 20000)

        res_export = export_hdfs_to_datacenter()
        self.assertEqual(res_export["status"], "success")
        self.assertGreaterEqual(res_export["total_exported_records"], 20000)

    def test_02_sql_to_hdfs(self):
        """Working 2: SQL Relational tables to HDFS and reverse sync."""
        res_export = export_sql_to_hdfs()
        self.assertEqual(res_export["status"], "success")
        self.assertIn("area_reference", res_export["exported_tables"])
        self.assertIn("police_stations", res_export["exported_tables"])

        res_import = import_hdfs_to_sql()
        self.assertEqual(res_import["status"], "success")

    def test_03_mongodb_nosql_and_complaint(self):
        """Working 3 & Feature 2: MongoDB NoSQL and Add New Complaint."""
        complaint_data = {
            "incident_date": "2026-10-13",
            "incident_time": "14:15",
            "crime_type": "Theft",
            "area_id": "A001",
            "area_name": "Central",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "description": "Test automated unit test complaint"
        }
        res = mongo_service.insert_complaint(complaint_data)
        self.assertTrue(res["complaint_id"].startswith("CMP-"))
        self.assertEqual(res["complaint_status"], "Under Review")
        self.assertFalse(res["verified_record"])

        res_sync = export_mongodb_to_hdfs()
        self.assertEqual(res_sync["status"], "success")
        self.assertGreaterEqual(res_sync["total_records"], 500)

    def test_04_pig_data_analysis(self):
        """Working 4: Structured Data Analysis using PIG."""
        res_clean = pig_runner.run_clean_crimes()
        self.assertEqual(res_clean["status"], "success")
        self.assertGreaterEqual(res_clean["output_records"], 20000)

        res_hotspot = pig_runner.run_hotspot_pig()
        self.assertEqual(res_hotspot["status"], "success")
        self.assertGreaterEqual(res_hotspot["total_hotspot_clusters"], 10)

        res_hourly = pig_runner.run_hourly_pig()
        self.assertEqual(res_hourly["status"], "success")
        self.assertGreaterEqual(res_hourly["total_slots"], 100)

    def test_05_hive_structured_analysis(self):
        """Working 5: Structured Data Process/Analysis using HIVE."""
        hive_runner.sync_external_tables()
        trends = hive_runner.run_monthly_trends_hive()
        self.assertEqual(trends["status"], "success")
        self.assertGreaterEqual(trends["row_count"], 12)

        areas = hive_runner.run_area_per_capita_hive()
        self.assertEqual(areas["status"], "success")
        self.assertGreaterEqual(areas["row_count"], 5)

    def test_06_safe_route_suggestion(self):
        """Feature 1: Safe-Route Suggestion Engine."""
        res = safe_route_engine.suggest_routes("A001", "A003", hour_of_day=22)
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["routes_count"], 1)
        self.assertIn("disclaimer", res)
        # Check route attributes
        route = res["routes"][0]
        self.assertIn("risk_score", route)
        self.assertIn("distance_km", route)
        self.assertIn("polyline_coordinates", route)

    def test_07_hotspot_detection(self):
        """Feature 5: Crime Hotspot Detection."""
        res = hotspot_engine.get_hotspots()
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["hotspot_count"], 5)
        top = res["hotspots"][0]
        self.assertEqual(top["rank"], 1)
        self.assertIn("circle_radius_meters", top)

    def test_08_time_patterns(self):
        """Feature 6: Time-Pattern Analysis."""
        res = time_pattern_engine.get_time_patterns()
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["hourly_distribution"]), 24)
        self.assertEqual(len(res["day_of_week_distribution"]), 7)

    def test_09_area_and_trends(self):
        """Features 4 & 7: Area Comparisons & Crime Trends."""
        res_comp = area_comparison_engine.compare_areas()
        self.assertEqual(res_comp["status"], "success")
        self.assertGreaterEqual(res_comp["total_areas_compared"], 5)

        res_trends = area_comparison_engine.get_crime_trends()
        self.assertEqual(res_trends["status"], "success")
        self.assertGreaterEqual(len(res_trends["monthly_trends"]), 12)

    def test_10_multi_source_integration(self):
        """Feature 8: Multi-Source Data Integration & Deduplication."""
        res = run_multi_source_integration()
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["clean_integrated_records"], 20000)
        self.assertIn("datacenter_historical_csv", res["source_breakdown"])

    def test_11_forecasting(self):
        """Feature 9: Crime Trend Forecasting."""
        res = crime_forecast_engine.forecast_trends(horizon_months=6)
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["forecast_data"]), 6)
        self.assertIn("disclaimer", res)

    def test_12_scalability_benchmark(self):
        """Feature 10: Scalability Benchmark on 100K Records."""
        res = benchmark_engine.run_benchmark(sample_sizes=[100000])
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["results"]), 1)
        b = res["results"][0]
        self.assertGreater(b["speedup_factor"], 1.0)

    def test_13_report_generator_pdf_csv(self):
        """Feature 3: Report Generator (CSV & PDF)."""
        csv_file = report_generator.export_csv()
        self.assertTrue(csv_file.exists())
        self.assertGreater(csv_file.stat().st_size, 1000)

        pdf_file = report_generator.export_pdf()
        self.assertTrue(pdf_file.exists())
        self.assertGreater(pdf_file.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
