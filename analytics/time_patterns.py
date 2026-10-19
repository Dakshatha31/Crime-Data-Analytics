"""
Crime Time-Pattern Analysis Engine.
Satisfies Feature 6: Find the days of the week, months, and hours associated with
higher recorded crime counts using large-scale date/time aggregations.
"""
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager


class TimePatternEngine:
    def __init__(self):
        pass

    def get_time_patterns(self) -> Dict[str, Any]:
        """Aggregate crime distributions across hours, days of week, and months."""
        cleaned_path = hdfs_manager._resolve_local_path("/crime/processed/cleaned_pig/cleaned_crimes.csv")
        if not cleaned_path.exists():
            cleaned_path = PROJECT_ROOT / "dataset" / "crime_records.csv"

        df = pd.read_csv(cleaned_path)
        total_crimes = len(df)

        # 1. 24-Hour Diurnal Curve (0 to 23)
        hourly_counts = df.groupby("hour_of_day").size().to_dict()
        hourly_data = []
        for h in range(24):
            count = hourly_counts.get(h, 0)
            hourly_data.append({
                "hour": h,
                "label": f"{h:02d}:00",
                "count": count,
                "percentage": round((count / total_crimes) * 100.0, 2)
            })

        # Peak and lowest hours
        sorted_hours = sorted(hourly_data, key=lambda x: x["count"], reverse=True)
        peak_hours = sorted_hours[:3]
        lowest_hours = sorted_hours[-3:]

        # 2. Day of Week Distribution
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow_counts = df.groupby("day_of_week").size().to_dict()
        dow_data = []
        for d in day_order:
            count = dow_counts.get(d, 0)
            dow_data.append({
                "day": d,
                "count": count,
                "percentage": round((count / total_crimes) * 100.0, 2)
            })

        weekday_sum = sum(dow_counts.get(d, 0) for d in day_order[:5])
        weekend_sum = sum(dow_counts.get(d, 0) for d in day_order[5:])
        weekday_avg = round(weekday_sum / 5.0, 1)
        weekend_avg = round(weekend_sum / 2.0, 1)

        # 3. Monthly Seasonal Distribution (1 to 12)
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_counts = df.groupby("crime_month").size().to_dict()
        monthly_data = []
        for m in range(1, 13):
            count = month_counts.get(m, 0)
            monthly_data.append({
                "month_num": m,
                "month_name": month_names[m - 1],
                "count": count,
                "percentage": round((count / total_crimes) * 100.0, 2)
            })

        # 4. Day of Week x 4-Hour Time Blocks Heatmap Matrix
        time_blocks = [
            ("00:00-04:00", [0, 1, 2, 3]),
            ("04:00-08:00", [4, 5, 6, 7]),
            ("08:00-12:00", [8, 9, 10, 11]),
            ("12:00-16:00", [12, 13, 14, 15]),
            ("16:00-20:00", [16, 17, 18, 19]),
            ("20:00-24:00", [20, 21, 22, 23])
        ]

        heatmap_matrix = []
        for d in day_order:
            row = {"day": d}
            sub_d = df[df["day_of_week"] == d]
            for label, hours in time_blocks:
                cnt = int(sub_d[sub_d["hour_of_day"].isin(hours)].shape[0])
                row[label] = cnt
            heatmap_matrix.append(row)

        return {
            "status": "success",
            "total_records_analyzed": total_crimes,
            "hourly_distribution": hourly_data,
            "peak_risk_hours": peak_hours,
            "lowest_risk_hours": lowest_hours,
            "day_of_week_distribution": dow_data,
            "weekday_avg": weekday_avg,
            "weekend_avg": weekend_avg,
            "monthly_distribution": monthly_data,
            "heatmap_matrix": heatmap_matrix
        }


# Global singleton
time_pattern_engine = TimePatternEngine()

if __name__ == "__main__":
    res = time_pattern_engine.get_time_patterns()
    print("Peak risk hour:", res["peak_risk_hours"][0])
    print("Weekday avg:", res["weekday_avg"], "Weekend avg:", res["weekend_avg"])
