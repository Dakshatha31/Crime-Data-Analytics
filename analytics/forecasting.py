"""
Crime Trend Forecasting Engine.
Satisfies Feature 9: Estimate future aggregate crime counts by area and crime category
using historical trends. Treats predictions as estimates rather than forecasts of individual behavior.
Feds directly from historical Hive-style monthly aggregates.
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager


class CrimeForecastEngine:
    def __init__(self):
        pass

    def forecast_trends(self, area_id: Optional[str] = None, crime_type: Optional[str] = None, horizon_months: int = 6) -> Dict[str, Any]:
        """
        Estimate future aggregate crime counts using Double Exponential Smoothing (Holt's Linear Trend)
        with seasonal monthly index adjustments.
        """
        cleaned_path = hdfs_manager._resolve_local_path("/crime/processed/cleaned_pig/cleaned_crimes.csv")
        if not cleaned_path.exists():
            cleaned_path = PROJECT_ROOT / "dataset" / "crime_records.csv"

        df = pd.read_csv(cleaned_path)

        # Apply area or crime type filters if specified
        scope_desc = "City-wide Total"
        if area_id and area_id != "ALL":
            df = df[df["area_id"] == area_id]
            scope_desc = f"Area {area_id}"
        if crime_type and crime_type.upper() != "ALL":
            df = df[df["crime_type"].str.upper() == crime_type.upper()]
            scope_desc += f" - {crime_type.upper()}"

        # Aggregate monthly counts
        monthly = df.groupby(["crime_year", "crime_month"]).size().reset_index(name="count")
        monthly = monthly.sort_values(by=["crime_year", "crime_month"])

        if len(monthly) < 12:
            return {
                "status": "warning",
                "message": "Insufficient historical points for seasonal projection (minimum 12 months needed)."
            }

        counts = monthly["count"].values.astype(float)
        years = monthly["crime_year"].values
        months = monthly["crime_month"].values

        historical_points = []
        for y, m, c in zip(years, months, counts):
            historical_points.append({
                "period": f"{int(y)}-{int(m):02d}",
                "count": int(c),
                "is_forecast": False
            })

        # Calculate seasonal indices (12 months)
        overall_mean = np.mean(counts)
        monthly["month_idx"] = monthly["crime_month"]
        seasonal_means = monthly.groupby("month_idx")["count"].mean()
        seasonal_indices = {m: (seasonal_means.get(m, overall_mean) / overall_mean) if overall_mean > 0 else 1.0 for m in range(1, 13)}

        # Deseasonalize series
        deseasonalized = [c / seasonal_indices.get(m, 1.0) for c, m in zip(counts, months)]

        # Holt's Linear Exponential Smoothing (Level and Trend)
        alpha = 0.35  # Level smoothing
        beta = 0.20   # Trend smoothing

        level = deseasonalized[0]
        trend = deseasonalized[1] - deseasonalized[0] if len(deseasonalized) > 1 else 0

        for val in deseasonalized[1:]:
            last_level = level
            level = alpha * val + (1 - alpha) * (level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend

        # Generate future forecasts
        last_year = int(years[-1])
        last_month = int(months[-1])

        forecast_points = []
        std_err = float(np.std(counts[-12:])) * 0.15

        for step in range(1, horizon_months + 1):
            future_month = ((last_month + step - 1) % 12) + 1
            year_advance = (last_month + step - 1) // 12
            future_year = last_year + year_advance

            base_pred = (level + step * trend) * seasonal_indices.get(future_month, 1.0)
            base_pred = max(5.0, base_pred)  # Non-negative lower threshold

            margin = std_err * np.sqrt(step)
            lower_bound = max(0.0, round(base_pred - 1.645 * margin, 1))
            upper_bound = round(base_pred + 1.645 * margin, 1)

            forecast_points.append({
                "period": f"{future_year}-{future_month:02d}",
                "predicted_count": round(base_pred, 1),
                "lower_bound_80pct": lower_bound,
                "upper_bound_80pct": upper_bound,
                "is_forecast": True
            })

        return {
            "status": "success",
            "scope": scope_desc,
            "horizon_months": horizon_months,
            "historical_months_count": len(historical_points),
            "historical_data": historical_points[-24:],  # Last 24 months for chart
            "forecast_data": forecast_points,
            "model_metadata": {
                "algorithm": "Holt-Winters Double Exponential Smoothing with Multiplicative Seasonality",
                "alpha_level_factor": alpha,
                "beta_trend_factor": beta,
                "estimated_trend_direction": "Upward" if trend > 0.5 else ("Downward" if trend < -0.5 else "Stable")
            },
            "disclaimer": "DISCLAIMER: These figures are aggregate mathematical projections derived from historical volume patterns. They are statistical estimates designed for resource planning and research, NOT individual behavioral predictions."
        }


# Global singleton
crime_forecast_engine = CrimeForecastEngine()

if __name__ == "__main__":
    res = crime_forecast_engine.forecast_trends()
    print("Forecast scope:", res["scope"])
    print("Trend direction:", res["model_metadata"]["estimated_trend_direction"])
    print("Next projected month:", res["forecast_data"][0])
