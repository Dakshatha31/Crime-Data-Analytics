"""
MongoDB NoSQL Service.
Satisfies Requirement 3: Storage / Process the data in NoSQL using MongoDB.
Supports real MongoDB Server (mongodb://localhost:27017/) with automatic fallback
to durable MongoMock + JSON persistence when MongoDB service is not started.
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_CSV = PROJECT_ROOT / "dataset" / "complaints_mongodb_seed.csv"
BACKUP_JSON_STORE = PROJECT_ROOT / "dataset" / "mongodb_store.json"

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = "crime_db"
COLLECTION_NAME = "complaints"


class MongoDBService:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.is_real_mongo = False
        self._init_connection()
        self._seed_if_empty()

    def _init_connection(self):
        """Attempt to connect to real MongoDB; fallback to mongomock if unavailable."""
        try:
            import pymongo
            real_client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=1000)
            real_client.server_info()  # Will trigger exception if not reachable
            self.client = real_client
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]
            self.is_real_mongo = True
        except Exception:
            # Fallback to mongomock
            import mongomock
            self.client = mongomock.MongoClient()
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]
            self.is_real_mongo = False
            self._load_from_json_backup()

    def _load_from_json_backup(self):
        """Load persisted documents into mongomock if backup json exists."""
        if BACKUP_JSON_STORE.exists():
            try:
                docs = json.loads(BACKUP_JSON_STORE.read_text(encoding="utf-8"))
                if docs:
                    self.collection.insert_many(docs)
            except Exception:
                pass

    def _save_to_json_backup(self):
        """Persist mongomock documents to disk so they survive restarts."""
        if not self.is_real_mongo:
            docs = list(self.collection.find({}, {"_id": 0}))
            BACKUP_JSON_STORE.write_text(json.dumps(docs, indent=2, default=str), encoding="utf-8")

    def _seed_if_empty(self):
        """Seed initial 500 synthetic complaints from complaints_mongodb_seed.csv."""
        if self.collection.count_documents({}) == 0 and SEED_CSV.exists():
            df = pd.read_csv(SEED_CSV)
            docs = df.to_dict(orient="records")
            # Format and enrich with timestamp and coordinates if missing
            area_coords = {
                "A001": (13.0827, 80.2707, "Central"),
                "A002": (13.115, 80.287, "North"),
                "A003": (12.9716, 80.2206, "South"),
                "A004": (13.05, 80.3, "East"),
                "A005": (13.075, 80.18, "West"),
                "A006": (13.105, 80.295, "Harbour"),
                "A007": (13.01, 80.19, "Industrial"),
                "A008": (13.01, 80.235, "University"),
                "A009": (13.09, 80.25, "Market"),
                "A010": (12.95, 80.16, "Suburban"),
            }
            for d in docs:
                aid = str(d.get("area_id", "A001"))
                coords = area_coords.get(aid, (13.08, 80.27, "Central"))
                d["latitude"] = coords[0]
                d["longitude"] = coords[1]
                d["verified_record"] = False
                d["storage_tier"] = "nosql_mongodb"
                if "created_at" not in d:
                    d["created_at"] = str(d.get("submitted_at", datetime.utcnow().isoformat()))

            self.collection.insert_many(docs)
            self._save_to_json_backup()

    def generate_reference_number(self) -> str:
        """Generate unique complaint reference code: CMP-YYYYMMDD-XXXX."""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        suffix = uuid.uuid4().hex[:4].upper()
        return f"CMP-{date_str}-{suffix}"

    def insert_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Feature 2: Add a new complaint.
        Stores new submissions in MongoDB and provides a complaint reference number.
        Keeps submitted complaints separate from verified historical police records.
        """
        ref_id = complaint_data.get("complaint_id") or self.generate_reference_number()
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        doc = {
            "complaint_id": ref_id,
            "incident_date": complaint_data.get("incident_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "incident_time": complaint_data.get("incident_time", datetime.utcnow().strftime("%H:%M")),
            "complaint_category": complaint_data.get("crime_type") or complaint_data.get("complaint_category", "General"),
            "area_id": complaint_data.get("area_id", "A001"),
            "area_name": complaint_data.get("area_name") or complaint_data.get("area", "Central"),
            "latitude": float(complaint_data.get("latitude", 13.0827)),
            "longitude": float(complaint_data.get("longitude", 80.2707)),
            "description": complaint_data.get("description", "").strip(),
            "complaint_status": "Under Review",
            "submission_channel": complaint_data.get("submission_channel", "Web Portal"),
            "submitted_at": now_str,
            "verified_record": False,  # Explicitly kept separate from official historical records
            "data_source": "citizen_mongodb_submission",
            "storage_tier": "nosql_mongodb"
        }

        self.collection.insert_one(doc)
        self._save_to_json_backup()

        # Clean copy for API response
        clean_doc = {k: v for k, v in doc.items() if k != "_id"}
        return clean_doc

    def get_complaints(self, limit: int = 50, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Retrieve recent complaint documents."""
        q = filter_dict or {}
        docs = list(self.collection.find(q, {"_id": 0}).sort("submitted_at", -1).limit(limit))
        return docs

    def count_complaints(self) -> int:
        """Count total complaint documents in MongoDB."""
        return self.collection.count_documents({})

    def get_stats(self) -> Dict[str, Any]:
        """Aggregation metrics for complaint categories and statuses."""
        total = self.count_complaints()
        # Category breakdown
        pipeline_cat = [
            {"$group": {"_id": "$complaint_category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = list(self.collection.aggregate(pipeline_cat))

        # Status breakdown
        pipeline_stat = [
            {"$group": {"_id": "$complaint_status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        statuses = list(self.collection.aggregate(pipeline_stat))

        return {
            "total_complaints": total,
            "is_real_mongo": self.is_real_mongo,
            "backend": "Real MongoDB Server" if self.is_real_mongo else "Embedded NoSQL (MongoMock + JSON)",
            "categories": [{"category": c["_id"], "count": c["count"]} for c in categories if c["_id"]],
            "statuses": [{"status": s["_id"], "count": s["count"]} for s in statuses if s["_id"]]
        }


# Global singleton
mongo_service = MongoDBService()
