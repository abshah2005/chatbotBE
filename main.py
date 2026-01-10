
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from datetime import datetime
# import uuid
# from chain import chatbot
# import json
# from typing import Dict, Any, Optional
# from dotenv import load_dotenv
# from memory import MongoDBManager, get_session_history
# import os
# from context_manager import AdmissionContextManager

# # Initialize context manager
# context_manager = AdmissionContextManager()

# app = Flask(__name__)
# CORS(app)  

# load_dotenv()


# @app.route("/chat", methods=["POST"])
# def chat_endpoint():
#     """Main chat endpoint with admission context"""
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "No JSON data provided"}), 400
        
#         session_id = data.get("session_id")
#         user_input = data.get("input")
        
#         if not session_id:
#             return jsonify({"error": "session_id is required"}), 400
#         if not user_input:
#             return jsonify({"error": "input is required"}), 400
        
#         # Get user context
#         user_context = context_manager.get_user_context(session_id)
#         user_info = user_context.get("user_info", {})
        
#         # Extract admission data
#         admission_data = context_manager.admission_data
        
#         # Prepare context for LLM
#         context_text = json.dumps(admission_data, indent=2)[:4000]  # Limit context size
        
#         # Check if we need to ask for user information
#         if not user_info.get("intermediate_marks"):
#             # First message, ask for marks
#             if "marks" not in user_input.lower() and "percentage" not in user_input.lower():
#                 return jsonify({
#                     "response": "Welcome to University Admission Assistant! To give you personalized guidance, please provide your intermediate marks (percentage).",
#                     "session_id": session_id,
#                     "needs_info": "intermediate_marks",
#                     "timestamp": datetime.now().isoformat()
#                 })
        
#         # Extract information from user input
#         extracted_info = extract_user_info(user_input)
        
#         # Update user context with extracted info
#         for key, value in extracted_info.items():
#             if value:
#                 context_manager.update_user_info(session_id, key, value)
        
#         # Prepare LLM input with enhanced context
        
#         llm_input = {
#             "input": user_input,
#             "context": context_text,
#             "university_name": "Minhaj",  # Change this
#             "user_marks": user_info.get("intermediate_marks", "Not provided"),
#             "user_discipline": user_info.get("intermediate_discipline", "Not specified"),
#             "user_interest": user_info.get("interested_field", "Not specified"),
#             "user_preferences": json.dumps(user_info.get("preferences", {})),
#             "admission_status": f"Admission open until {admission_data['important_dates']['admission_end']}"
#         }
        
#         import asyncio
        
#         # Invoke the chatbot
#         response = asyncio.run(
#             chatbot.ainvoke(
#                 llm_input,
#                 config={"configurable": {"session_id": session_id}}
#             )
#         )
        
#         # Update metadata
#         update_session_metadata(session_id)
        
#         # Check if we need to ask for more info
#         follow_up = check_for_missing_info(user_info)
        
#         return jsonify({
#             "response": response.content,
#             "session_id": session_id,
#             "user_info": user_info,
#             "follow_up_question": follow_up,
#             "timestamp": datetime.now().isoformat()
#         })
        
#     except Exception as e:
#         app.logger.error(f"Chat error: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# def extract_user_info(user_input: str) -> Dict[str, Any]:
#     """Extract user information from input"""
#     extracted = {}
    
#     # Extract marks (simplified - use NLP for better extraction)
#     import re
    
#     # Look for percentage
#     marks_pattern = r'(\d{1,3})%\s*marks|\s*(\d{1,3})\s*percent'
#     marks_match = re.search(marks_pattern, user_input, re.IGNORECASE)
#     if marks_match:
#         extracted["intermediate_marks"] = marks_match.group(1) or marks_match.group(2)
    
#     # Extract discipline
#     disciplines = ["ICS", "FSC Pre-Engineering", "FSC Pre-Medical", "FA", "I.Com", "A-Levels"]
#     for discipline in disciplines:
#         if discipline.lower() in user_input.lower():
#             extracted["intermediate_discipline"] = discipline
#             break
    
