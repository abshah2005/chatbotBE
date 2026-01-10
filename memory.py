import os
from typing import Optional
from pymongo import MongoClient
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from dotenv import load_dotenv

load_dotenv()

class MongoDBManager:
    """Singleton MongoDB connection manager"""
    _client: Optional[MongoClient] = None
    _database = None
    
    @classmethod
    def get_client(cls):
        if cls._client is None:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            cls._client = MongoClient(
                mongodb_uri,
                maxPoolSize=100,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=30000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            try:
                cls._client.admin.command('ping')
                print("✅ MongoDB connection successful")
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
                raise
                
        return cls._client
    
    @classmethod
    def get_database(cls):
        if cls._database is None:
            db_name = os.getenv("MONGODB_DATABASE", "chat_history_db")
            cls._database = cls.get_client()[db_name]
        return cls._database
    
    @classmethod
    def close_connection(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None

def get_session_history(session_id: str) -> MongoDBChatMessageHistory:
    """
    Get or create chat history for a session from MongoDB
    
    Args:
        session_id: Unique identifier for the chat session
        
    Returns:
        MongoDBChatMessageHistory instance
    """
    try:
        database = MongoDBManager.get_database()
        
        # Create MongoDB chat message history
        return MongoDBChatMessageHistory(
            session_id=session_id,
            connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            database_name=os.getenv("MONGODB_DATABASE", "chat_history_db"),
            collection_name="chat_sessions",
        )
    except Exception as e:
        print(f"Error getting session history for {session_id}: {e}")
        # Fallback to in-memory if MongoDB fails
        from langchain_core.chat_history import InMemoryChatMessageHistory
        return InMemoryChatMessageHistory()