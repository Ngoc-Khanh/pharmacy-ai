from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.database import get_database
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.db = get_database()
        
    

# Tạo instance service
db_service = DatabaseService() 