#     # Extract interested field
#     fields = ["Computer Science", "Software Engineering", "PharmD", "DPT", "Engineering", "Medicine"]
#     for field in fields:
#         if field.lower() in user_input.lower():
#             extracted["interested_field"] = field
#             break
    
#     return extracted

# def check_for_missing_info(user_info: Dict[str, Any]) -> Optional[str]:
#     """Check if we need to ask for more information"""
#     if not user_info.get("intermediate_marks"):
#         return "What is your intermediate marks percentage?"
#     elif not user_info.get("intermediate_discipline"):
#         return "What was your intermediate discipline? (e.g., ICS, FSC Pre-Engineering, FSC Pre-Medical)"
#     elif not user_info.get("interested_field"):
#         return "Which field are you interested in? (e.g., Computer Science, Pharmacy, Medicine)"
    
#     return None

# def update_session_metadata(session_id: str):
#     """Update session metadata"""
#     database = MongoDBManager.get_database()
#     metadata_collection = database["sessions_metadata"]
    
#     metadata = metadata_collection.find_one({"session_id": session_id})
#     if not metadata:
#         metadata_collection.insert_one({
#             "session_id": session_id,
#             "session_name": f"Admission Query {session_id[:8]}",
#             "created_at": datetime.now(),
#             "updated_at": datetime.now(),
#             "message_count": 1,
#             "query_type": "admission"
#         })
#     else:
#         metadata_collection.update_one(
#             {"session_id": session_id},
#             {
#                 "$inc": {"message_count": 1},
#                 "$set": {"updated_at": datetime.now()}
#             }
#         )


# @app.route("/sessions", methods=["GET"])
# def list_sessions():
#     """List all chat sessions with metadata"""
#     try:
#         database = MongoDBManager.get_database()
#         collection = database["chat_sessions"]
        
#         # Get unique sessions
#         sessions = collection.distinct("SessionId")
        
#         # Get metadata for each session
#         sessions_with_metadata = []
#         for session_id in sessions:
#             # Get the last message timestamp
#             last_message = collection.find_one(
#                 {"SessionId": session_id},
#                 sort=[("CreatedAt", -1)]
#             )
            
#             # Count messages in session
#             message_count = collection.count_documents({"SessionId": session_id})
            
#             sessions_with_metadata.append({
#                 "session_id": session_id,
#                 "message_count": message_count,
#                 "last_activity": last_message.get("CreatedAt") if last_message else None,
#                 "created_at": last_message.get("CreatedAt") if last_message else None
#             })
        
#         return jsonify({
#             "sessions": sessions_with_metadata,
#             "count": len(sessions_with_metadata)
#         })
        
#     except Exception as e:
#         app.logger.error(f"List sessions error: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# @app.route("/history/<session_id>", methods=["GET"])
# def get_chat_history(session_id):
#     """Get complete chat history for a session using LangChain's methods"""
#     try:
#         if not session_id:
#             return jsonify({"error": "session_id is required"}), 400
        
#         # Create MongoDBChatMessageHistory instance
#         from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
        
#         history = MongoDBChatMessageHistory(
#             session_id=session_id,
#             connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
#             database_name=os.getenv("MONGODB_DATABASE", "chat_history_db"),
#             collection_name="chat_sessions",
#         )
        
#         # Get messages using the built-in method
#         messages = history.messages
        
#         # Format the messages
#         formatted_messages = []
#         for i, msg in enumerate(messages):
#             formatted_messages.append({
#                 "id": f"{session_id}_{i}",
#                 "type": msg.type,
#                 "content": msg.content,
#                 "timestamp": None,  # LangChain doesn't store timestamps by default
#                 "additional_kwargs": msg.additional_kwargs
#             })
        
