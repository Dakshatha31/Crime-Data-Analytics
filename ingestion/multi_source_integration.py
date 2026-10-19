"""
Multi-Source Data Integration & Deduplication Engine.
Satisfies Feature 8: Combine historical crime CSV files, SQL tables, and MongoDB complaint
records into a consistent analytical dataset. Track data sources and remove duplicate records.
"""
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager
from ingestion.sql_to_hdfs import init_sql_database
from nosql.mongo_service import mongo_service

OUTPUT_HDFS_PATH = "/crime/processed/integrated_master.csv"


def run_multi_source_integration() -> Dict[str, Any]:
    """Execute complete multi-source integration pipeline."""
    # 1. Load Source A: Datacenter CSV
    datacenter_csv = PROJECT_ROOT / "dataset" / "crime_records.csv"
    if not datacenter_csv.exists():
        raise FileNotFoundError(f"Missing datacenter dataset: {datacenter_csv}")

    df_csv = pd.read_csv(datacenter_csv)
    df_csv["data_source"] = "datacenter_historical_csv"
    df_csv["verified_flag"] = True

    # 2. Load Source B: SQL Relational Area & Police Station Reference
    conn = init_sql_database()
    df_areas = pd.read_sql_query("SELECT area_id, district_name, population_estimate FROM area_reference", conn)
    conn.close()

    # Join district_name if not already present
    if "district_name" not in df_csv.columns:
        df_csv = df_csv.merge(df_areas, on="area_id", how="left")
    else:
        df_csv = df_csv.merge(df_areas[["area_id", "population_estimate"]], on="area_id", how="left")

    # 3. Load Source C: MongoDB Citizen Complaints
    complaints = mongo_service.get_complaints(limit=100000)
    complaints_data = []
    for c in complaints:
        # Standardize fields to match crime schema
        c_date = c.get("incident_date", "")
        c_time = c.get("incident_time", "12:00")
        c_dt = f"{c_date} {c_time}:00" if c_date else str(c.get("submitted_at", ""))

        complaints_data.append({
            "crime_id": c.get("complaint_id", ""),
            "case_number": f"CMP-{c.get('complaint_id', '')}",
            "crime_datetime": c_dt,
            "crime_year": int(c_date.split("-")[0]) if "-" in str(c_date) else 2025,
            "crime_month": int(c_date.split("-")[1]) if "-" in str(c_date) and len(c_date.split("-")) > 1 else 1,
            "crime_day": int(c_date.split("-")[2]) if "-" in str(c_date) and len(c_date.split("-")) > 2 else 1,
            "day_of_week": datetime.strptime(c_date, "%Y-%m-%d").strftime("%A") if c_date and len(c_date) == 10 else "Unknown",
            "hour_of_day": int(c_time.split(":")[0]) if ":" in str(c_time) else 12,
            "crime_type": c.get("complaint_category", "Theft"),
            "description": c.get("description", ""),
            "location_type": "Public Street",
            "area_id": c.get("area_id", "A001"),
            "area_name": c.get("area_name", "Central"),
            "district_name": "Central District",
            "latitude": float(c.get("latitude", 13.0827)),
            "longitude": float(c.get("longitude", 80.2707)),
            "arrest_flag": 0,
            "domestic_flag": 0,
            "case_status": c.get("complaint_status", "Citizen Report"),
            "data_source": "mongodb_citizen_complaints",
            "verified_flag": False,
            "population_estimate": 185000
        })

    df_mongo = pd.DataFrame(complaints_data)

    # 4. Schema harmonization and Concatenation
    canonical_columns = [
        "crime_id", "case_number", "crime_datetime", "crime_year", "crime_month", "crime_day",
        "day_of_week", "hour_of_day", "crime_type", "description", "location_type",
        "area_id", "area_name", "district_name", "latitude", "longitude",
        "arrest_flag", "domestic_flag", "case_status", "data_source", "verified_flag", "population_estimate"
    ]

    for col in canonical_columns:
        if col not in df_csv.columns:
            df_csv[col] = None
        if not df_mongo.empty and col not in df_mongo.columns:
            df_mongo[col] = None

    df_combined = pd.concat([df_csv[canonical_columns], df_mongo[canonical_columns]], ignore_index=True)
    raw_total = len(df_combined)

    # 5. Deduplication
    # Deduplicate exact case numbers
    df_dedup = df_combined.drop_duplicates(subset=["case_number"], keep="first")
    # Fuzzy duplicate removal: duplicate incident reported with same (area_id, crime_type, crime_datetime)
    df_dedup = df_dedup.drop_duplicates(subset=["area_id", "crime_type", "crime_datetime"], keep="first")
    duplicates_removed = raw_total - len(df_dedup)

    # 6. Save unified dataset to HDFS
    temp_master = PROJECT_ROOT / "reports_out" / "integrated_master.csv"
    df_dedup.to_csv(temp_master, index=False)
    hdfs_res = hdfs_manager.put_file(temp_master, OUTPUT_HDFS_PATH)

    # Summary metrics by data source
    source_breakdown = df_dedup["data_source"].value_counts().to_dict()
    status_breakdown = df_dedup["case_status"].value_counts().to_dict()

    return {
        "status": "success",
        "operation": "multi_source_data_integration",
        "raw_records_imported": raw_total,
        "duplicates_removed": duplicates_removed,
        "clean_integrated_records": len(df_dedup),
        "source_breakdown": source_breakdown,
        "status_breakdown": status_breakdown,
        "hdfs_destination": OUTPUT_HDFS_PATH,
        "local_mirror": str(temp_master),
        "execution_timestamp": datetime.utcnow().isoformat() + "Z",
        "details": hdfs_res
    }


if __name__ == "__main__":
    print("[*] Executing Multi-Source Data Integration & Deduplication...")
    res = run_multi_source_integration()
    print(f"[+] Total Clean Integrated Records: {res['clean_integrated_records']}")
    print(f"[+] Duplicates Removed: {res['duplicates_removed']}")
    print(f"[+] Provenance Breakdown: {res['source_breakdown']}")
