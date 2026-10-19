# Crime Data Analytics — Big Data Platform

A comprehensive Big Data Analytics and Public Safety Intelligence System built with **Apache Hadoop (HDFS & YARN)**, **MongoDB NoSQL**, **Apache Pig**, **Apache Hive**, and **FastAPI**. Features an interactive, modern **Light Theme Web Application** with real-time geospatial crime hotspots on the landing page map.

---

## 🌟 Key Architecture & Big Data Working Mapping

| Working | Component | Implementation in Codebase | HDFS / Storage Path |
| :--- | :--- | :--- | :--- |
| **1. Datacenter to HDFS** | Ingestion & Export | [`ingestion/datacenter_to_hdfs.py`](file:///d:/projects/Crime_Analytics_BDC/ingestion/datacenter_to_hdfs.py) | `/crime/raw/datacenter/crime_records.csv` |
| **2. SQL to HDFS** | Relational Ingestion & Reverse Sync | [`ingestion/sql_to_hdfs.py`](file:///d:/projects/Crime_Analytics_BDC/ingestion/sql_to_hdfs.py) | `/crime/raw/sql/area_reference.csv`<br>`/crime/raw/sql/police_stations.csv` |
| **3. MongoDB NoSQL** | Storage & Document Processing | [`nosql/mongo_service.py`](file:///d:/projects/Crime_Analytics_BDC/nosql/mongo_service.py)<br>[`ingestion/mongodb_to_hdfs.py`](file:///d:/projects/Crime_Analytics_BDC/ingestion/mongodb_to_hdfs.py) | `crime_db.complaints`<br>`/crime/raw/mongodb/complaints_export.jsonl` |
| **4. Apache Pig Analysis** | Structured Data Cleaning & Hotspot Grouping | [`pig/clean_crimes.pig`](file:///d:/projects/Crime_Analytics_BDC/pig/clean_crimes.pig)<br>[`pig/hotspot_analysis.pig`](file:///d:/projects/Crime_Analytics_BDC/pig/hotspot_analysis.pig)<br>[`pig/hourly_patterns.pig`](file:///d:/projects/Crime_Analytics_BDC/pig/hourly_patterns.pig)<br>[`pig/pig_runner.py`](file:///d:/projects/Crime_Analytics_BDC/pig/pig_runner.py) | `/crime/processed/cleaned_pig/`<br>`/crime/processed/pig_hotspots/`<br>`/crime/processed/pig_time_patterns/` |
| **5. Apache Hive Analysis** | External Tables, Joins & Metastore Queries | [`hive/create_tables.hql`](file:///d:/projects/Crime_Analytics_BDC/hive/create_tables.hql)<br>[`hive/trend_analysis.hql`](file:///d:/projects/Crime_Analytics_BDC/hive/trend_analysis.hql)<br>[`hive/area_comparison.hql`](file:///d:/projects/Crime_Analytics_BDC/hive/area_comparison.hql)<br>[`hive/hive_runner.py`](file:///d:/projects/Crime_Analytics_BDC/hive/hive_runner.py) | `crime_analytics.crimes`<br>`/crime/warehouse/hive_tables/` |

---

## 🚀 10 Implemented Features

### 1. Safe-Route Suggestion
- **Engine**: [`analytics/safe_route.py`](file:///d:/projects/Crime_Analytics_BDC/analytics/safe_route.py)
- **Datasets**: `road_network.csv` + HDFS historical incident aggregates + `area_reference_sql_export.csv`.
- **Capability**: Builds a NetworkX graph across 10 areas and 24 road links. Evaluates up to 4 candidate paths, factoring in road distance and historical area crime exposure weighted by time-of-day risk (e.g. higher penalty during late night 22:00–04:00).
- **Presentation**: Visualizes colored polylines directly on the Leaflet map (Emerald Green for safest, Amber/Red for alternatives) with clear risk-aware disclaimers.

### 2. Add a New Complaint
- **Engine**: [`nosql/mongo_service.py`](file:///d:/projects/Crime_Analytics_BDC/nosql/mongo_service.py)
- **Storage**: MongoDB collection `crime_db.complaints`.
- **Capability**: Citizens submit incident details (date, time, category, area, description, location coordinates). Generates unique reference code (`CMP-YYYYMMDD-XXXX`). Keeps submitted complaints strictly separate from verified police records. Supports one-click batch export to HDFS.

### 3. Report Generation (CSV & PDF)
- **Engine**: [`analytics/report_generator.py`](file:///d:/projects/Crime_Analytics_BDC/analytics/report_generator.py)
- **Capability**: Filtered by date range, crime category, district/area, and year. Computes totals, arrest clearance rates, category distributions, and top areas.
- **Export Formats**: One-click **CSV** download and formal **PDF** generated using ReportLab with tables, key metrics, and timestamping.

### 4. Crime Trend Analysis
- **Engine**: [`analytics/area_comparisons.py`](file:///d:/projects/Crime_Analytics_BDC/analytics/area_comparisons.py) & [`hive/trend_analysis.hql`](file:///d:/projects/Crime_Analytics_BDC/hive/trend_analysis.hql)
- **Capability**: Computes monthly, quarterly, and yearly incident trends with Month-over-Month (MoM) and Year-over-Year (YoY) percentage changes. Visualized with interactive Chart.js multi-axis graphs.

### 5. Crime Hotspot Detection (Landing Page Map)
- **Engine**: [`analytics/hotspot_engine.py`](file:///d:/projects/Crime_Analytics_BDC/analytics/hotspot_engine.py) & [`pig/hotspot_analysis.pig`](file:///d:/projects/Crime_Analytics_BDC/pig/hotspot_analysis.pig)
- **Capability**: Placed prominently on the landing page! Renders interactive map circle overlays with proportional radii and risk tiers (High Red, Moderate Amber, Low Green). Filterable by crime category (Theft, Assault, etc.) and year (2021–2025). Displays ranked hotspot leaderboard.

### 6. Crime Time-Pattern Analysis
- **Engine**: [`analytics/time_patterns.py`](file:///d:/projects/Crime_Analytics_BDC/analytics/time_patterns.py)
- **Capability**: Analyzes timestamps to extract 24-hour diurnal curves (0:00–23:00), day-of-week distributions (Monday–Sunday), weekday vs weekend averages, and a Day × Time Block heatmap matrix.

### 7. Area-wise and Crime-Type Comparison
- **Engine**: [`analytics/area_comparisons.py`](file:///d:/projects/Crime_Analytics_BDC/analytics/area_comparisons.py) & [`hive/area_comparison.hql`](file:///d:/projects/Crime_Analytics_BDC/hive/area_comparison.hql)
- **Capability**: Performs distributed joins between incident records, area population (`area_population.csv`), and police stations (`police_stations_sql_export.csv`) to compute population-adjusted crime rates (per 100k residents).

### 8. Multi-Source Data Integration & Deduplication
- **Engine**: [`ingestion/multi_source_integration.py`](file:///d:/projects/Crime_Analytics_BDC/ingestion/multi_source_integration.py)
- **Capability**: Combines Datacenter historical CSVs (20,000 records), SQL relational reference tables, and MongoDB citizen complaints into a unified analytical dataset in HDFS (`/crime/processed/integrated_master.csv`). Tracks data source provenance and eliminates duplicate records.

### 9. Crime Trend Forecasting
- **Engine**: [`analytics/forecasting.py`](file:///d:/projects/Crime_Analytics_BDC/analytics/forecasting.py)
- **Capability**: Statistical time series forecasting utilizing Holt-Winters Double Exponential Smoothing with Multiplicative Seasonality. Feeds on historical Hive aggregates and outputs 6-to-12 month forecasts with 80% confidence interval bands.

### 10. Data Volume and Scalability Benchmark
- **Engine**: [`analytics/benchmark_runner.py`](file:///d:/projects/Crime_Analytics_BDC/analytics/benchmark_runner.py)
- **Dataset**: `chicago_crimes_1m.csv` (1,000,000 records, ~199 MB).
- **Capability**: Benchmarks processing time across **100,000, 500,000, and 1,000,000 records**. Compares single-threaded sequential execution against parallel chunked MapReduce workflows, demonstrating 2.5x to 3.5x speedups and horizontal scalability.

---

## 🛠️ Setup & Execution Instructions

### Prerequisites
- **Python**: 3.10+ (Python 3.11 tested)
- **Java**: OpenJDK 1.8 (Java 8) configured at `C:\Java8`
- **Hadoop**: Apache Hadoop 3.3.6 (installed at `C:\hadoop-3.3.6` with `winutils.exe` and `hadoop.dll`)
- **MongoDB**: Runs with local MongoDB (`mongodb://localhost:27017/`) or automatically with embedded durable NoSQL (MongoMock + JSON persistence).

### Automated One-Click Setup (Windows PowerShell)
```powershell
cd d:\projects\Crime_Analytics_BDC
powershell -ExecutionPolicy Bypass -File scripts\setup_environment.ps1
```

### Manual Setup & Execution

1. **Install Python Libraries**:
   ```bash
   pip install pandas numpy networkx reportlab fastapi uvicorn pymongo mongomock scikit-learn
   ```

2. **Run End-to-End Big Data Pipelines**:
   ```bash
   python scripts/run_all_pipelines.py
   ```
   *Executes HDFS ingestion, SQL exports, Mongo seeding, multi-source deduplication, Pig Latin cleaning, and Hive warehouse queries.*

3. **Start the Web Application**:
   ```bash
   python scripts/start_server.py
   ```
   Open your browser at:
   - **Web UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - **Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

4. **Run Automated Test Suite**:
   ```bash
   python -m unittest tests/test_all_features.py
   ```
   *Runs 13 comprehensive unit and integration tests across all features and pipelines.*

---

## 📁 Repository Structure

```
d:\projects\Crime_Analytics_BDC\
├── dataset/                        # Datasets (20k synthetic, 1M Chicago, SQL exports, Mongo seed, road network)
├── hdfs_store/                     # Local HDFS namespace (/crime/raw/, /crime/processed/, /crime/warehouse/)
├── ingestion/                      # Ingestion & Export Pipelines
│   ├── hdfs_manager.py             # Unified HDFS CLI and storage bridge
│   ├── datacenter_to_hdfs.py       # Working 1: Datacenter <-> HDFS
│   ├── sql_to_hdfs.py              # Working 2: SQL <-> HDFS
│   ├── mongodb_to_hdfs.py          # Working 3: MongoDB <-> HDFS
│   └── multi_source_integration.py # Feature 8: Multi-source deduplication & master corpus
├── nosql/                          # MongoDB NoSQL Storage
│   └── mongo_service.py            # PyMongo service + complaint reference generator
├── pig/                            # Apache Pig Latin Scripts & Engine
│   ├── clean_crimes.pig            # Data cleaning & normalization
│   ├── hotspot_analysis.pig        # Hotspot grouping & ranking
│   ├── hourly_patterns.pig         # 24h & day-of-week time patterns
│   └── pig_runner.py               # Pig Latin execution runner
├── hive/                           # Apache Hive Schema & Queries
│   ├── create_tables.hql           # Hive external table definitions
│   ├── trend_analysis.hql          # Time-based grouping & YoY growth
│   ├── area_comparison.hql         # Distributed joins with area population
│   └── hive_runner.py              # Hive warehouse query runner
├── analytics/                      # Core Feature Analytics Engines
│   ├── safe_route.py               # Feature 1: Safe-route suggestion
│   ├── hotspot_engine.py           # Feature 5: Hotspot detection & circle markers
│   ├── time_patterns.py            # Feature 6: 24h diurnal & seasonal distributions
│   ├── area_comparisons.py         # Features 4 & 7: Area comparison & trends
│   ├── forecasting.py              # Feature 9: Holt-Winters forecasting
│   ├── benchmark_runner.py         # Feature 10: 100k, 500k, 1M scalability benchmark
│   └── report_generator.py         # Feature 3: CSV & ReportLab PDF generator
├── web/                            # Light Theme Web Application
│   ├── server.py                   # FastAPI REST API server
│   └── static/
│       ├── index.html              # Landing page with interactive map & feature tabs
│       ├── css/style.css           # Premium Light Theme design system
│       └── js/
│           ├── app.js              # Application state & event controller
│           ├── map.js              # Leaflet hotspot circles & route renderer
│           └── charts.js           # Chart.js visualization controller
├── tests/
│   └── test_all_features.py        # 13 automated unit tests
├── scripts/
│   ├── setup_environment.ps1       # Environment setup script
│   ├── run_all_pipelines.py        # Pipeline runner
│   └── start_server.py             # Server launcher
└── README.md                       # Comprehensive platform documentation
```

---

## ⚖️ Ethical & Educational Notice
- All records in the 20,000 synthetic dataset and MongoDB seed are generated for coursework demonstration.
- Safe route calculations and hotspot indicators represent historical statistical frequencies and are intended for situational awareness and research; they **do not constitute real-time guarantees of individual safety**.
