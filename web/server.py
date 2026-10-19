"""
Crime Data Analytics — High-Performance FastAPI Server.
Exposes REST APIs for all 5 Big Data workings and all 10 features.
Serves the modern Light Theme Web UI.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.hdfs_manager import hdfs_manager
from ingestion.datacenter_to_hdfs import import_datacenter_to_hdfs, export_hdfs_to_datacenter
from ingestion.sql_to_hdfs import export_sql_to_hdfs, import_hdfs_to_sql
from ingestion.mongodb_to_hdfs import export_mongodb_to_hdfs, import_hdfs_to_mongodb
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

app = FastAPI(
    title="Crime Data Analytics",
    description="Big Data Crime Intelligence Platform with HDFS, Pig, Hive, MongoDB & Scalability Engine",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = PROJECT_ROOT / "web" / "static"


# -------------------------------------------------------------------------
# Request Models
# -------------------------------------------------------------------------
class ComplaintRequest(BaseModel):
    incident_date: str
    incident_time: str
    crime_type: str
    area_id: str
    area_name: str
    latitude: float
    longitude: float
    description: str
    submission_channel: Optional[str] = "Web Portal"


class HiveQueryRequest(BaseModel):
    query: str


class BenchmarkRequest(BaseModel):
    sample_size: int = 100000


# -------------------------------------------------------------------------
# System Overview API
# -------------------------------------------------------------------------
@app.get("/api/summary")
def get_system_summary():
    """System-level big data overview stats."""
    mongo_stats = mongo_service.get_stats()
    hdfs_files = hdfs_manager.list_dir("/crime")
    hotspots = hotspot_engine.get_hotspots()

    return {
        "status": "online",
        "title": "Crime Data Analytics Big Data Platform",
        "hdfs_files_count": len(hdfs_files),
        "total_historical_crimes": hotspots.get("total_crimes_in_scope", 20000),
        "active_hotspot_areas": hotspots.get("hotspot_count", 10),
        "mongodb_complaints": mongo_stats.get("total_complaints", 0),
        "mongodb_backend": mongo_stats.get("backend", "NoSQL"),
        "hadoop_available": hdfs_manager.hadoop_cli_available,
        "pig_engine": "Pig Relational Engine (Pig Latin 0.17.0)",
        "hive_engine": "Hive Warehouse Engine (HiveQL 3.1.3)",
        "yarn_benchmark_dataset": "chicago_crimes_1m.csv (1,000,000 records)"
    }


# -------------------------------------------------------------------------
# Feature 1: Safe-Route Suggestion
# -------------------------------------------------------------------------
@app.get("/api/safe-route")
def get_safe_route(from_area: str = "A001", to_area: str = "A003", hour: int = 20):
    return safe_route_engine.suggest_routes(from_area, to_area, hour_of_day=hour)


@app.get("/api/areas")
def get_areas_list():
    """List all known areas and centroids for selection."""
    return list(safe_route_engine.area_metadata.values())


# -------------------------------------------------------------------------
# Feature 2: Add New Complaint (MongoDB NoSQL)
# -------------------------------------------------------------------------
@app.post("/api/complaints")
def submit_complaint(complaint: ComplaintRequest):
    new_doc = mongo_service.insert_complaint(complaint.dict())
    return {
        "status": "success",
        "message": f"Complaint successfully recorded in MongoDB with Reference {new_doc['complaint_id']}",
        "complaint": new_doc
    }


@app.get("/api/complaints")
def list_complaints(limit: int = 50):
    docs = mongo_service.get_complaints(limit=limit)
    stats = mongo_service.get_stats()
    return {
        "status": "success",
        "total_complaints": stats["total_complaints"],
        "backend": stats["backend"],
        "complaints": docs
    }


@app.post("/api/complaints/sync-hdfs")
def sync_complaints_to_hdfs():
    return export_mongodb_to_hdfs()


# -------------------------------------------------------------------------
# Feature 3: Report Generation (CSV & PDF)
# -------------------------------------------------------------------------
@app.get("/api/reports/summary")
def get_report_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    crime_category: Optional[str] = None,
    area_name: Optional[str] = None,
    year: Optional[str] = None
):
    return report_generator.generate_report_summary(start_date, end_date, crime_category, area_name, year)


@app.get("/api/reports/download-csv")
def download_report_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    crime_category: Optional[str] = None,
    area_name: Optional[str] = None,
    year: Optional[str] = None
):
    file_path = report_generator.export_csv(start_date, end_date, crime_category, area_name, year)
    return FileResponse(file_path, media_type="text/csv", filename=file_path.name)


@app.get("/api/reports/download-pdf")
def download_report_pdf(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    crime_category: Optional[str] = None,
    area_name: Optional[str] = None,
    year: Optional[str] = None
):
    file_path = report_generator.export_pdf(start_date, end_date, crime_category, area_name, year)
    return FileResponse(file_path, media_type="application/pdf", filename=file_path.name)


# -------------------------------------------------------------------------
# Feature 4 & 7: Crime Trend Analysis & Area Comparisons
# -------------------------------------------------------------------------
@app.get("/api/trends")
def get_crime_trends():
    return area_comparison_engine.get_crime_trends()


@app.get("/api/area-comparison")
def get_area_comparison():
    return area_comparison_engine.compare_areas()


# -------------------------------------------------------------------------
# Feature 5: Crime Hotspot Detection
# -------------------------------------------------------------------------
@app.get("/api/hotspots")
def get_crime_hotspots(crime_type: Optional[str] = None, year: Optional[str] = None):
    return hotspot_engine.get_hotspots(crime_type=crime_type, year=year)


# -------------------------------------------------------------------------
# Feature 6: Crime Time-Pattern Analysis
# -------------------------------------------------------------------------
@app.get("/api/time-patterns")
def get_time_patterns():
    return time_pattern_engine.get_time_patterns()


# -------------------------------------------------------------------------
# Feature 8: Multi-Source Data Integration
# -------------------------------------------------------------------------
@app.post("/api/integration/run")
def trigger_multi_source_integration():
    return run_multi_source_integration()


# -------------------------------------------------------------------------
# Feature 9: Crime Trend Forecasting
# -------------------------------------------------------------------------
@app.get("/api/forecasting")
def get_trend_forecasting(area_id: Optional[str] = None, crime_type: Optional[str] = None, horizon: int = 6):
    return crime_forecast_engine.forecast_trends(area_id=area_id, crime_type=crime_type, horizon_months=horizon)


# -------------------------------------------------------------------------
# Feature 10: Data Volume & Scalability Benchmark
# -------------------------------------------------------------------------
@app.get("/api/benchmark")
def get_scalability_benchmark():
    return benchmark_engine.get_calibrated_benchmark_results()


@app.post("/api/benchmark/live")
def run_live_benchmark(req: BenchmarkRequest):
    return benchmark_engine.run_benchmark(sample_sizes=[req.sample_size])


# -------------------------------------------------------------------------
# Core Big Data Workings 1-5 (HDFS, SQL, Pig, Hive)
# -------------------------------------------------------------------------
@app.get("/api/hdfs/files")
def list_hdfs_files():
    return hdfs_manager.list_dir("/crime")


@app.get("/api/hdfs/cat")
def read_hdfs_file(path: str = "/crime/processed/pig_hotspots/part-r-00000", limit: int = 25):
    """Inspect and preview raw lines of an HDFS file (part-r-*, CSV, JSONL)."""
    local_p = hdfs_manager._resolve_local_path(path)
    lines = []
    if local_p.exists() and local_p.is_file():
        try:
            with open(local_p, "r", encoding="utf-8", errors="replace") as f:
                for _ in range(limit):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.rstrip("\r\n"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif shutil.which("wsl"):
        try:
            import subprocess
            wsl_cmd = f"export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64; export HADOOP_HOME=/opt/hadoop; /opt/hadoop/bin/hdfs dfs -cat {path} | head -n {limit}"
            res = subprocess.run(["wsl", "-e", "bash", "-c", wsl_cmd], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout:
                lines = [l for l in res.stdout.splitlines() if l.strip()]
        except Exception:
            pass

    if not lines and not (local_p.exists() and local_p.is_file()):
        raise HTTPException(status_code=404, detail=f"HDFS file not found: {path}")

    return {
        "status": "success",
        "hdfs_path": path,
        "total_lines_previewed": len(lines),
        "lines": lines,
        "preview_text": "\n".join(lines)
    }


@app.post("/api/ingestion/datacenter-to-hdfs")
def run_datacenter_to_hdfs():
    return import_datacenter_to_hdfs()


@app.post("/api/ingestion/sql-to-hdfs")
def run_sql_to_hdfs():
    return export_sql_to_hdfs()


@app.post("/api/ingestion/mongodb-to-hdfs")
def run_mongo_to_hdfs():
    return export_mongodb_to_hdfs()


@app.post("/api/pig/run-clean")
def run_pig_cleaning():
    return pig_runner.run_clean_crimes()


@app.post("/api/pig/run-hotspots")
def run_pig_hotspot_job():
    return pig_runner.run_hotspot_pig()


@app.post("/api/hive/monthly-trends")
def run_hive_monthly_job():
    return hive_runner.run_monthly_trends_hive()


@app.post("/api/hive/query")
def execute_hive_query(req: HiveQueryRequest):
    return hive_runner.execute_query(req.query)


# -------------------------------------------------------------------------
# Static File Mounts & Landing Page
# -------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)


if __name__ == "__main__":
    import uvicorn
    # Initialize basic datasets into HDFS and Hive on startup
    try:
        import_datacenter_to_hdfs()
        export_sql_to_hdfs()
        pig_runner.run_clean_crimes()
        hive_runner.sync_external_tables()
    except Exception as e:
        print(f"[!] Startup pipeline note: {e}")

    uvicorn.run("web.server:app", host="127.0.0.1", port=8000, reload=False)
