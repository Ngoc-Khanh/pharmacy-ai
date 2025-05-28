#!/usr/bin/env python3
"""
Test script để kiểm tra FastAPI server
"""
import requests
import time
import subprocess
import sys
from threading import Thread

def start_server():
    """Khởi động server trong background"""
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"])
    except Exception as e:
        print(f"Error starting server: {e}")

def test_endpoints():
    """Test các endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    # Đợi server khởi động
    print("Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/")
        print(f"GET / - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        print(f"GET /health - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test medications endpoint
        response = requests.get(f"{base_url}/api/medications")
        print(f"GET /api/medications - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Make sure it's running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"Error testing endpoints: {e}")

if __name__ == "__main__":
    print("Starting FastAPI server test...")
    
    # Khởi động server trong thread riêng
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Test endpoints
    test_endpoints()
