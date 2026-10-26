import json
import os
import urllib.parse
import urllib.request
import requests
import google.auth
import google.auth.transport.requests
from typing import Optional, Dict, Any, List

PROJECT_ID = "qwiklabs-gcp-03-3ff306ba56bc"

def _get_api_key() -> str:
    """Read Google Maps API Key from environment."""
    return os.getenv("GOOGLE_MAPS_API_KEY", "").strip()

def _get_auth_headers_for_places() -> Dict[str, str]:
    """Get headers for Places API (New), using API key if set or ADC Bearer token."""
    api_key = _get_api_key()
    field_mask = "places.displayName,places.formattedAddress,places.location"

    if api_key:
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": field_mask
        }

    # Fallback to Application Default Credentials
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {credentials.token}",
        "X-Goog-User-Project": PROJECT_ID,
        "X-Goog-FieldMask": field_mask
    }

def geocode_address(address: str) -> str:
    """Use Google Maps Geocoding API to turn a street address or city into latitude and longitude coordinates.

    Args:
        address: The street address, city, or postal code to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'San Francisco, CA').

    Returns:
        A JSON string containing the formatted address and location coordinates (latitude and longitude).
    """
    clean_address = address.strip()
    api_key = _get_api_key()
    encoded_address = urllib.parse.quote(clean_address)

    if api_key:
        # Standard Geocoding API v3
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
        headers = {}
    else:
        # Geocoding API v4 (Google Cloud Standard Platform with ADC)
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        url = f"https://geocode.googleapis.com/v4beta/geocode/address?addressQuery={encoded_address}"
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "X-Goog-User-Project": PROJECT_ID
        }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Geocoding request failed: {str(e)}"
        })

    # Parse response
    results = data.get("results", [])
    if results and len(results) > 0:
        first = results[0]
        # In v3: geometry.location.{lat, lng}; in v4: location.{latitude, longitude}
        loc = first.get("geometry", {}).get("location")
        if loc:
            lat = loc.get("lat")
            lng = loc.get("lng")
        else:
            loc_v4 = first.get("location", {})
            lat = loc_v4.get("latitude")
            lng = loc_v4.get("longitude")

        fmt_address = first.get("formattedAddress") or first.get("formatted_address", clean_address)

        return json.dumps({
            "status": "success",
            "formatted_address": fmt_address,
            "location": {
                "latitude": lat,
                "longitude": lng
            }
        }, indent=2)

    return json.dumps({
        "status": "not_found",
        "message": f"No geocoding results found for '{clean_address}'."
    })

def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "car_repair",
    radius_meters: float = 5000.0,
    max_results: int = 5
) -> str:
    """Use Google Places API (New) searchNearby endpoint to find nearby places of a specific type
    around given geographic coordinates.

    Args:
        latitude: Latitude coordinate of the search center.
        longitude: Longitude coordinate of the search center.
        place_type: Type of place to search for (e.g. 'car_repair', 'car_parts_store', 'car_dealer', 'gas_station').
        radius_meters: Radius in meters around the center coordinates (default 5000.0, up to 50000.0).
        max_results: Maximum results to return (default 5).

    Returns:
        A JSON string containing the key fields: name, address, and location (latitude/longitude) for each place.
    """
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = _get_auth_headers_for_places()

    payload = {
        "includedTypes": [place_type],
        "maxResultCount": min(max(max_results, 1), 10),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude)
                },
                "radius": float(radius_meters)
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Places API returned HTTP {response.status_code}: {response.text}"
            })

        data = response.json()
        raw_places = data.get("places", [])
        
        places = []
        for p in raw_places:
            display_name = p.get("displayName", {}).get("text", "Unknown Place")
            address = p.get("formattedAddress", "No address provided")
            loc = p.get("location", {})
            places.append({
                "name": display_name,
                "address": address,
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude")
                }
            })

        return json.dumps({
            "status": "success",
            "place_type": place_type,
            "center": {"latitude": latitude, "longitude": longitude},
            "count": len(places),
            "places": places
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to search nearby places: {str(e)}"
        })
