import requests
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

def verify_mc_number(mc_number: str) -> Dict:
    """
    Verify MC number with FMCSA API
    
    Args:
        mc_number (str): Motor Carrier number to verify
        
    Returns:
        Dict: Verification result with status and company info
    """
    api_key = os.getenv('FMCSA_API_KEY')
    
    try:
        # Clean MC number - remove any non-numeric characters
        clean_mc = ''.join(filter(str.isdigit, mc_number))
        
        if not clean_mc:
            return {
                "status": "invalid",
                "error": "Invalid MC number format",
                "mc_number": mc_number
            }
        
        # Make request to FMCSA API
        headers = {
            'User-Agent': 'FreightBroker/1.0',
            'Accept': 'application/json'
        }
        
        if not api_key:
            return {
                "status": "error",
                "error": "FMCSA API key (webkey) is required but not found in environment variables",
                "mc_number": clean_mc
            }
        
        # Use correct FMCSA API endpoint for MC/docket number lookup
        url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{clean_mc}"
        params = {'webKey': api_key}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return parse_fmcsa_response(data, clean_mc)
        elif response.status_code == 404:
            return {
                "status": "not_found",
                "error": "MC number not found in FMCSA database",
                "mc_number": clean_mc
            }
        else:
            return {
                "status": "error",
                "error": f"FMCSA API returned status {response.status_code}",
                "mc_number": clean_mc
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "FMCSA API timeout",
            "mc_number": mc_number
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"Request failed: {str(e)}",
            "mc_number": mc_number
        }

def parse_fmcsa_response(data: Dict, mc_number: str) -> Dict:
    """Parse FMCSA API response and return standardized format"""
    try:
        # Check if we have content and extract carrier data
        if not data.get('content') or len(data['content']) == 0:
            return {
                "status": "not_found",
                "error": "No carrier data found in FMCSA response",
                "mc_number": mc_number
            }
        
        carrier_data = data['content'][0]['carrier']
        
        # Extract relevant fields from FMCSA response
        company_name = carrier_data.get('legalName', 'Unknown')
        status_code = carrier_data.get('statusCode', '')
        allowed_to_operate = carrier_data.get('allowedToOperate', '')
        
        # Determine verification status based on FMCSA status codes
        # A = Active/Authorized, I = Inactive, etc.
        if status_code == 'A' and allowed_to_operate == 'Y':
            status = "verified"
        elif status_code in ['I', 'U']:  # Inactive or Unauthorized
            status = "inactive"
        elif allowed_to_operate == 'N':
            status = "not_authorized"
        else:
            status = "unknown"
        
        # Parse insurance information
        bipd_insurance_required = carrier_data.get('bipdInsuranceRequired', '') == 'Y'
        cargo_insurance_required = carrier_data.get('cargoInsuranceRequired', '') == 'Y'
        
        return {
            "status": status,
            "mc_number": mc_number,
            "dot_number": carrier_data.get('dotNumber'),
            "company_name": company_name,
            "status_code": status_code,
            "allowed_to_operate": allowed_to_operate,
            "safety_rating": carrier_data.get('safetyRating'),
            "bipd_insurance_required": bipd_insurance_required,
            "cargo_insurance_required": cargo_insurance_required,
            "bipd_insurance_on_file": carrier_data.get('bipdInsuranceOnFile'),
            "cargo_insurance_on_file": carrier_data.get('cargoInsuranceOnFile'),
            "total_drivers": carrier_data.get('totalDrivers'),
            "total_power_units": carrier_data.get('totalPowerUnits'),
            "physical_address": {
                "street": carrier_data.get('phyStreet'),
                "city": carrier_data.get('phyCity'),
                "state": carrier_data.get('phyState'),
                "zipcode": carrier_data.get('phyZipcode')
            }
        }
        
    except (KeyError, IndexError, TypeError) as e:
        return {
            "status": "error",
            "error": f"Unexpected FMCSA response format: {str(e)}",
            "mc_number": mc_number,
            "raw_response": data
        }