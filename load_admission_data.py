# load_admission_data.py
import json
from memory import MongoDBManager
from datetime import datetime

def load_admission_data():
    """Load admission data from JSON file to MongoDB"""
    try:
        # Load from JSON file
        with open('admissions_data.json', 'r', encoding='utf-8') as f:
            admission_data = json.load(f)
        
        database = MongoDBManager.get_database()
        collection = database["admission_context"]
        
        # Update or insert admission data
        collection.update_one(
            {"type": "admission_data"},
            {
                "$set": {
                    "type": "admission_data",
                    "data": admission_data,
                    "last_updated": datetime.now()
                }
            },
            upsert=True
        )
        
        print("✅ Admission data loaded successfully")
        
    except Exception as e:
        print(f"❌ Error loading admission data: {e}")

if __name__ == "__main__":
    load_admission_data()