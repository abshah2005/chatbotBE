from memory import MongoDBManager
from pymongo import ASCENDING, DESCENDING

def create_indexes():
    """Create MongoDB indexes for optimal performance"""
    try:
        database = MongoDBManager.get_database()
        
        # Indexes for chat_sessions collection
        chat_sessions = database["chat_sessions"]
        
        # Compound index for session-based queries
        chat_sessions.create_index([
            ("SessionId", ASCENDING),
            ("CreatedAt", ASCENDING)
        ])
        
        # TTL index for automatic cleanup (optional - 90 days retention)
        chat_sessions.create_index(
            [("CreatedAt", ASCENDING)],
            expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
        )
        
        # Index for sessions_metadata collection
        sessions_metadata = database["sessions_metadata"]
        
        sessions_metadata.create_index([
            ("session_id", ASCENDING)
        ], unique=True)
        
        sessions_metadata.create_index([
            ("updated_at", DESCENDING)
        ])
        
        print("✅ MongoDB indexes created successfully")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")

if __name__ == "__main__":
    create_indexes()