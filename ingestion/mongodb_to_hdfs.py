"""
MongoDB to HDFS Batch Ingestion.
Satisfies Requirement 3 & Feature 2:
Exports MongoDB complaint documents to HDFS and vice-versa.
"""
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager
from nosql.mongo_service import mongo_service

HDFS_MONGO_DIR = "/crime/raw/mongodb"


def export_mongodb_to_hdfs() -> Dict[str, Any]:
    """Batch export all MongoDB complaints to HDFS in JSONL and CSV formats."""
    complaints = mongo_service.get_complaints(limit=100000)
    total_docs = len(complaints)

    if not complaints:
        return {
            "status": "warning",
            "message": "No complaints in MongoDB to export",
            "total_records": 0
        }

    hdfs_manager.mkdir(HDFS_MONGO_DIR)

    # 1. Export as JSON Lines
    temp_jsonl = PROJECT_ROOT / "reports_out" / "complaints_export.jsonl"
    with open(temp_jsonl, "w", encoding="utf-8") as f:
        for doc in complaints:
            f.write(json.dumps(doc, default=str) + "\n")

    put_jsonl = hdfs_manager.put_file(temp_jsonl, f"{HDFS_MONGO_DIR}/complaints_export.jsonl")

    # 2. Export as CSV
    df = pd.DataFrame(complaints)
    temp_csv = PROJECT_ROOT / "reports_out" / "complaints_export.csv"
    df.to_csv(temp_csv, index=False)

    put_csv = hdfs_manager.put_file(temp_csv, f"{HDFS_MONGO_DIR}/complaints_export.csv")

    return {
        "status": "success",
        "operation": "mongodb_to_hdfs_export",
        "total_records": total_docs,
        "files_exported": [
            f"{HDFS_MONGO_DIR}/complaints_export.jsonl",
            f"{HDFS_MONGO_DIR}/complaints_export.csv"
        ],
        "details": {
            "jsonl": put_jsonl,
            "csv": put_csv
        }
    }


def import_hdfs_to_mongodb(hdfs_path: str = f"{HDFS_MONGO_DIR}/complaints_export.jsonl") -> Dict[str, Any]:
    """Ingest HDFS complaint records into MongoDB collection."""
    temp_local = PROJECT_ROOT / "reports_out" / "hdfs_import_complaints.jsonl"
    hdfs_manager.get_file(hdfs_path, temp_local)

    imported_count = 0
    with open(temp_local, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                mongo_service.collection.update_one(
                    {"complaint_id": doc["complaint_id"]},
                    {"$set": doc},
                    upsert=True
                )
                imported_count += 1

    mongo_service._save_to_json_backup()

    return {
        "status": "success",
        "operation": "hdfs_to_mongodb_import",
        "hdfs_source": hdfs_path,
        "records_imported": imported_count
    }


if __name__ == "__main__":
    print("[*] Exporting MongoDB complaints to HDFS...")
    res = export_mongodb_to_hdfs()
    print(f"[+] Exported {res['total_records']} complaint documents to HDFS.")
