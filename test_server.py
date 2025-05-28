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
        print(f"Lỗi khi khởi động server: {e}")

def test_endpoints():
    """Test các endpoints"""
    base_url = "http://127.0.0.1:8000"
      # Đợi server khởi động
    print("Đang đợi server khởi động...")
    time.sleep(3)
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/")
        print(f"GET / - Trạng thái: {response.status_code}")
        print(f"Phản hồi: {response.json()}")
        print()
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        print(f"GET /health - Trạng thái: {response.status_code}")
        print(f"Phản hồi: {response.json()}")
        
        print("\nTất cả endpoints đã được kiểm tra thành công!")
        
    except requests.exceptions.ConnectionError:
        print("Không thể kết nối đến server. Đảm bảo server đang chạy tại http://127.0.0.1:8000")
    except Exception as e:
        print(f"Lỗi khi kiểm tra endpoints: {e}")

if __name__ == "__main__":
    print("Bắt đầu kiểm tra FastAPI server...")
    
    # Khởi động server trong thread riêng
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Test endpoints
    test_endpoints()
