
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import uuid
from chain import chatbot
from dotenv import load_dotenv
from memory import MongoDBManager, get_session_history
import os

app = Flask(__name__)
CORS(app)  

load_dotenv()

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        client = MongoDBManager.get_client()
        client.admin.command('ping')
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 503

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Main chat endpoint with context and session management"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        session_id = data.get("session_id")
        user_input = data.get("input")
        context = data.get("context", "")
        
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        if not user_input:
            return jsonify({"error": "input is required"}), 400
        
        import asyncio
        
        # Invoke the chatbot
        response = asyncio.run(
            chatbot.ainvoke(
                {"input": user_input, "context": context},
                config={"configurable": {"session_id": session_id}}
            )
        )
        
        return jsonify({
            "response": response.content,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/sessions", methods=["GET"])
def list_sessions():
    """List all chat sessions with metadata"""
    try:
        database = MongoDBManager.get_database()
        collection = database["chat_sessions"]
        
        # Get unique sessions
        sessions = collection.distinct("SessionId")
        
        # Get metadata for each session
        sessions_with_metadata = []
        for session_id in sessions:
            # Get the last message timestamp
            last_message = collection.find_one(
                {"SessionId": session_id},
                sort=[("CreatedAt", -1)]
            )
            
            # Count messages in session
            message_count = collection.count_documents({"SessionId": session_id})
            
            sessions_with_metadata.append({
                "session_id": session_id,
                "message_count": message_count,
                "last_activity": last_message.get("CreatedAt") if last_message else None,
                "created_at": last_message.get("CreatedAt") if last_message else None
            })
        
        return jsonify({
            "sessions": sessions_with_metadata,
            "count": len(sessions_with_metadata)
        })
        
    except Exception as e:
        app.logger.error(f"List sessions error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/history/<session_id>", methods=["GET"])
def get_chat_history(session_id):
    """Get complete chat history for a session using LangChain's methods"""
    try:
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        
        # Create MongoDBChatMessageHistory instance
        from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
        
        history = MongoDBChatMessageHistory(
            session_id=session_id,
            connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            database_name=os.getenv("MONGODB_DATABASE", "chat_history_db"),
            collection_name="chat_sessions",
        )
        
        # Get messages using the built-in method
        messages = history.messages
        
        # Format the messages
        formatted_messages = []
        for i, msg in enumerate(messages):
            formatted_messages.append({
                "id": f"{session_id}_{i}",
                "type": msg.type,
                "content": msg.content,
                "timestamp": None,  # LangChain doesn't store timestamps by default
                "additional_kwargs": msg.additional_kwargs
            })
        
        return jsonify({
            "session_id": session_id,
            "messages": formatted_messages,
            "count": len(formatted_messages)
        })
        
    except Exception as e:
        app.logger.error(f"Get history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/history/<session_id>/clear", methods=["DELETE"])
def clear_chat_history(session_id):
    """Clear chat history for a session"""
    try:
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        
        database = MongoDBManager.get_database()
        collection = database["chat_sessions"]
        
        # Delete all messages for this session
        result = collection.delete_many({"SessionId": session_id})
        
        return jsonify({
            "session_id": session_id,
            "deleted_count": result.deleted_count,
            "message": "Chat history cleared successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Clear history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/session/new", methods=["POST"])
def create_new_session():
    """Create a new chat session"""
    try:
        data = request.get_json() or {}
        session_name = data.get("session_name", "New Chat")
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Create initial session record
        database = MongoDBManager.get_database()
        collection = database["sessions_metadata"]
        
        session_metadata = {
            "session_id": session_id,
            "session_name": session_name,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "message_count": 0
        }
        
        collection.insert_one(session_metadata)
        
        return jsonify({
            "session_id": session_id,
            "session_name": session_name,
            "created_at": session_metadata["created_at"].isoformat(),
            "message": "New session created successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Create session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/sessions/metadata", methods=["GET"])
def get_sessions_metadata():
    """Get metadata for all sessions"""
    try:
        database = MongoDBManager.get_database()
        collection = database["sessions_metadata"]
        
        sessions = list(collection.find(
            {},
            sort=[("updated_at", -1)]
        ))
        
        # Convert ObjectId to string and datetime to ISO format
        for session in sessions:
            session["_id"] = str(session["_id"])
            session["created_at"] = session["created_at"].isoformat() if session.get("created_at") else None
            session["updated_at"] = session["updated_at"].isoformat() if session.get("updated_at") else None
        
        return jsonify({
            "sessions": sessions,
            "count": len(sessions)
        })
        
    except Exception as e:
        app.logger.error(f"Get sessions metadata error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)