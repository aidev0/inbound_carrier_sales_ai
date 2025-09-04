from flask import Flask, request, jsonify
from fmcsa_verify import verify_mc_number
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)