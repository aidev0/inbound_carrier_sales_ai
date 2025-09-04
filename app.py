from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from fmcsa_verify import verify_mc_number

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "success",
        "message": "FMCSA Carrier Verification API",
        "endpoints": {
            "verify": "/api/verify/<mc_number>",
            "health": "/health"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy"})

@app.route('/api/verify/<mc_number>', methods=['GET'])
def verify_carrier(mc_number):
    """
    Verify MC number with FMCSA database
    
    Args:
        mc_number (str): Motor Carrier number (e.g., MC-227271, 227271)
    
    Returns:
        JSON: Verification result with carrier information
    """
    try:
        result = verify_mc_number(mc_number)
        
        # Add HTTP status code based on result
        if result['status'] == 'error':
            return jsonify(result), 500
        elif result['status'] == 'not_found':
            return jsonify(result), 404
        elif result['status'] == 'invalid':
            return jsonify(result), 400
        else:
            return jsonify(result), 200
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Internal server error: {str(e)}",
            "mc_number": mc_number
        }), 500

@app.route('/api/verify', methods=['POST'])
def verify_carrier_post():
    """
    Verify MC number via POST request
    
    Expected JSON body:
    {
        "mc_number": "MC-227271"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'mc_number' not in data:
            return jsonify({
                "status": "error",
                "error": "Missing 'mc_number' in request body"
            }), 400
            
        mc_number = data['mc_number']
        result = verify_mc_number(mc_number)
        
        # Add HTTP status code based on result
        if result['status'] == 'error':
            return jsonify(result), 500
        elif result['status'] == 'not_found':
            return jsonify(result), 404
        elif result['status'] == 'invalid':
            return jsonify(result), 400
        else:
            return jsonify(result), 200
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "error": "Endpoint not found",
        "available_endpoints": [
            "/",
            "/health",
            "/api/verify/<mc_number>",
            "/api/verify (POST)"
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "status": "error",
        "error": "Method not allowed"
    }), 405

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)