#         return jsonify({
#             "session_id": session_id,
#             "messages": formatted_messages,
#             "count": len(formatted_messages)
#         })
        
#     except Exception as e:
#         app.logger.error(f"Get history error: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route("/history/<session_id>/clear", methods=["DELETE"])
# def clear_chat_history(session_id):
#     """Clear chat history and metadata for a session"""
#     try:
#         if not session_id:
#             return jsonify({"error": "session_id is required"}), 400
        
#         database = MongoDBManager.get_database()
#         chat_collection = database["chat_sessions"]
#         metadata_collection = database["sessions_metadata"]
        
#         # Delete all messages for this session from chat_sessions
#         chat_result = chat_collection.delete_many({"SessionId": session_id})
        
#         # Also delete the session metadata
#         metadata_result = metadata_collection.delete_one({"session_id": session_id})
        
#         deleted_metadata = metadata_result.deleted_count > 0
        
#         return jsonify({
#             "session_id": session_id,
#             "deleted_messages": chat_result.deleted_count,
#             "deleted_metadata": deleted_metadata,
#             "message": "Chat history and metadata cleared successfully"
#         })
        
#     except Exception as e:
#         app.logger.error(f"Clear history error: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route("/session/new", methods=["POST"])
# def create_new_session():
#     """Create a new chat session"""
#     try:
#         data = request.get_json() or {}
#         session_name = data.get("session_name", "New Chat")
        
#         # Generate a unique session ID
#         session_id = str(uuid.uuid4())
        
#         # Create initial session record
#         database = MongoDBManager.get_database()
#         collection = database["sessions_metadata"]
        
#         session_metadata = {
#             "session_id": session_id,
#             "session_name": session_name,
#             "created_at": datetime.now(),
#             "updated_at": datetime.now(),
#             "message_count": 0
#         }
        
#         collection.insert_one(session_metadata)
        
#         return jsonify({
#             "session_id": session_id,
#             "session_name": session_name,
#             "created_at": session_metadata["created_at"].isoformat(),
#             "message": "New session created successfully"
#         })
        
#     except Exception as e:
#         app.logger.error(f"Create session error: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route("/sessions/metadata", methods=["GET"])
# def get_sessions_metadata():
#     """Get metadata for all sessions with accurate message counts"""
#     try:
#         database = MongoDBManager.get_database()
#         metadata_collection = database["sessions_metadata"]
#         chat_collection = database["chat_sessions"]
        
#         # Get all sessions from metadata
#         sessions = list(metadata_collection.find({}, sort=[("updated_at", -1)]))
        
#         # Update each session with actual message count
#         for session in sessions:
#             session_id = session["session_id"]
            
#             # Get actual message count from chat_sessions
#             actual_count = chat_collection.count_documents({"SessionId": session_id})
            
#             # Update session metadata with real count
#             metadata_collection.update_one(
#                 {"session_id": session_id},
#                 {
#                     "$set": {
#                         "message_count": actual_count,
#                         "updated_at": datetime.now() if actual_count > 0 else session.get("updated_at")
#                     }
#                 }
#             )
            
#             # Update the session object for response
#             session["message_count"] = actual_count
#             session["_id"] = str(session["_id"])
#             session["created_at"] = session["created_at"].isoformat() if session.get("created_at") else None
#             session["updated_at"] = session["updated_at"].isoformat() if session.get("updated_at") else None
        
#         return jsonify({
#             "sessions": sessions,
#             "count": len(sessions)
#         })
        
#     except Exception as e:
#         app.logger.error(f"Get sessions metadata error: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

































from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import uuid
from chain import chatbot
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from memory import MongoDBManager, get_session_history
import os
from context_manager import AdmissionContextManager
from functools import wraps

# Initialize context manager
context_manager = AdmissionContextManager()

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable credentials for cookies
load_dotenv()

