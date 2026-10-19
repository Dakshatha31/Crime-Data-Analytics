-- =========================================================================
-- area_comparison.hql: HiveQL Distributed Joins & Per-Capita Crime Analysis
-- =========================================================================

USE crime_analytics;

-- Query 1: Join Crimes with Area Reference & Population to calculate Per-Capita Crime Rate
SELECT 
    c.area_id,
    a.area_name,
    a.district_name,
    a.population_estimate,
    COUNT(c.crime_id) AS total_incidents,
    ROUND((COUNT(c.crime_id) * 100000.0) / a.population_estimate, 2) AS crime_rate_per_100k
FROM crimes c
JOIN area_reference a ON (c.area_id = a.area_id)
GROUP BY c.area_id, a.area_name, a.district_name, a.population_estimate
ORDER BY crime_rate_per_100k DESC;

-- Query 2: Area x Crime Type Pivot Breakdown
SELECT 
    c.area_name,
    c.crime_type,
    COUNT(*) AS incident_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY c.area_name), 2) AS pct_of_area_crime
FROM crimes c
GROUP BY c.area_name, c.crime_type
ORDER BY c.area_name, incident_count DESC;

-- Query 3: Police Station Load & Proximity Summary
SELECT 
    ps.station_id,
    ps.station_name,
    ps.contact_number,
    ar.area_name,
    COUNT(c.crime_id) AS recorded_area_incidents
FROM police_stations ps
JOIN area_reference ar ON (ps.area_id = ar.area_id)
LEFT JOIN crimes c ON (c.area_id = ar.area_id)
GROUP BY ps.station_id, ps.station_name, ps.contact_number, ar.area_name
ORDER BY recorded_area_incidents DESC;
