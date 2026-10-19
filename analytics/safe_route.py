"""
Safe-Route Suggestion Engine.
Satisfies Feature 1: Suggest a route between two locations using historical crime counts,
time of day, and road network graph. Compare multiple candidate routes using a crime-exposure score.
Presents result as a risk-aware suggestion, not a guarantee of safety.
"""
import sys
import json
import networkx as nx
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager

ROAD_NETWORK_CSV = PROJECT_ROOT / "dataset" / "road_network.csv"
AREA_REF_CSV = PROJECT_ROOT / "dataset" / "area_reference_sql_export.csv"


class SafeRouteEngine:
    def __init__(self):
        self.graph = nx.Graph()
        self.area_metadata = {}
        self._build_graph()

    def _build_graph(self):
        """Construct NetworkX graph from road network and area references."""
        # 1. Load Areas
        if AREA_REF_CSV.exists():
            df_areas = pd.read_csv(AREA_REF_CSV)
            for _, row in df_areas.iterrows():
                self.area_metadata[row["area_id"]] = {
                    "area_id": row["area_id"],
                    "area_name": row["area_name"],
                    "district_name": row["district_name"],
                    "lat": float(row["center_latitude"]),
                    "lng": float(row["center_longitude"])
                }

        # 2. Load Road Network
        if ROAD_NETWORK_CSV.exists():
            df_roads = pd.read_csv(ROAD_NETWORK_CSV)
            for _, row in df_roads.iterrows():
                u = row["from_area_id"]
                v = row["to_area_id"]
                dist = float(row["distance_km"])
                self.graph.add_edge(u, v, weight=dist, distance_km=dist, road_name=row["road_name"], road_type=row["road_type"])

    def _get_area_crime_counts(self, hour_filter: int = None) -> Dict[str, int]:
        """Compute crime counts per area from HDFS cleaned records, optionally filtered by hour."""
        cleaned_path = hdfs_manager._resolve_local_path("/crime/processed/cleaned_pig/cleaned_crimes.csv")
        if not cleaned_path.exists():
            cleaned_path = PROJECT_ROOT / "dataset" / "crime_records.csv"

        df = pd.read_csv(cleaned_path)
        if hour_filter is not None and "hour_of_day" in df.columns:
            # Emphasize crimes within +/- 2 hours of target time
            window = [(hour_filter + i) % 24 for i in range(-2, 3)]
            df = df[df["hour_of_day"].isin(window)]

        counts = df.groupby("area_id").size().to_dict()
        return counts

    def suggest_routes(self, from_area_id: str, to_area_id: str, hour_of_day: int = 20) -> Dict[str, Any]:
        """
        Suggest and compare candidate routes between origin and destination.
        Returns ranked routes with distance, crime exposure, score, and polylines.
        """
        if from_area_id not in self.graph or to_area_id not in self.graph:
            return {
                "status": "error",
                "message": f"Areas {from_area_id} or {to_area_id} not found in road network graph."
            }

        area_crimes = self._get_area_crime_counts(hour_filter=hour_of_day)

        # Find simple paths up to 5 hops
        try:
            candidate_paths = list(nx.all_simple_paths(self.graph, source=from_area_id, target=to_area_id, cutoff=5))
        except Exception:
            candidate_paths = []

        if not candidate_paths:
            # Fallback to shortest path
            try:
                shortest = nx.shortest_path(self.graph, source=from_area_id, target=to_area_id, weight="weight")
                candidate_paths = [shortest]
            except Exception:
                return {
                    "status": "error",
                    "message": "No navigable route found between selected areas."
                }

        # Keep up to 4 distinct routes
        candidate_paths = candidate_paths[:4]

        routes_evaluated = []
        for idx, path in enumerate(candidate_paths):
            total_dist = 0.0
            road_segments = []
            polyline_coords = []

            for i in range(len(path)):
                aid = path[i]
                meta = self.area_metadata.get(aid, {"lat": 13.08, "lng": 80.27, "area_name": aid})
                polyline_coords.append([meta["lat"], meta["lng"]])

                if i < len(path) - 1:
                    nxt = path[i + 1]
                    edge = self.graph.get_edge_data(aid, nxt) or {}
                    dist = edge.get("distance_km", 3.0)
                    total_dist += dist
                    road_segments.append(f"{edge.get('road_name', 'Connector')} ({dist} km)")

            # Crime exposure along the path
            exposure = sum(area_crimes.get(aid, 0) for aid in path)

            # Nighttime risk multiplier (higher risk at late hours: 22:00 to 04:00)
            time_weight = 1.35 if (hour_of_day >= 22 or hour_of_day <= 4) else 1.0
            adjusted_exposure = round(exposure * time_weight)

            # Combined risk-aware score (exposure + distance penalty)
            combined_score = round(adjusted_exposure + (18 * total_dist), 1)

            area_names = [self.area_metadata.get(aid, {}).get("area_name", aid) for aid in path]

            routes_evaluated.append({
                "route_id": f"Route {chr(65 + idx)}",
                "path_area_ids": path,
                "path_area_names": area_names,
                "area_sequence": " -> ".join(area_names),
                "distance_km": round(total_dist, 2),
                "historical_crime_exposure": exposure,
                "time_adjusted_exposure": adjusted_exposure,
                "risk_score": combined_score,
                "road_segments": road_segments,
                "polyline_coordinates": polyline_coords
            })

        # Rank by risk score ascending (Lowest risk = Recommended)
        routes_evaluated.sort(key=lambda r: r["risk_score"])

        # Tag recommended route and alternative routes
        for i, r in enumerate(routes_evaluated):
            if i == 0:
                r["recommendation"] = "Recommended (Lowest Crime-Exposure)"
                r["color"] = "#10b981"  # Emerald green
                r["badge"] = "Safest Suggestion"
            elif i == 1:
                r["recommendation"] = "Alternative Route (Moderate Exposure)"
                r["color"] = "#f59e0b"  # Amber
                r["badge"] = "Alternative 1"
            else:
                r["recommendation"] = "High Exposure / Longer Route"
                r["color"] = "#ef4444"  # Coral / Red
                r["badge"] = f"Alternative {i}"

        return {
            "status": "success",
            "from_area": self.area_metadata.get(from_area_id, {}),
            "to_area": self.area_metadata.get(to_area_id, {}),
            "time_of_day_hour": hour_of_day,
            "routes_count": len(routes_evaluated),
            "routes": routes_evaluated,
            "disclaimer": "CRITICAL NOTICE: Routes are calculated using historical statistical crime totals and road network distances. This feature offers a risk-aware suggestion for coursework and situational awareness, NOT an official guarantee of personal safety."
        }


# Global singleton
safe_route_engine = SafeRouteEngine()

if __name__ == "__main__":
    res = safe_route_engine.suggest_routes("A001", "A003", hour_of_day=22)
    print(f"Computed {res['routes_count']} candidate routes between {res['from_area']['area_name']} and {res['to_area']['area_name']}")
    for r in res["routes"]:
        print(f"[{r['badge']}] {r['route_id']}: Score={r['risk_score']}, Dist={r['distance_km']}km, Path={r['area_sequence']}")
