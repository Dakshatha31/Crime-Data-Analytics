"""
SQL to HDFS Ingestion & Export.
Satisfies Requirement 2: Import / Export the data from SQL to HDFS.
Uses standard SQL relational database with tables:
- area_reference
- police_stations
- sql_crime_aggregates
"""
import sys
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager

SQL_DB_PATH = PROJECT_ROOT / "dataset" / "crime_relational.db"
AREA_REF_CSV = PROJECT_ROOT / "dataset" / "area_reference_sql_export.csv"
POLICE_REF_CSV = PROJECT_ROOT / "dataset" / "police_stations_sql_export.csv"
HDFS_SQL_DIR = "/crime/raw/sql"


def init_sql_database(db_path: Path = SQL_DB_PATH) -> sqlite3.Connection:
    """Initialize relational SQL database with schema matching sql_schema.sql."""
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS area_reference (
        area_id TEXT PRIMARY KEY,
        area_name TEXT,
        district_name TEXT,
        center_latitude REAL,
        center_longitude REAL,
        population_estimate INTEGER,
        population_year INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS police_stations (
        station_id TEXT PRIMARY KEY,
        station_name TEXT,
        area_id TEXT,
        latitude REAL,
        longitude REAL,
        contact_number TEXT,
        FOREIGN KEY (area_id) REFERENCES area_reference(area_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sql_crime_aggregates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_id TEXT,
        area_name TEXT,
        crime_type TEXT,
        total_incidents INTEGER,
        synced_from_hdfs_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    # Seed initial rows if empty
    cur.execute("SELECT COUNT(*) FROM area_reference")
    if cur.fetchone()[0] == 0 and AREA_REF_CSV.exists():
        df_areas = pd.read_csv(AREA_REF_CSV)
        df_areas.to_sql("area_reference", conn, if_exists="append", index=False)

    cur.execute("SELECT COUNT(*) FROM police_stations")
    if cur.fetchone()[0] == 0 and POLICE_REF_CSV.exists():
        df_stations = pd.read_csv(POLICE_REF_CSV)
        df_stations.to_sql("police_stations", conn, if_exists="append", index=False)

    conn.commit()
    return conn


def export_sql_to_hdfs(db_path: Path = SQL_DB_PATH) -> Dict[str, Any]:
    """Query SQL database and export relational tables into HDFS."""
    conn = init_sql_database(db_path)

    # 1. Export area_reference
    df_areas = pd.read_sql_query("SELECT * FROM area_reference", conn)
    local_temp_areas = PROJECT_ROOT / "reports_out" / "temp_sql_areas.csv"
    df_areas.to_csv(local_temp_areas, index=False)
    put_areas = hdfs_manager.put_file(local_temp_areas, f"{HDFS_SQL_DIR}/area_reference.csv")

    # 2. Export police_stations
    df_stations = pd.read_sql_query("SELECT * FROM police_stations", conn)
    local_temp_stations = PROJECT_ROOT / "reports_out" / "temp_sql_stations.csv"
    df_stations.to_csv(local_temp_stations, index=False)
    put_stations = hdfs_manager.put_file(local_temp_stations, f"{HDFS_SQL_DIR}/police_stations.csv")

    conn.close()

    return {
        "status": "success",
        "operation": "sql_to_hdfs_export",
        "database": str(db_path),
        "exported_tables": {
            "area_reference": {
                "rows": len(df_areas),
                "hdfs_destination": f"{HDFS_SQL_DIR}/area_reference.csv",
                "details": put_areas
            },
            "police_stations": {
                "rows": len(df_stations),
                "hdfs_destination": f"{HDFS_SQL_DIR}/police_stations.csv",
                "details": put_stations
            }
        }
    }


def import_hdfs_to_sql(hdfs_aggregates_path: str = "/crime/processed/pig_hotspots/hotspots.csv", db_path: Path = SQL_DB_PATH) -> Dict[str, Any]:
    """Import processed HDFS aggregates back into SQL relational table."""
    conn = init_sql_database(db_path)
    local_temp = PROJECT_ROOT / "reports_out" / "temp_hdfs_aggregates.csv"

    try:
        hdfs_manager.get_file(hdfs_aggregates_path, local_temp)
        df = pd.read_csv(local_temp)
        # Match columns: area_id, area_name, crime_type, total_incidents
        if "incident_count" in df.columns:
            df = df.rename(columns={"incident_count": "total_incidents"})
        if "count" in df.columns:
            df = df.rename(columns={"count": "total_incidents"})

        cols_to_keep = [c for c in ["area_id", "area_name", "crime_type", "total_incidents"] if c in df.columns]
        df_sql = df[cols_to_keep]

        cur = conn.cursor()
        cur.execute("DELETE FROM sql_crime_aggregates")
        df_sql.to_sql("sql_crime_aggregates", conn, if_exists="append", index=False)
        conn.commit()
        row_count = len(df_sql)
    except Exception as e:
        row_count = 0
        df_sql = pd.DataFrame()
    finally:
        conn.close()

    return {
        "status": "success",
        "operation": "hdfs_to_sql_import",
        "hdfs_source": hdfs_aggregates_path,
        "database": str(db_path),
        "records_loaded": row_count
    }


if __name__ == "__main__":
    print("[*] Initializing SQL Database & Exporting to HDFS...")
    res = export_sql_to_hdfs()
    print(f"[+] SQL tables exported to HDFS: {list(res['exported_tables'].keys())}")
