-- Example relational tables for a SQL-to-HDFS export demonstration
CREATE DATABASE IF NOT EXISTS crime_project;
USE crime_project;

CREATE TABLE area_reference (
  area_id VARCHAR(10) PRIMARY KEY,
  area_name VARCHAR(80),
  district_name VARCHAR(80),
  center_latitude DECIMAL(9,6),
  center_longitude DECIMAL(9,6),
  population_estimate INT,
  population_year INT
);

CREATE TABLE police_stations (
  station_id VARCHAR(10) PRIMARY KEY,
  station_name VARCHAR(100),
  area_id VARCHAR(10),
  latitude DECIMAL(9,6),
  longitude DECIMAL(9,6),
  contact_number VARCHAR(20)
);

-- Load the matching CSV files using your SQL tool's CSV import function.
-- Export/query these tables to CSV, then upload CSV files to HDFS with hdfs dfs -put.
