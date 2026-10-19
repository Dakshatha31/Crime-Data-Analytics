-- =========================================================================
-- clean_crimes.pig: Pig Latin Script for Structured Data Cleaning & Normalization
-- =========================================================================

-- Load raw crime records from HDFS raw directory
raw_crimes = LOAD '/crime/raw/datacenter/crime_records.csv' USING PigStorage(',') AS (
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

-- Filter out corrupt rows, header lines, and invalid coordinate ranges
valid_crimes = FILTER raw_crimes BY
    crime_id IS NOT NULL AND
    crime_id != 'crime_id' AND
    crime_type IS NOT NULL AND
    area_id IS NOT NULL AND
    latitude >= 12.0 AND latitude <= 14.5 AND
    longitude >= 79.5 AND longitude <= 81.5;

-- Standardize and normalize textual fields
normalized_crimes = FOREACH valid_crimes GENERATE
    TRIM(crime_id) AS crime_id,
    TRIM(case_number) AS case_number,
    TRIM(crime_datetime) AS crime_datetime,
    crime_year,
    crime_month,
    crime_day,
    TRIM(day_of_week) AS day_of_week,
    hour_of_day,
    UPPER(TRIM(crime_type)) AS crime_type,
    TRIM(description) AS description,
    TRIM(location_type) AS location_type,
    TRIM(area_id) AS area_id,
    TRIM(area_name) AS area_name,
    latitude,
    longitude,
    arrest_flag,
    domestic_flag,
    TRIM(case_status) AS case_status,
    'pig_cleaned_pipeline' AS data_source;

-- Store cleaned records into HDFS processed location
STORE normalized_crimes INTO '/crime/processed/cleaned_pig' USING PigStorage(',');
