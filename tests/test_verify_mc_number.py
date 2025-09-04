import pytest
import os
import requests
from unittest.mock import patch, Mock
from fmcsa_verify import verify_mc_number, parse_fmcsa_response


class TestVerifyMcNumber:
    """Test cases for FMCSA MC number verification"""

    def test_valid_mc_number_verified(self):
        """Test with a valid, verified MC number"""
        # Mock response data based on actual FMCSA API response
        mock_response_data = {
            "content": [{
                "carrier": {
                    "dotNumber": 428823,
                    "legalName": "KNIGHT TRANSPORTATION INC",
                    "statusCode": "A",
                    "allowedToOperate": "Y",
                    "safetyRating": "S",
                    "bipdInsuranceRequired": "Y",
                    "cargoInsuranceRequired": "u",
                    "bipdInsuranceOnFile": "5000",
                    "cargoInsuranceOnFile": "5",
                    "totalDrivers": 3200,
                    "totalPowerUnits": 3200,
                    "phyStreet": "2002 WEST WAHALLA LANE",
                    "phyCity": "PHOENIX",
                    "phyState": "AZ",
                    "phyZipcode": "85027"
                }
            }]
        }
        
        with patch('fmcsa_verify.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            with patch.dict(os.environ, {'FMCSA_API_KEY': 'test_key'}):
                result = verify_mc_number("MC-227271")
                
                assert result['status'] == 'verified'
                assert result['mc_number'] == '227271'
                assert result['dot_number'] == 428823
                assert result['company_name'] == 'KNIGHT TRANSPORTATION INC'
                assert result['status_code'] == 'A'
                assert result['allowed_to_operate'] == 'Y'
                assert result['safety_rating'] == 'S'
                assert result['bipd_insurance_required'] is True
                assert result['cargo_insurance_required'] is False

    def test_inactive_mc_number(self):
        """Test with an inactive MC number"""
        mock_response_data = {
            "content": [{
                "carrier": {
                    "dotNumber": 123456,
                    "legalName": "INACTIVE CARRIER INC",
                    "statusCode": "I",
                    "allowedToOperate": "N",
                    "safetyRating": "U",
                    "bipdInsuranceRequired": "N",
                    "cargoInsuranceRequired": "N"
                }
            }]
        }
        
        with patch('fmcsa_verify.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            with patch.dict(os.environ, {'FMCSA_API_KEY': 'test_key'}):
                result = verify_mc_number("MC-999999")
                
                assert result['status'] == 'inactive'
                assert result['company_name'] == 'INACTIVE CARRIER INC'
                assert result['status_code'] == 'I'
                assert result['allowed_to_operate'] == 'N'

    def test_mc_number_not_found(self):
        """Test with MC number that returns 404"""
        with patch('fmcsa_verify.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            with patch.dict(os.environ, {'FMCSA_API_KEY': 'test_key'}):
                result = verify_mc_number("MC-000000")
                
                assert result['status'] == 'not_found'
                assert 'not found in FMCSA database' in result['error']
                assert result['mc_number'] == '000000'

    def test_missing_api_key(self):
        """Test behavior when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            result = verify_mc_number("MC-227271")
            
            assert result['status'] == 'error'
            assert 'webkey' in result['error'].lower()
            assert 'required' in result['error'].lower()

    def test_invalid_mc_number_format(self):
        """Test with invalid MC number format"""
        result = verify_mc_number("INVALID")
        
        assert result['status'] == 'invalid'
        assert result['error'] == 'Invalid MC number format'

    def test_api_timeout(self):
        """Test API timeout handling"""
        with patch('fmcsa_verify.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            with patch.dict(os.environ, {'FMCSA_API_KEY': 'test_key'}):
                result = verify_mc_number("MC-227271")
                
                assert result['status'] == 'error'
                assert 'timeout' in result['error'].lower()

    def test_api_request_exception(self):
        """Test general request exception handling"""
        with patch('fmcsa_verify.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Connection error")
            
            with patch.dict(os.environ, {'FMCSA_API_KEY': 'test_key'}):
                result = verify_mc_number("MC-227271")
                
                assert result['status'] == 'error'
                assert 'Request failed' in result['error']

    def test_mc_number_cleaning(self):
        """Test that MC numbers are properly cleaned"""
        mock_response_data = {
            "content": [{
                "carrier": {
                    "dotNumber": 428823,
                    "legalName": "TEST CARRIER",
                    "statusCode": "A",
                    "allowedToOperate": "Y"
                }
            }]
        }
        
        with patch('fmcsa_verify.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            with patch.dict(os.environ, {'FMCSA_API_KEY': 'test_key'}):
                # Test various MC number formats
                for mc_input in ["MC-227271", "MC227271", "227271", "mc-227271"]:
                    result = verify_mc_number(mc_input)
                    assert result['mc_number'] == '227271'

    def test_parse_fmcsa_response_empty_content(self):
        """Test parsing response with empty content"""
        empty_response = {"content": []}
        result = parse_fmcsa_response(empty_response, "123456")
        
        assert result['status'] == 'not_found'
        assert 'No carrier data found' in result['error']

    def test_parse_fmcsa_response_malformed(self):
        """Test parsing malformed response"""
        malformed_response = {"content": [{"invalid": "data"}]}
        result = parse_fmcsa_response(malformed_response, "123456")
        
        assert result['status'] == 'error'
        assert 'Unexpected FMCSA response format' in result['error']
        assert 'raw_response' in result


# Integration test that requires actual API key
class TestIntegration:
    """Integration tests that require a real FMCSA API key"""
    
    @pytest.mark.skipif(not os.getenv('FMCSA_API_KEY'), reason="Requires FMCSA_API_KEY")
    def test_real_api_call(self):
        """Test with actual API call - requires real API key"""
        result = verify_mc_number("MC-227271")
        
        # Should get verified result for Knight Transportation
        assert result['status'] == 'verified'
        assert result['company_name'] == 'KNIGHT TRANSPORTATION INC'
        assert result['dot_number'] == 428823
        
    @pytest.mark.skipif(not os.getenv('FMCSA_API_KEY'), reason="Requires FMCSA_API_KEY")
    def test_nonexistent_mc_number(self):
        """Test with non-existent MC number"""
        result = verify_mc_number("MC-000001")
        
        # MC-000001 might exist but be inactive, so check for either
        assert result['status'] in ['not_found', 'inactive']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])