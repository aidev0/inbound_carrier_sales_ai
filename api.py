from flask import Flask, request, jsonify
from fmcsa_verify import verify_mc_number
import os

app = Flask(__name__)

@app.route('/verify-carrier', methods=['POST'])
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