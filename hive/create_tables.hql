-- =========================================================================
-- create_tables.hql: Apache Hive Schema DDL for Crime Analytics Warehouse
-- =========================================================================

CREATE DATABASE IF NOT EXISTS crime_analytics;
USE crime_analytics;

-- External Table: Cleaned Crimes (Backed by Pig Output on HDFS)
CREATE EXTERNAL TABLE IF NOT EXISTS crime_analytics.crimes (
    crime_id STRING,
    case_number STRING,
    crime_datetime STRING,
    crime_year INT,
    crime_month INT,
    crime_day INT,
    day_of_week STRING,
    hour_of_day INT,
    crime_type STRING,
    description STRING,
    location_type STRING,
    area_id STRING,
    area_name STRING,
    latitude DOUBLE,
    longitude DOUBLE,
    arrest_flag INT,
    domestic_flag INT,
    case_status STRING,
    data_source STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/crime/processed/cleaned_pig';

-- External Table: Area Reference (Backed by SQL export on HDFS)
CREATE EXTERNAL TABLE IF NOT EXISTS crime_analytics.area_reference (
    area_id STRING,
    area_name STRING,
    district_name STRING,
    center_latitude DOUBLE,
    center_longitude DOUBLE,
    population_estimate INT,
    population_year INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/crime/raw/sql/area_reference';

-- External Table: Police Stations (Backed by SQL export on HDFS)
CREATE EXTERNAL TABLE IF NOT EXISTS crime_analytics.police_stations (
    station_id STRING,
    station_name STRING,
    area_id STRING,
    latitude DOUBLE,
    longitude DOUBLE,
    contact_number STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/crime/raw/sql/police_stations';