# Custom decorator for Google OAuth authentication
def google_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user_id from headers (passed by frontend)
        user_id = request.headers.get('X-User-ID')
        email = request.headers.get('X-User-Email')
        
        if not user_id or not email:
            return jsonify({"error": "Authentication required. Please log in."}), 401
        
        # You can add additional verification here if needed
        # For example, check if the user exists in your database
        
        return f(*args, **kwargs, user_id=user_id, email=email)
    return decorated_function

# Helper function to get user from database
def get_or_create_user(google_id: str, email: str, name: str = None):
    """Get existing user or create new user from Google OAuth"""
    database = MongoDBManager.get_database()
    users_collection = database["users"]
    
    # Check if user exists by Google ID
    user = users_collection.find_one({"google_id": google_id})
    
    if not user:
        # Check if user exists by email (in case Google ID changes)
        user = users_collection.find_one({"email": email})
        
    if user:
        # Update last login time
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now()}}
        )
        user["_id"] = str(user["_id"])
        return user
    
    # Create new user
    new_user = {
        "user_id": str(uuid.uuid4()),  # Your internal user ID
        "google_id": google_id,
        "email": email,
        "name": name,
        "created_at": datetime.now(),
        "last_login": datetime.now(),
        "is_active": True
    }
    
    result = users_collection.insert_one(new_user)
    new_user["_id"] = str(result.inserted_id)
    return new_user

