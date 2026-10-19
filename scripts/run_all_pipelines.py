"""
End-to-End Big Data Pipeline Runner.
Executes the full pipeline across all 5 core workings:
1. Datacenter -> HDFS Ingestion
2. SQL -> HDFS Relational Export
3. MongoDB NoSQL Seeding & Ingestion -> HDFS
4. Multi-Source Integration & Deduplication
5. Apache Pig Data Cleaning & Hotspot Aggregation
6. Apache Hive Schema Synchronization & Trend Queries
7. Automated Executive PDF & CSV Report Generation
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.datacenter_to_hdfs import import_datacenter_to_hdfs
from ingestion.sql_to_hdfs import export_sql_to_hdfs, import_hdfs_to_sql
from ingestion.mongodb_to_hdfs import export_mongodb_to_hdfs
from ingestion.multi_source_integration import run_multi_source_integration
from pig.pig_runner import pig_runner
from hive.hive_runner import hive_runner
from analytics.report_generator import report_generator
from nosql.mongo_service import mongo_service


def run_all():
    print("=" * 75)
    print("  CRIME DATA ANALYTICS -- END-TO-END BIG DATA PIPELINE RUNNER")
    print("=" * 75)
    t0 = time.time()

    # Step 1: Datacenter to HDFS
    print("\n[Stage 1/7] Ingesting Datacenter Historical CSV to HDFS...")
    res_dc = import_datacenter_to_hdfs()
    print(f"  [+] Copied {res_dc['total_records']:,} records to {res_dc['hdfs_destination']}")

    # Step 2: SQL to HDFS
    print("\n[Stage 2/7] Exporting Relational SQL Tables to HDFS...")
    res_sql = export_sql_to_hdfs()
    print(f"  [+] Exported tables: {list(res_sql['exported_tables'].keys())} to HDFS")

    # Step 3: MongoDB NoSQL to HDFS
    print("\n[Stage 3/7] Ingesting MongoDB NoSQL Complaints to HDFS...")
    res_mongo = export_mongodb_to_hdfs()
    print(f"  [+] Exported {res_mongo['total_records']} complaint documents to {res_mongo['files_exported'][0]}")

    # Step 4: Multi-Source Integration & Deduplication
    print("\n[Stage 4/7] Running Multi-Source Integration & Deduplication Engine...")
    res_int = run_multi_source_integration()
    print(f"  [+] Processed {res_int['raw_records_imported']:,} raw records")
    print(f"  [+] Removed {res_int['duplicates_removed']} duplicate records")
    print(f"  [+] Unified master analytical corpus: {res_int['clean_integrated_records']:,} rows in {res_int['hdfs_destination']}")

    # Step 5: Pig Latin Pipelines
    print("\n[Stage 5/7] Executing Apache Pig Latin Scripts...")
    pig_clean = pig_runner.run_clean_crimes()
    print(f"  [+] [clean_crimes.pig] Processed {pig_clean['input_records']:,} -> {pig_clean['output_records']:,} in {pig_clean['execution_time_seconds']}s")
    pig_hot = pig_runner.run_hotspot_pig()
    print(f"  [+] [hotspot_analysis.pig] Identified {pig_hot['total_hotspot_clusters']} hotspot clusters in {pig_hot['execution_time_seconds']}s")
    pig_time = pig_runner.run_hourly_pig()
    print(f"  [+] [hourly_patterns.pig] Grouped {pig_time['total_slots']} time intervals in {pig_time['execution_time_seconds']}s")

    # Step 6: Hive Warehouse Tables & Queries
    print("\n[Stage 6/7] Synchronizing Hive Metastore & Running HiveQL Analytical Queries...")
    hive_runner.sync_external_tables()
    h_trends = hive_runner.run_monthly_trends_hive()
    print(f"  [+] [Hive Monthly Trends] Computed {h_trends['row_count']} monthly buckets in {h_trends['execution_time_seconds']}s")
    h_areas = hive_runner.run_area_per_capita_hive()
    print(f"  [+] [Hive Distributed Joins] Computed per-capita rates across {h_areas['row_count']} areas in {h_areas['execution_time_seconds']}s")

    # Reverse export to SQL
    res_rev_sql = import_hdfs_to_sql()
    print(f"  [+] [HDFS -> SQL] Synced {res_rev_sql['records_loaded']} analytical aggregates into SQL table sql_crime_aggregates")

    # Step 7: Report Generation (CSV & PDF)
    print("\n[Stage 7/7] Generating Executive Analytical Reports (CSV & PDF)...")
    csv_file = report_generator.export_csv()
    pdf_file = report_generator.export_pdf()
    print(f"  [+] Exported CSV Report: {csv_file.name}")
    print(f"  [+] Generated Executive PDF: {pdf_file.name}")

    total_time = round(time.time() - t0, 2)
    print("\n" + "=" * 75)
    print(f"  ALL BIG DATA PIPELINES EXECUTED SUCCESSFULLY IN {total_time} SECONDS!")
    print("=" * 75)


if __name__ == "__main__":
    run_all()
