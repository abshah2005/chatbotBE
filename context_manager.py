import json
from datetime import datetime
from typing import Dict, Any, Optional
from memory import MongoDBManager

class AdmissionContextManager:
    """Manages admission-related context and user information"""
    
    def __init__(self):
        self.database = MongoDBManager.get_database()
        self.context_collection = self.database["admission_context"]
        
        # Load admission data
        self.admission_data = self._load_admission_data()
    
    def _load_admission_data(self) -> Dict[str, Any]:
        """Load admission-related data from database or file"""
        # Try to load from database first
        data = self.context_collection.find_one({"type": "admission_data"})
        
        if data:
            return data.get("data", {})
        
        # Default structure
        return {
            "programs": {
                "Computer Science": {
                    "seats_total": 200,
                    "seats_remaining": 45,
                    "eligibility": "Intermediate with Mathematics (60%+)",
                    "fee_per_semester": 85000,
                    "duration": "4 years",
                    "subjects": ["Programming", "Algorithms", "Database", "AI"]
                },
                "Software Engineering": {
                    "seats_total": 150,
                    "seats_remaining": 30,
                    "eligibility": "FSC Pre-Engineering (55%+)",
                    "fee_per_semester": 90000,
                    "duration": "4 years",
                    "subjects": ["Software Design", "Web Development", "Mobile Apps"]
                },
                "PharmD": {
                    "seats_total": 100,
                    "seats_remaining": 15,
                    "eligibility": "FSC Pre-Medical (70%+)",
                    "fee_per_semester": 120000,
                    "duration": "5 years"
                },
                "DPT": {
                    "seats_total": 80,
                    "seats_remaining": 25,
                    "eligibility": "FSC Pre-Medical (65%+)",
                    "fee_per_semester": 95000,
                    "duration": "5 years"
                }
                # Add more programs as needed
            },
            "admission_schedule": {
                "start_date": "2024-01-15",
                "end_date": "2024-08-30",
                "merit_list_dates": ["2024-09-10", "2024-09-20"]
            },
            "faqs": [
                {
                    "question": "What's the difference between CS and SE?",
                    "answer": "CS focuses on theory and fundamentals, while SE focuses on practical software development."
                },
                {
                    "question": "Can I apply with FSC Pre-Medical for CS?",
                    "answer": "No, CS requires Mathematics in intermediate."
                }
            ],
            "fee_structure": {
                "admission_fee": 10000,
                "security_deposit": 5000,
                "semester_fees": "Varies by program"
            }
        }
    
    def get_user_context(self, session_id: str) -> Dict[str, Any]:
        """Get or create user-specific context"""
        user_context = self.database["user_contexts"].find_one({"session_id": session_id})
        
        if not user_context:
            user_context = {
                "session_id": session_id,
                "user_info": {
                    "intermediate_marks": None,
                    "intermediate_discipline": None,
                    "interested_field": None,
                    "preferences": {}
                },
                "conversation_state": "greeting",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            self.database["user_contexts"].insert_one(user_context)
        
        return user_context
    
    def update_user_info(self, session_id: str, field: str, value: Any):
        """Update user information"""
        self.database["user_contexts"].update_one(
            {"session_id": session_id},
            {
                "$set": {
                    f"user_info.{field}": value,
                    "updated_at": datetime.now()
                }
            }
        )
    
    def get_program_recommendations(self, marks: float, discipline: str) -> Dict[str, Any]:
        """Generate program recommendations based on marks and discipline"""
        recommendations = []
        
        for program_name, program_info in self.admission_data["programs"].items():
            # Check eligibility based on discipline
            if self._check_eligibility(program_info["eligibility"], discipline, marks):
                recommendations.append({
                    "program": program_name,
                    "eligibility_score": self._calculate_eligibility_score(marks),
                    "seats_remaining": program_info.get("seats_remaining", 0),
                    "fee": program_info.get("fee_per_semester", 0)
                })
        
        return {
            "recommendations": sorted(recommendations, key=lambda x: x["eligibility_score"], reverse=True),
            "user_marks": marks,
            "user_discipline": discipline
        }
    
    def _check_eligibility(self, eligibility_str: str, discipline: str, marks: float) -> bool:
        """Check if user is eligible for a program"""
        # Simplified eligibility check - expand based on your criteria
        discipline_map = {
            "ICS": ["Computer Science", "Software Engineering", "IT"],
            "FSC Pre-Engineering": ["Software Engineering", "Electrical Engineering", "Civil Engineering"],
            "FSC Pre-Medical": ["PharmD", "DPT", "Biotechnology", "MBBS"]
        }
        
        # Implement your actual eligibility logic here
        return True
    
    def _calculate_eligibility_score(self, marks: float) -> float:
        """Calculate eligibility score based on marks"""
        if marks >= 80:
            return 1.0
        elif marks >= 70:
            return 0.8
        elif marks >= 60:
            return 0.6
        else:
            return 0.4
    
    def get_program_comparison(self, program1: str, program2: str) -> Dict[str, Any]:
        """Compare two programs"""
        p1 = self.admission_data["programs"].get(program1, {})
        p2 = self.admission_data["programs"].get(program2, {})
        
        return {
            "comparison": {
                program1: p1,
                program2: p2
            },
            "differences": self._find_differences(p1, p2)
        }
    
    # def _find_differences(self, p1: Dict, p2: Dict) -> Dict[str, Any]:
    #     """Find key differences between two programs"""
    #     differences = {}
        
    #     for key in set(p1.keys()) | set(p2.keys()):
    #         if p1.get(key) != p2.get(key):
    #             differences[key] = {
    #                 program1: p1.get(key),
    #                 program2: p2.get(key)
    #             }
        
    #     return differences
    
    def _find_differences(self, p1: Dict, p2: Dict, program1: str, program2: str) -> Dict[str, Any]:
        """Find key differences between two programs"""
        differences = {}
        
        for key in set(p1.keys()) | set(p2.keys()):
            if p1.get(key) != p2.get(key):
                differences[key] = {
                    program1: p1.get(key),
                    program2: p2.get(key)
                }
        
        return differences