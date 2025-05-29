import requests
import json
import os

# URL of your FastAPI server
BASE_URL = "http://localhost:8000"  # Change this if your server is on a different port or host

def diagnose_symptoms(symptoms, age=None, gender=None, medical_history=None, additional_info=None):
    """
    Send a request to the symptom diagnosis API
    
    Args:
        symptoms: List of symptoms
        age: Patient's age (optional)
        gender: Patient's gender (optional)
        medical_history: Patient's medical history (optional)
        additional_info: Any additional information (optional)
    
    Returns:
        Dictionary containing the API response
    """
    url = f"{BASE_URL}/api/diagnosis/analyze"
    
    # Prepare the request payload
    payload = {
        "symptoms": symptoms
    }
    
    # Add optional fields if provided
    if age is not None:
        payload["age"] = age
    if gender is not None:
        payload["gender"] = gender
    if medical_history is not None:
        payload["medical_history"] = medical_history
    if additional_info is not None:
        payload["additional_info"] = additional_info
    
    # Make the API request
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    # Example usage
    symptoms = ["đau đầu", "sốt", "mệt mỏi"]
    result = diagnose_symptoms(
        symptoms=symptoms,
        age=35,
        gender="nam",
        medical_history="Không có tiền sử bệnh nào đáng kể",
        additional_info="Triệu chứng xuất hiện sau khi đi du lịch"
    )
    
    if result:
        print("\nKết quả chẩn đoán:")
        print("-----------------")
        
        print("\nCác tình trạng có thể:")
        for condition in result["possible_conditions"]:
            print(f"- {condition}")
        
        print("\nĐề xuất:")
        for recommendation in result["recommendations"]:
            print(f"- {recommendation}")
        
        print(f"\n{result['disclaimer']}") 