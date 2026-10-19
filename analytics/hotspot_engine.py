"""
Crime Hotspot Detection & Mapping Engine.
Satisfies Feature 5: Identify areas with high historical crime counts, rank them,
and display them on a map. Compare hotspots by crime type and time period.
Backed by Pig and Hive aggregations.
"""
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager

AREA_REF_CSV = PROJECT_ROOT / "dataset" / "area_reference_sql_export.csv"


class HotspotEngine:
    def __init__(self):
        self.area_reference = {}
        self._load_area_reference()

    def _load_area_reference(self):
        if AREA_REF_CSV.exists():
            df_areas = pd.read_csv(AREA_REF_CSV)
            for _, r in df_areas.iterrows():
                self.area_reference[r["area_id"]] = {
                    "area_id": r["area_id"],
                    "area_name": r["area_name"],
                    "district_name": r["district_name"],
                    "center_lat": float(r["center_latitude"]),
                    "center_lng": float(r["center_longitude"]),
                    "population": int(r["population_estimate"])
                }

    def get_hotspots(self, crime_type: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Compute hotspots ranked by crime count, filtered by crime type and year.
        Returns map circles with coordinates, radius, risk tier, and category distribution.
        """
        cleaned_path = hdfs_manager._resolve_local_path("/crime/processed/cleaned_pig/cleaned_crimes.csv")
        if not cleaned_path.exists():
            cleaned_path = PROJECT_ROOT / "dataset" / "crime_records.csv"

        df = pd.read_csv(cleaned_path)

        # Filters
        if crime_type and crime_type.upper() != "ALL":
            df = df[df["crime_type"].str.upper() == crime_type.upper()]
        if year and str(year) != "ALL":
            df = df[df["crime_year"] == int(year)]

        total_crimes_in_scope = len(df)
        if total_crimes_in_scope == 0:
            return {
                "status": "success",
                "total_crimes": 0,
                "hotspots": [],
                "summary": "No incidents match the selected filter."
            }

        # Area aggregation
        area_group = df.groupby(["area_id", "area_name"]).agg(
            incident_count=("crime_id", "count"),
            arrests=("arrest_flag", "sum"),
            avg_lat=("latitude", "mean"),
            avg_lng=("longitude", "mean")
        ).reset_index()

        area_group = area_group.sort_values(by="incident_count", ascending=False)
        max_count = area_group["incident_count"].max() if not area_group.empty else 1

        hotspots_list = []
        for rank, (_, row) in enumerate(area_group.iterrows(), start=1):
            aid = row["area_id"]
            ref = self.area_reference.get(aid, {})
            count = int(row["incident_count"])
            arrests = int(row["arrests"])
            arrest_rate = round((arrests / count) * 100.0, 1) if count > 0 else 0.0

            # Find top crime type in this area
            sub_df = df[df["area_id"] == aid]
            top_type = sub_df["crime_type"].value_counts().index[0] if not sub_df.empty else "N/A"
            top_type_count = int(sub_df["crime_type"].value_counts().iloc[0]) if not sub_df.empty else 0

            # Proportional radius for map circle (meters): 400m to 1200m
            circle_radius = int(450 + (count / max_count) * 850)

            # Risk classification
            if count >= max_count * 0.75:
                risk_tier = "High Hotspot"
                color = "#ef4444"  # Red
                fill_color = "#f87171"
            elif count >= max_count * 0.45:
                risk_tier = "Moderate Hotspot"
                color = "#f59e0b"  # Amber
                fill_color = "#fbbf24"
            else:
                risk_tier = "Low Hotspot"
                color = "#10b981"  # Emerald
                fill_color = "#34d399"

            lat = float(row["avg_lat"]) if pd.notnull(row["avg_lat"]) else ref.get("center_lat", 13.08)
            lng = float(row["avg_lng"]) if pd.notnull(row["avg_lng"]) else ref.get("center_lng", 80.27)

            hotspots_list.append({
                "rank": rank,
                "area_id": aid,
                "area_name": row["area_name"],
                "district_name": ref.get("district_name", "Metropolitan"),
                "latitude": round(lat, 5),
                "longitude": round(lng, 5),
                "circle_radius_meters": circle_radius,
                "incident_count": count,
                "percentage_of_total": round((count / total_crimes_in_scope) * 100.0, 1),
                "arrest_rate_pct": arrest_rate,
                "top_crime_type": top_type,
                "top_crime_type_count": top_type_count,
                "risk_tier": risk_tier,
                "color": color,
                "fill_color": fill_color,
                "population": ref.get("population", 150000)
            })

        return {
            "status": "success",
            "filter_crime_type": crime_type or "ALL",
            "filter_year": year or "ALL",
            "total_crimes_in_scope": total_crimes_in_scope,
            "hotspot_count": len(hotspots_list),
            "hotspots": hotspots_list
        }


# Global singleton
hotspot_engine = HotspotEngine()

if __name__ == "__main__":
    res = hotspot_engine.get_hotspots()
    print(f"Computed {res['hotspot_count']} hotspots across {res['total_crimes_in_scope']} crimes.")
    print("Top 3 Hotspots:")
    for h in res["hotspots"][:3]:
        print(f"Rank {h['rank']}: {h['area_name']} - {h['incident_count']} incidents ({h['risk_tier']})")
