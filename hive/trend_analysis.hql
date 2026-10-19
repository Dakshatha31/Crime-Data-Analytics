-- =========================================================================
-- trend_analysis.hql: HiveQL Time-Based Grouping, Trend & Growth Queries
-- =========================================================================

USE crime_analytics;

-- Query 1: Monthly Crime Trend with Percentage Changes
SELECT 
    crime_year,
    crime_month,
    CONCAT(crime_year, '-', LPAD(crime_month, 2, '0')) AS year_month,
    COUNT(*) AS total_crimes,
    COUNT(CASE WHEN arrest_flag = 1 THEN 1 END) AS arrest_count,
    ROUND(COUNT(CASE WHEN arrest_flag = 1 THEN 1 END) * 100.0 / COUNT(*), 2) AS arrest_rate_pct
FROM crimes
GROUP BY crime_year, crime_month
ORDER BY crime_year, crime_month;

-- Query 2: Yearly Crime Totals with Year-over-Year Growth
SELECT 
    crime_year,
    COUNT(*) AS annual_crimes,
    LAG(COUNT(*), 1) OVER (ORDER BY crime_year) AS prev_year_crimes,
    ROUND((COUNT(*) - LAG(COUNT(*), 1) OVER (ORDER BY crime_year)) * 100.0 / 
          LAG(COUNT(*), 1) OVER (ORDER BY crime_year), 2) AS yoy_growth_pct
FROM crimes
GROUP BY crime_year
ORDER BY crime_year;

-- Query 3: Quarterly Distribution
SELECT 
    crime_year,
    CASE 
        WHEN crime_month BETWEEN 1 AND 3 THEN 'Q1'
        WHEN crime_month BETWEEN 4 AND 6 THEN 'Q2'
        WHEN crime_month BETWEEN 7 AND 9 THEN 'Q3'
        ELSE 'Q4' 
    END AS quarter,
    COUNT(*) AS quarterly_crimes
FROM crimes
GROUP BY crime_year, 
    CASE 
        WHEN crime_month BETWEEN 1 AND 3 THEN 'Q1'
        WHEN crime_month BETWEEN 4 AND 6 THEN 'Q2'
        WHEN crime_month BETWEEN 7 AND 9 THEN 'Q3'
        ELSE 'Q4' 
    END
ORDER BY crime_year, quarter;
