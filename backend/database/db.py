import os
import json
import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NeuralWatchDB")

# Environment configurations
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "neuralwatch"
FALLBACK_FILE = os.path.join(os.path.dirname(__file__), "db_fallback.json")

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_mongodb_active = False
        self._connect()

    def _connect(self):
        try:
            logger.info(f"Attempting to connect to MongoDB at {MONGO_URI}...")
            # Set a 3-second timeout for server selection
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
            # Trigger connection check
            self.client.admin.command('ping')
            self.db = self.client[DB_NAME]
            self.is_mongodb_active = True
            logger.info("Successfully connected to MongoDB.")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"MongoDB connection failed: {e}. Falling back to local JSON database storage.")
            self.is_mongodb_active = False
            self._init_fallback_db()

    def _init_fallback_db(self):
        if not os.path.exists(FALLBACK_FILE):
            with open(FALLBACK_FILE, "w") as f:
                json.dump({"sessions": [], "alerts": []}, f, indent=2)
            logger.info(f"Created fallback JSON database at {FALLBACK_FILE}")

    def _read_fallback(self):
        self._init_fallback_db()
        try:
            with open(FALLBACK_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading fallback DB: {e}")
            return {"sessions": [], "alerts": []}

    def _write_fallback(self, data):
        try:
            with open(FALLBACK_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing fallback DB: {e}")

    def save_session(self, session_data):
        """Save a completed driver monitoring session."""
        session_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        if self.is_mongodb_active:
            try:
                result = self.db.sessions.insert_one(session_data)
                logger.info(f"Saved session to MongoDB. ID: {result.inserted_id}")
                return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Failed to write to MongoDB: {e}. Writing to fallback.")
        
        # Fallback implementation
        db_data = self._read_fallback()
        session_data["_id"] = len(db_data["sessions"]) + 1
        db_data["sessions"].append(session_data)
        self._write_fallback(db_data)
        logger.info("Saved session to local fallback database.")
        return str(session_data["_id"])

    def save_alert(self, alert_event):
        """Save a drowsiness alert event."""
        alert_event["timestamp"] = datetime.utcnow().isoformat() + "Z"
        if self.is_mongodb_active:
            try:
                result = self.db.alerts.insert_one(alert_event)
                logger.info(f"Saved alert to MongoDB. ID: {result.inserted_id}")
                return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Failed to write to MongoDB: {e}. Writing to fallback.")
        
        # Fallback implementation
        db_data = self._read_fallback()
        alert_event["_id"] = len(db_data["alerts"]) + 1
        db_data["alerts"].append(alert_event)
        self._write_fallback(db_data)
        logger.info("Saved alert log to local fallback database.")
        return str(alert_event["_id"])

    def get_recent_alerts(self, limit=20):
        """Fetch the most recent alerts."""
        if self.is_mongodb_active:
            try:
                cursor = self.db.alerts.find().sort("timestamp", -1).limit(limit)
                alerts = []
                for a in cursor:
                    a["id"] = str(a.pop("_id"))
                    alerts.append(a)
                return alerts
            except Exception as e:
                logger.error(f"MongoDB read error: {e}. Reading from fallback.")
        
        # Fallback implementation
        db_data = self._read_fallback()
        sorted_alerts = sorted(db_data["alerts"], key=lambda x: x.get("timestamp", ""), reverse=True)
        return sorted_alerts[:limit]

    def get_sessions(self, limit=10):
        """Fetch the most recent driver sessions."""
        if self.is_mongodb_active:
            try:
                cursor = self.db.sessions.find().sort("timestamp", -1).limit(limit)
                sessions = []
                for s in cursor:
                    s["id"] = str(s.pop("_id"))
                    sessions.append(s)
                return sessions
            except Exception as e:
                logger.error(f"MongoDB read error: {e}. Reading from fallback.")
        
        # Fallback implementation
        db_data = self._read_fallback()
        sorted_sessions = sorted(db_data["sessions"], key=lambda x: x.get("timestamp", ""), reverse=True)
        return sorted_sessions[:limit]

# Singleton instance
db_instance = Database()
