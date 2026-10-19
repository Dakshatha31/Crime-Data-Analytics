# Crime Data Analysis Project — Synthetic Datasets

All records in this package are SYNTHETIC and were generated for coursework/demo purposes.
They do not represent real crimes, real complainants, real police stations, or verified safety levels.
Coordinates are approximate mock points around Chennai-like locations and must not be interpreted as accurate real-world locations.

## Files
- crime_records.csv: 20,000 synthetic historical crime records (2021–2025), main HDFS/Hive/Pig dataset.
- area_reference_sql_export.csv: area reference table, sample SQL-to-HDFS export.
- police_stations_sql_export.csv: sample station reference table, sample SQL-to-HDFS export.
- complaints_mongodb_seed.csv: 500 synthetic complaint documents to seed MongoDB for demos.
- road_network.csv: synthetic graph edges connecting area IDs; prototype route analysis only.
- area_population.csv: synthetic population estimates for per-capita calculations.
- monthly_crime_aggregates.csv: derived monthly aggregates, useful for validation/demo (can also be recomputed in Hive/Pig).

## Suggested feature mapping
- HDFS: crime_records.csv, monthly_crime_aggregates.csv, SQL exports.
- Pig: cleaning, filtering, grouping, category/area totals.
- Hive: monthly trends, district comparisons, joins with area_population and station reference.
- MongoDB: complaints_mongodb_seed.csv documents and new complaint submissions.
- Safe route prototype: road_network.csv + area-level crime counts; use only as a teaching demo, not real safety advice.
- Report generation: Hive query results exported as CSV and converted to PDF by your app.
- Scale/performance test: use a larger dataset only if needed; don't simply duplicate rows without noting they are duplicates.

## Important limitations
- Synthetic dataset only. If you need real-world analysis, replace crime_records.csv with a government/open-data source.
- The case_status and arrest flags are simulated and should not be used for operational decisions.
- The complaint descriptions contain no personal information.
