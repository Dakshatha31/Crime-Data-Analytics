"""
Datacenter to HDFS Ingestion & Export.
Satisfies Requirement 1: Import / Export the data from datacenter to HDFS.
"""
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager

DATACENTER_RAW_CSV = PROJECT_ROOT / "dataset" / "crime_records.csv"
HDFS_TARGET_DIR = "/crime/raw/datacenter"
HDFS_TARGET_FILE = "/crime/raw/datacenter/crime_records.csv"


def import_datacenter_to_hdfs(src_path: Path = DATACENTER_RAW_CSV) -> Dict[str, Any]:
    """Import raw crime records from Datacenter storage into HDFS."""
    if not src_path.exists():
        raise FileNotFoundError(f"Datacenter source file not found: {src_path}")

    # Inspect dataset metrics
    df = pd.read_csv(src_path)
    total_records = len(df)
    columns = list(df.columns)
    unique_areas = df["area_name"].nunique() if "area_name" in df.columns else 0
    unique_types = df["crime_type"].nunique() if "crime_type" in df.columns else 0

    hdfs_manager.mkdir(HDFS_TARGET_DIR)
    put_res = hdfs_manager.put_file(src_path, HDFS_TARGET_FILE)

    return {
        "status": "success",
        "operation": "datacenter_import_to_hdfs",
        "source_path": str(src_path),
        "hdfs_destination": HDFS_TARGET_FILE,
        "total_records": total_records,
        "columns": columns,
        "unique_areas": unique_areas,
        "unique_crime_types": unique_types,
        "file_size_bytes": src_path.stat().st_size,
        "details": put_res
    }


def export_hdfs_to_datacenter(hdfs_src: str = HDFS_TARGET_FILE, export_dest: Path = None) -> Dict[str, Any]:
    """Export HDFS dataset back to Datacenter storage."""
    if export_dest is None:
        export_dest = PROJECT_ROOT / "dataset" / "datacenter_export_records.csv"

    get_res = hdfs_manager.get_file(hdfs_src, export_dest)
    df = pd.read_csv(export_dest)

    return {
        "status": "success",
        "operation": "hdfs_export_to_datacenter",
        "hdfs_source": hdfs_src,
        "datacenter_destination": str(export_dest),
        "total_exported_records": len(df),
        "file_size_bytes": export_dest.stat().st_size,
        "details": get_res
    }


if __name__ == "__main__":
    print("[*] Running Datacenter -> HDFS Import...")
    res = import_datacenter_to_hdfs()
    print(f"[+] Successfully imported {res['total_records']} records to {res['hdfs_destination']}")

    print("[*] Running HDFS -> Datacenter Export...")
    exp = export_hdfs_to_datacenter()
    print(f"[+] Successfully exported {exp['total_exported_records']} records to {exp['datacenter_destination']}")
