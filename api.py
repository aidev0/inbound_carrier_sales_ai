from flask import Flask, request, jsonify
from fmcsa_verify import verify_mc_number
from mongo_client import mongo_conn
from functools import wraps
import os

app = Flask(__name__)

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_secret = os.getenv('API_SECRET_KEY')
        if not api_secret:
            return jsonify({
                "status": "error",
                "error": "API authentication not configured"
            }), 500
            
        # Check for API key in headers
        provided_key = request.headers.get('X-API-Key')
        if not provided_key:
            return jsonify({
                "status": "error",
                "error": "API key required. Include 'X-API-Key' header."
            }), 401
            
        if provided_key != api_secret:
            return jsonify({
                "status": "error",
                "error": "Invalid API key"
            }), 401
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/verify-carrier', methods=['POST'])
@require_api_key
def verify_carrier():
    """Verify carrier MC number through FMCSA API"""
    try:
        data = request.get_json()
        
        if not data or 'mc_number' not in data:
            return jsonify({
                "status": "error",
                "error": "MC number is required"
            }), 400
        
        mc_number = data['mc_number']
        result = verify_mc_number(mc_number)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/search-loads', methods=['POST'])
@require_api_key
def search_loads():
    """Search for loads by equipment type"""
    try:
        data = request.get_json()
        
        if not data or 'equipment_type' not in data:
            return jsonify({
                "status": "error",
                "error": "equipment_type is required"
            }), 400
        
        equipment_type = data['equipment_type']
        
        # Search loads in MongoDB
        loads = mongo_conn.search_loads_by_equipment(equipment_type)
        
        if loads is None:
            return jsonify({
                "status": "error",
                "error": "Database connection failed"
            }), 500
        
        return jsonify({
            "status": "success",
            "equipment_type": equipment_type,
            "count": len(loads),
            "loads": loads
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/carriers-calls', methods=['POST'])
@require_api_key
def create_carrier_call():
    """Create a new carrier call record"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "error": "Request body is required"
            }), 400
        
        # Insert the document with timestamp
        from datetime import datetime, timezone
        call_data = {
            **data,
            "created_at": datetime.now(timezone.utc)
        }
        
        result = mongo_conn.insert_carrier_call(call_data)
        
        if result is None:
            return jsonify({
                "status": "error",
                "error": "Database connection failed"
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "Carrier call record created successfully",
            "data": result
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Internal server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)