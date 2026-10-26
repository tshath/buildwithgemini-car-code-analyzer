import json
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any, List

def fetch_nhtsa_recalls(make: str, model: str, year: int) -> str:
    """Fetch official safety recalls from the National Highway Traffic Safety Administration (NHTSA) API
    for a specific vehicle make, model, and year.

    Args:
        make: Vehicle make (e.g. 'Honda', 'Toyota', 'Ford', 'Chevrolet').
        model: Vehicle model (e.g. 'Civic', 'Camry', 'F-150', 'Silverado').
        year: Model year (e.g. 2018, 2021).

    Returns:
        A JSON string containing the count and list of active safety recalls, affected components,
        hazard summaries, consequences, and free dealer remedies.
    """
    clean_make = urllib.parse.quote(make.strip())
    clean_model = urllib.parse.quote(model.strip())
    clean_year = int(year)

    url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={clean_make}&model={clean_model}&modelYear={clean_year}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PitStop-AI/1.0 (Automotive Diagnostic Assistant)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to retrieve NHTSA recall data: {str(e)}"
        })

    raw_results = data.get("results", [])
    recalls = []
    for item in raw_results:
        recalls.append({
            "campaign_number": item.get("NHTSACampaignNumber"),
            "component": item.get("Component"),
            "summary": item.get("Summary"),
            "consequence": item.get("Consequence"),
            "remedy": item.get("Remedy"),
            "report_date": item.get("ReportReceivedDate"),
            "manufacturer": item.get("Manufacturer")
        })

    return json.dumps({
        "status": "success",
        "vehicle": f"{year} {make} {model}",
        "recall_count": len(recalls),
        "recalls": recalls
    }, indent=2)
