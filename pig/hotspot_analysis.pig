-- =========================================================================
-- hotspot_analysis.pig: Pig Latin Hotspot Grouping & Crime Ranking
-- =========================================================================

cleaned_crimes = LOAD '/crime/processed/cleaned_pig' USING PigStorage(',') AS (
    crime_id:chararray,
    case_number:chararray,
    crime_datetime:chararray,
    crime_year:int,
    crime_month:int,
    crime_day:int,
    day_of_week:chararray,
    hour_of_day:int,
    crime_type:chararray,
    description:chararray,
    location_type:chararray,
    area_id:chararray,
    area_name:chararray,
    latitude:double,
    longitude:double,
    arrest_flag:int,
    domestic_flag:int,
    case_status:chararray,
    data_source:chararray
);

-- Group by Area and Crime Type
grouped_by_area_type = GROUP cleaned_crimes BY (area_id, area_name, crime_type);

-- Generate Count Aggregates
hotspot_counts = FOREACH grouped_by_area_type GENERATE
    group.area_id AS area_id,
    group.area_name AS area_name,
    group.crime_type AS crime_type,
    COUNT(cleaned_crimes) AS incident_count,
    AVG(cleaned_crimes.latitude) AS avg_latitude,
    AVG(cleaned_crimes.longitude) AS avg_longitude;

-- Order by Incident Count Descending
ordered_hotspots = ORDER hotspot_counts BY incident_count DESC;

-- Store hotspot ranking into HDFS
STORE ordered_hotspots INTO '/crime/processed/pig_hotspots' USING PigStorage(',');
