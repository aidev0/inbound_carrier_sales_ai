from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class MongoConnection:
    """MongoDB connection utility"""
    
    def __init__(self):
        self.connection_string = None
        self.database_name = None
        self.loads_collection_name = None
        self.client = None
        self.db = None
        self.loads_collection = None
        self._initialized = False

    def _initialize(self):
        """Initialize connection parameters from environment variables"""
        if self._initialized:
            return True
            
        self.connection_string = os.getenv('MONGODB_URL')
        self.database_name = os.getenv('DATABASE_NAME')
        self.loads_collection_name = os.getenv('LOADS_COLLECTION_NAME')
        
        if not self.connection_string:
            raise ValueError("MONGODB_URL not found in environment variables")
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
                serverSelectionTimeoutMS=10000,  # 10 second timeout
                connectTimeoutMS=15000,          # 15 second connect timeout
                socketTimeoutMS=20000,           # 20 second socket timeout
                maxIdleTimeMS=30000,             # 30 second idle timeout
                maxPoolSize=10,                  # Maximum pool size
                minPoolSize=1,                   # Minimum pool size
                retryWrites=True,                # Enable retryable writes
                retryReads=True                  # Enable retryable reads
            )
            self.db = self.client[self.database_name]
            self.loads_collection = self.db[self.loads_collection_name]
            
            # Test connection with timeout
            self.client.admin.command('ping')
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
            ).max_time_ms(15000)  # 15 second query timeout
            
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

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            
# Global instance
mongo_conn = MongoConnection()