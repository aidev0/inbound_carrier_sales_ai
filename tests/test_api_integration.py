import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class TestAPIIntegration:
    """Integration tests for the deployed API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration"""
        self.api_url = os.getenv('API_URL')
        self.api_key = os.getenv('API_SECRET_KEY')
        
        if not self.api_url:
            pytest.skip("API_URL not configured in environment")
        if not self.api_key:
            pytest.skip("API_SECRET_KEY not configured in environment")

    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.api_url}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_verify_carrier_with_api_key(self):
        """Test carrier verification with valid API key"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        data = {"mc_number": "MC-227271"}
        
        response = requests.post(
            f"{self.api_url}/verify-carrier",
            headers=headers,
            json=data,
            timeout=30
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "verified"
        assert result["company_name"] == "KNIGHT TRANSPORTATION INC"
        assert result["dot_number"] == 428823
        assert result["mc_number"] == "227271"

    def test_verify_carrier_without_api_key(self):
        """Test carrier verification without API key (should fail)"""
        headers = {"Content-Type": "application/json"}
        data = {"mc_number": "MC-227271"}
        
        response = requests.post(
            f"{self.api_url}/verify-carrier",
            headers=headers,
            json=data,
            timeout=10
        )
        
        assert response.status_code == 401
        result = response.json()
        assert result["status"] == "error"
        assert "API key required" in result["error"]

    def test_verify_carrier_invalid_api_key(self):
        """Test carrier verification with invalid API key"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": "invalid_key"
        }
        data = {"mc_number": "MC-227271"}
        
        response = requests.post(
            f"{self.api_url}/verify-carrier",
            headers=headers,
            json=data,
            timeout=10
        )
        
        assert response.status_code == 401
        result = response.json()
        assert result["status"] == "error"
        assert "Invalid API key" in result["error"]

    def test_verify_carrier_missing_mc_number(self):
        """Test carrier verification with missing MC number"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        data = {}
        
        response = requests.post(
            f"{self.api_url}/verify-carrier",
            headers=headers,
            json=data,
            timeout=10
        )
        
        assert response.status_code == 400
        result = response.json()
        assert result["status"] == "error"
        assert "MC number is required" in result["error"]

    def test_verify_carrier_invalid_format(self):
        """Test carrier verification with invalid MC number format"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        data = {"mc_number": "INVALID"}
        
        response = requests.post(
            f"{self.api_url}/verify-carrier",
            headers=headers,
            json=data,
            timeout=30
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "invalid"
        assert "Invalid MC number format" in result["error"]

    def test_verify_nonexistent_mc_number(self):
        """Test carrier verification with non-existent MC number"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        data = {"mc_number": "MC-000001"}
        
        response = requests.post(
            f"{self.api_url}/verify-carrier",
            headers=headers,
            json=data,
            timeout=30
        )
        
        # Could be 404 (not found) or 200 (inactive status)
        assert response.status_code in [200, 404]
        result = response.json()
        assert result["status"] in ["not_found", "inactive"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])