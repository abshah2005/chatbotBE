// Initialize database and user for chat application
db = db.getSiblingDB('chat_history_db');

// Create user for the application
db.createUser({
  user: 'chat_app',
  pwd: 'app_password',
  roles: [
    {
      role: 'readWrite',
      db: 'chat_history_db'
    }
  ]
});

// Create collections
db.createCollection('chat_sessions');
db.createCollection('sessions_metadata');

print('✅ MongoDB initialized successfully');