# User endpoints
@app.route("/api/user/verify", methods=["POST"])
def verify_user():
    """Verify Google OAuth user and create/get user record"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        google_id = data.get("google_id")
        email = data.get("email")
        name = data.get("name")
        
        if not google_id or not email:
            return jsonify({"error": "Google ID and email are required"}), 400
        
        # Get or create user
        user = get_or_create_user(google_id, email, name)
        
        return jsonify({
            "user_id": user["user_id"],
            "google_id": user["google_id"],
            "email": user["email"],
            "name": user.get("name"),
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            "message": "User verified successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Verify user error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Modified chat endpoint with user association
@app.route("/chat", methods=["POST"])
@google_auth_required
def chat_endpoint(user_id=None, email=None):
    """Main chat endpoint with admission context"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        session_id = data.get("session_id")
        user_input = data.get("input")
        
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        if not user_input:
            return jsonify({"error": "input is required"}), 400
        
        # Get user context
        user_context = context_manager.get_user_context(session_id)
        user_info = user_context.get("user_info", {})
        
        # Extract admission data
        admission_data = context_manager.admission_data
        
        # Prepare context for LLM
        context_text = json.dumps(admission_data, indent=2)[:4000]  # Limit context size
        
        # Check if we need to ask for user information
        if not user_info.get("intermediate_marks"):
            # First message, ask for marks
            if "marks" not in user_input.lower() and "percentage" not in user_input.lower():
                return jsonify({
                    "response": "Welcome to University Admission Assistant! To give you personalized guidance, please provide your intermediate marks (percentage).",
                    "session_id": session_id,
                    "user_id": user_id,  # Add user_id to response
                    "needs_info": "intermediate_marks",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Extract information from user input
        extracted_info = extract_user_info(user_input)
        
        # Update user context with extracted info
        for key, value in extracted_info.items():
            if value:
                context_manager.update_user_info(session_id, key, value)
        
        # Prepare LLM input with enhanced context
        llm_input = {
            "input": user_input,
            "context": context_text,
            "university_name": "Minhaj",
            "user_marks": user_info.get("intermediate_marks", "Not provided"),
            "user_discipline": user_info.get("intermediate_discipline", "Not specified"),
            "user_interest": user_info.get("interested_field", "Not specified"),
            "user_preferences": json.dumps(user_info.get("preferences", {})),
            "admission_status": f"Admission open until {admission_data['important_dates']['admission_end']}"
        }
        
        import asyncio
        
        # Invoke the chatbot
        response = asyncio.run(
            chatbot.ainvoke(
                llm_input,
                config={"configurable": {"session_id": session_id}}
            )
        )
        
        # Update metadata with user_id
        update_session_metadata(session_id, user_id)
        
        # Check if we need to ask for more info
        follow_up = check_for_missing_info(user_info)
        
        return jsonify({
            "response": response.content,
            "session_id": session_id,
            "user_id": user_id,  # Add user_id to response
            "user_info": user_info,
            "follow_up_question": follow_up,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def update_session_metadata(session_id: str, user_id: str = None):
    """Update session metadata with user association"""
    database = MongoDBManager.get_database()
    metadata_collection = database["sessions_metadata"]
    
    metadata = metadata_collection.find_one({"session_id": session_id})
    if not metadata:
        metadata_collection.insert_one({
            "session_id": session_id,
            "session_name": f"Admission Query {session_id[:8]}",
            "user_id": user_id,  # Add user_id
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "message_count": 1,
            "query_type": "admission"
        })
    else:
        metadata_collection.update_one(
            {"session_id": session_id},
            {
                "$inc": {"message_count": 1},
                "$set": {
                    "updated_at": datetime.now(),
                    "user_id": user_id  # Ensure user_id is set
                }
            }
        )

# Modified session endpoints to filter by user
@app.route("/sessions", methods=["GET"])
@google_auth_required
def list_sessions(user_id=None, email=None):
    """List chat sessions for the authenticated user only"""
    try:
        database = MongoDBManager.get_database()
        metadata_collection = database["sessions_metadata"]
        
        # Filter sessions by user_id
        sessions = list(metadata_collection.find(
            {"user_id": user_id},
            sort=[("updated_at", -1)]
        ))
        
        # Get actual message counts from chat_sessions
        chat_collection = database["chat_sessions"]
        for session in sessions:
            session_id = session["session_id"]
            actual_count = chat_collection.count_documents({
                "SessionId": session_id
            })
            
            # Update session with real count
            session["message_count"] = actual_count
            session["_id"] = str(session["_id"])
            session["created_at"] = session["created_at"].isoformat() if session.get("created_at") else None
            session["updated_at"] = session["updated_at"].isoformat() if session.get("updated_at") else None
        
        return jsonify({
            "sessions": sessions,
            "count": len(sessions),
            "user_id": user_id
        })
        
    except Exception as e:
        app.logger.error(f"List sessions error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/history/<session_id>", methods=["GET"])
@google_auth_required
def get_chat_history(session_id, user_id=None, email=None):
    """Get chat history only if the session belongs to the user"""
    try:
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        
        # First check if session belongs to user
        database = MongoDBManager.get_database()
        metadata_collection = database["sessions_metadata"]
        
        session_metadata = metadata_collection.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        if not session_metadata:
            return jsonify({"error": "Session not found or access denied"}), 404
        
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
                "timestamp": None,
                "additional_kwargs": msg.additional_kwargs
            })
        
        return jsonify({
            "session_id": session_id,
            "user_id": user_id,
            "messages": formatted_messages,
            "count": len(formatted_messages)
        })
        
    except Exception as e:
        app.logger.error(f"Get history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/history/<session_id>/clear", methods=["DELETE"])
@google_auth_required
def clear_chat_history(session_id, user_id=None, email=None):
    """Clear chat history only if session belongs to user"""
    try:
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        
        # First check if session belongs to user
        database = MongoDBManager.get_database()
        metadata_collection = database["sessions_metadata"]
        
        session_metadata = metadata_collection.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        if not session_metadata:
            return jsonify({"error": "Session not found or access denied"}), 404
        
        chat_collection = database["chat_sessions"]
        metadata_collection = database["sessions_metadata"]
        
        # Delete all messages for this session
        chat_result = chat_collection.delete_many({"SessionId": session_id})
        
        # Also delete the session metadata
        metadata_result = metadata_collection.delete_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        deleted_metadata = metadata_result.deleted_count > 0
        
        return jsonify({
            "session_id": session_id,
            "user_id": user_id,
            "deleted_messages": chat_result.deleted_count,
            "deleted_metadata": deleted_metadata,
            "message": "Chat history and metadata cleared successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Clear history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/session/new", methods=["POST"])
@google_auth_required
def create_new_session(user_id=None, email=None):
    """Create a new chat session for the authenticated user"""
    try:
        data = request.get_json() or {}
        session_name = data.get("session_name", "New Chat")
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Create initial session record with user_id
        database = MongoDBManager.get_database()
        collection = database["sessions_metadata"]
        
        session_metadata = {
            "session_id": session_id,
            "session_name": session_name,
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "message_count": 0
        }
        
        collection.insert_one(session_metadata)
        
        return jsonify({
            "session_id": session_id,
            "session_name": session_name,
            "user_id": user_id,
            "created_at": session_metadata["created_at"].isoformat(),
            "message": "New session created successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Create session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/sessions/metadata", methods=["GET"])
@google_auth_required
def get_sessions_metadata(user_id=None, email=None):
    """Get metadata for all sessions of the authenticated user"""
    try:
        database = MongoDBManager.get_database()
        metadata_collection = database["sessions_metadata"]
        chat_collection = database["chat_sessions"]
        
        # Get all sessions for this user only
        sessions = list(metadata_collection.find(
            {"user_id": user_id},
            sort=[("updated_at", -1)]
        ))
        
        # Update each session with actual message count
        for session in sessions:
            session_id = session["session_id"]
            
            # Get actual message count from chat_sessions
            actual_count = chat_collection.count_documents({"SessionId": session_id})
            
            # Update session metadata with real count
            metadata_collection.update_one(
                {"session_id": session_id, "user_id": user_id},
                {
                    "$set": {
                        "message_count": actual_count,
                        "updated_at": datetime.now() if actual_count > 0 else session.get("updated_at")
                    }
                }
            )
            
            # Update the session object for response
            session["message_count"] = actual_count
            session["_id"] = str(session["_id"])
            session["created_at"] = session["created_at"].isoformat() if session.get("created_at") else None
            session["updated_at"] = session["updated_at"].isoformat() if session.get("updated_at") else None
        
        return jsonify({
            "sessions": sessions,
            "count": len(sessions),
            "user_id": user_id
        })
        
    except Exception as e:
        app.logger.error(f"Get sessions metadata error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Keep existing helper functions (extract_user_info, check_for_missing_info)
def extract_user_info(user_input: str) -> Dict[str, Any]:
    """Extract user information from input"""
    extracted = {}
    
    import re
    marks_pattern = r'(\d{1,3})%\s*marks|\s*(\d{1,3})\s*percent'
    marks_match = re.search(marks_pattern, user_input, re.IGNORECASE)
    if marks_match:
        extracted["intermediate_marks"] = marks_match.group(1) or marks_match.group(2)
    
    disciplines = ["ICS", "FSC Pre-Engineering", "FSC Pre-Medical", "FA", "I.Com", "A-Levels"]
    for discipline in disciplines:
        if discipline.lower() in user_input.lower():
            extracted["intermediate_discipline"] = discipline
            break
    
    fields = ["Computer Science", "Software Engineering", "PharmD", "DPT", "Engineering", "Medicine"]
    for field in fields:
        if field.lower() in user_input.lower():
            extracted["interested_field"] = field
            break
    
    return extracted

def check_for_missing_info(user_info: Dict[str, Any]) -> Optional[str]:
    """Check if we need to ask for more information"""
    if not user_info.get("intermediate_marks"):
        return "What is your intermediate marks percentage?"
    elif not user_info.get("intermediate_discipline"):
        return "What was your intermediate discipline? (e.g., ICS, FSC Pre-Engineering, FSC Pre-Medical)"
    elif not user_info.get("interested_field"):
        return "Which field are you interested in? (e.g., Computer Science, Pharmacy, Medicine)"
    
    return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)