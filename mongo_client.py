from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

class MongoConnection:
    """MongoDB connection utility"""
    
    def __init__(self):
        self.connection_string = None
        self.database_name = None
        self.loads_collection_name = None
        self.carriers_calls_collection_name = None
        self.client = None
        self.db = None
        self.loads_collection = None
        self.carriers_calls_collection = None
        self._initialized = False

    def _initialize(self):
        """Initialize connection parameters from environment variables"""
        if self._initialized:
            return True
            
        self.connection_string = os.getenv('MONGODB_URI')
        self.database_name = os.getenv('DATABASE_NAME')
        self.loads_collection_name = os.getenv('LOADS_COLLECTION_NAME')
        self.carriers_calls_collection_name = os.getenv('CARRIERS_CALLS_COLLECTION_NAME', 'carriers_calls')
        
        if not self.connection_string:
            raise ValueError("MONGODB_URI not found in environment variables")
        if not self.database_name:
            raise ValueError("DATABASE_NAME not found in environment variables") 
        if not self.loads_collection_name:
            raise ValueError("LOADS_COLLECTION_NAME not found in environment variables")
            
        self._initialized = True
        return True

    def connect(self):
        """Establish MongoDB connection"""
        try:
            if not self._initialize():
                return False
                
            self.client = MongoClient(
                self.connection_string,
                socketTimeoutMS=60000, 
                connectTimeoutMS=60000
            )
            self.db = self.client[self.database_name]
            self.loads_collection = self.db[self.loads_collection_name]
            self.carriers_calls_collection = self.db[self.carriers_calls_collection_name]
            
            # Test connection with timeout
            # self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            if self.client:
                self.client.close()
                self.client = None
            return False

    def search_loads_by_equipment(self, equipment_type):
        """Search loads by equipment type"""
        try:
            if not self.loads_collection:
                if not self.connect():
                    return None
            
            # Search for loads with matching equipment type with timeout
            cursor = self.loads_collection.find(
                {"equipment_type": equipment_type}
            )
            
            loads = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for load in loads:
                if '_id' in load:
                    load['_id'] = str(load['_id'])
                    
            return loads
        except Exception as e:
            print(f"Error searching loads: {e}")
            # Reset connection on error
            self.client = None
            self.loads_collection = None
            return None

    def insert_carrier_call(self, call_data):
        """Insert a carrier call document"""
        try:
            if not self.carriers_calls_collection:
                if not self.connect():
                    return None
            
            # Insert the document
            result = self.carriers_calls_collection.insert_one(call_data)
            
            return {
                "inserted_id": str(result.inserted_id),
                "acknowledged": result.acknowledged
            }
        except Exception as e:
            print(f"Error inserting carrier call: {e}")
            # Reset connection on error
            self.client = None
            self.carriers_calls_collection = None
            return None

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            
# Global instance
mongo_conn = MongoConnection()