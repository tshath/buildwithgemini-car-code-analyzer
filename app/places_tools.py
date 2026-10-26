import json
import os
import requests
import google.auth
import google.auth.transport.requests
from typing import Optional, Dict, Any, List

PROJECT_ID = "qwiklabs-gcp-03-3ff306ba56bc"

def _get_auth_headers() -> Dict[str, str]:
    """Obtain credentials for Places API (supports API key from env or ADC Bearer token)."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if api_key:
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.googleMapsUri,places.regularOpeningHours.openNow"
        }

    # Use Application Default Credentials (OAuth2 Bearer token)
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {credentials.token}",
        "X-Goog-User-Project": PROJECT_ID,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.googleMapsUri,places.regularOpeningHours.openNow"
    }

def find_nearby_auto_services(
    query: str,
    location: str = "San Francisco, CA",
    max_results: int = 4
) -> str:
    """Search for nearby auto repair shops, brand dealerships, or auto parts stores using Google Places API (New).
    Provides ratings, full street addresses, open/closed status, and direct Google Maps navigation links.

    Args:
        query: Search term (e.g., 'AutoZone auto parts', 'Honda dealership service center', 'Brake and exhaust mechanic').
        location: City, neighborhood, or address (defaults to 'San Francisco, CA').
        max_results: Maximum number of places to return (default 4).

    Returns:
        A JSON string containing the list of matching places with names, ratings, addresses,
        open status, and Google Maps navigation URLs.
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    full_text_query = f"{query} near {location}".strip()

    try:
        headers = _get_auth_headers()
        payload = {
            "textQuery": full_text_query,
            "pageSize": min(max(max_results, 1), 10)
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Places API returned HTTP {response.status_code}: {response.text}"
            })

        data = response.json()
        raw_places = data.get("places", [])
        
        results = []
        for p in raw_places[:max_results]:
            name = p.get("displayName", {}).get("text", "Unknown Auto Service")
            address = p.get("formattedAddress", "")
            rating = p.get("rating")
            rating_count = p.get("userRatingCount")
            maps_uri = p.get("googleMapsUri")
            opening_hours = p.get("regularOpeningHours", {})
            is_open = opening_hours.get("openNow")

            results.append({
                "name": name,
                "rating": rating,
                "review_count": rating_count,
                "address": address,
                "is_open_now": is_open,
                "maps_url": maps_uri
            })

        return json.dumps({
            "status": "success",
            "query": full_text_query,
            "count": len(results),
            "places": results
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to search places: {str(e)}"
        })
