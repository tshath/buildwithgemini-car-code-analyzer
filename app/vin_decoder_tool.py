import json
import os
import urllib.parse
import urllib.request
from typing import Dict, Any

# If a third-party API key is ever configured, read from env var
VIN_API_KEY = os.getenv("VIN_API_KEY", "")

def decode_vin(vin: str) -> str:
    """Decode a 17-character Vehicle Identification Number (VIN) using the official NHTSA vPIC Public API.
    Retrieves the exact vehicle make, model, year, engine displacement, cylinder count,
    fuel type, and drivetrain specifications needed for accurate OBD2 diagnostics.

    Args:
        vin: The 17-character VIN string (e.g. '1HGCR2F83HA000000').

    Returns:
        A JSON string containing the decoded vehicle specs or an error message.
    """
    clean_vin = vin.strip().upper()
    if len(clean_vin) != 17:
        return json.dumps({
            "status": "error",
            "message": f"Invalid VIN length ({len(clean_vin)} characters). A standard VIN must be exactly 17 characters."
        })

    encoded_vin = urllib.parse.quote(clean_vin)
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{encoded_vin}?format=json"

    headers = {
        "User-Agent": "PitStop-AI/1.0 (Automotive Diagnostic Assistant)"
    }
    if VIN_API_KEY:
        headers["Authorization"] = f"Bearer {VIN_API_KEY}"

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to connect to VIN decoder service: {str(e)}"
        })

    results = data.get("Results", [])
    if not results:
        return json.dumps({"status": "error", "message": f"No data returned for VIN {clean_vin}"})

    r = results[0]
    error_code = r.get("ErrorCode", "")
    if error_code and error_code not in ("0", "") and not r.get("Make"):
        return json.dumps({
            "status": "error",
            "message": f"VIN decoding error: {r.get('ErrorText', 'Unknown error')}"
        })

    specs = {
        "status": "success",
        "vin": clean_vin,
        "year": r.get("ModelYear"),
        "make": r.get("Make"),
        "model": r.get("Model"),
        "trim": r.get("Trim"),
        "engine_displacement_l": r.get("DisplacementL"),
        "engine_cylinders": r.get("EngineCylinders"),
        "engine_configuration": r.get("EngineConfiguration"),
        "fuel_type": r.get("FuelTypePrimary"),
        "drive_type": r.get("DriveType"),
        "transmission_style": r.get("TransmissionStyle"),
        "body_class": r.get("BodyClass"),
        "plant_country": r.get("PlantCountry")
    }

    return json.dumps(specs, indent=2)
