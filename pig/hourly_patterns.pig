-- =========================================================================
-- hourly_patterns.pig: Pig Latin Time-Pattern Aggregation (24-Hour & Days)
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

-- Group by Day of Week and Hour of Day
time_grouped = GROUP cleaned_crimes BY (day_of_week, hour_of_day);

-- Compute counts per time window
time_patterns = FOREACH time_grouped GENERATE
    group.day_of_week AS day_of_week,
    group.hour_of_day AS hour_of_day,
    COUNT(cleaned_crimes) AS crime_count;

-- Store time pattern output into HDFS
STORE time_patterns INTO '/crime/processed/pig_time_patterns' USING PigStorage(',');
