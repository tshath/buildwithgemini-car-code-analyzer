import json
from typing import Optional, Dict, Any, List
from google.cloud import firestore

# Hardcode the GCP Project ID as a string to avoid project number resolution issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-03-3ff306ba56bc"

_db = None

def get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db

def lookup_obd2_code(code: str) -> str:
    """Look up diagnostic trouble code (OBD2) details, symptoms, causes, fixes, and estimated costs.

    Args:
        code: The standard OBD2 trouble code (e.g., 'P0300', 'P0420', 'P0171', 'P0128', 'P0455').

    Returns:
        A JSON string containing code details, severity, possible causes, symptoms, and repair estimates.
    """
    clean_code = code.strip().upper()
    db = get_db()
    doc_ref = db.collection("obd2_codes").document(clean_code)
    doc = doc_ref.get()
    
    if not doc.exists:
        return json.dumps({
            "status": "not_found",
            "message": f"OBD2 code '{clean_code}' not found in the primary database. Please ask the user for vehicle symptoms or check if the code is typed correctly."
        })
    
    return json.dumps({"status": "found", "data": doc.to_dict()}, indent=2)

def list_common_obd2_codes() -> str:
    """Retrieve all diagnostic trouble codes currently stored in the OBD2 knowledge base.

    Returns:
        A JSON string with summary info for all available trouble codes.
    """
    db = get_db()
    docs = db.collection("obd2_codes").stream()
    codes = []
    for doc in docs:
        d = doc.to_dict()
        codes.append({
            "code": d.get("code"),
            "title": d.get("title"),
            "system": d.get("system"),
            "severity": d.get("severity"),
            "urgency": d.get("urgency")
        })
    return json.dumps({"status": "success", "count": len(codes), "codes": codes}, indent=2)

def get_vehicle_garage(vehicle_id: str = "veh_001") -> str:
    """Retrieve vehicle details and diagnostic history from the user's garage.

    Args:
        vehicle_id: The ID of the vehicle (defaults to 'veh_001').

    Returns:
        A JSON string containing the vehicle's year, make, model, mileage, and past logged codes.
    """
    db = get_db()
    doc_ref = db.collection("garage_vehicles").document(vehicle_id)
    doc = doc_ref.get()
    if not doc.exists:
        return json.dumps({
            "status": "not_found",
            "message": f"No vehicle found with ID '{vehicle_id}' in the garage."
        })
    return json.dumps({"status": "found", "vehicle": doc.to_dict()}, indent=2)

def log_diagnostic_event(
    code: str,
    vehicle_id: str = "veh_001",
    notes: str = ""
) -> str:
    """Log a newly detected OBD2 diagnostic trouble code to a vehicle's history in the garage.

    Args:
        code: The trouble code diagnosed (e.g. 'P0300').
        vehicle_id: The ID of the vehicle in the garage (defaults to 'veh_001').
        notes: Optional diagnosis or inspection notes from the user or mechanic.

    Returns:
        A JSON string confirming the update to the vehicle record.
    """
    clean_code = code.strip().upper()
    db = get_db()
    doc_ref = db.collection("garage_vehicles").document(vehicle_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return json.dumps({"status": "error", "message": f"Vehicle '{vehicle_id}' does not exist."})
    
    vehicle_data = doc.to_dict()
    logged_codes = vehicle_data.get("logged_codes", [])
    if clean_code not in logged_codes:
        logged_codes.append(clean_code)
        
    doc_ref.update({
        "logged_codes": logged_codes,
        "last_diagnostic_code": clean_code,
        "last_diagnostic_notes": notes
    })
    
    return json.dumps({
        "status": "success",
        "message": f"Logged code {clean_code} to vehicle {vehicle_id}.",
        "logged_codes": logged_codes
    })
