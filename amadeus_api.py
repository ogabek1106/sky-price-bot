# amadeus_api.py
import os
import time
import requests
from typing import List, Dict, Any
from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, AMADEUS_HOST

BASE_URL = os.getenv("AMADEUS_HOST", AMADEUS_HOST or "https://test.api.amadeus.com")

# --- tiny token cache so we don't request a token every call ---
_token = {"value": None, "exp": 0}

def _get_access_token() -> str:
    now = int(time.time())
    if _token["value"] and now < _token["exp"] - 30:
        return _token["value"]

    url = f"{BASE_URL}/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET,
    }
    r = requests.post(url, headers=headers, data=data, timeout=25)
    r.raise_for_status()
    j = r.json()
    _token["value"] = j["access_token"]
    _token["exp"]   = int(time.time()) + int(j.get("expires_in", 1800))
    return _token["value"]

def _auth_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json"
    }

def _price_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Confirm (re-price) one search offer.
    Returns the *priced* offer payload (not the raw search hit).
    """
    url = f"{BASE_URL}/v1/shopping/flight-offers/pricing"
    payload = {
        "data": {
            "type": "flight-offers-pricing",
            "flightOffers": [offer]
        }
    }
    r = requests.post(url, headers=_auth_headers(), json=payload, timeout=40)
    r.raise_for_status()
    return r.json()["data"]["flightOffers"][0]

def search_hy_all_classes(
    origin: str,
    destination: str,
    date: str,
    adults: int = 1,
    currency: str = "RUB",
    max_results: int = 50
) -> List[Dict[str, Any]]:
    """
    Search HY flights → immediately re-price → group by exact flight and show all available classes.
    """
    search_url = f"{BASE_URL}/v2/shopping/flight-offers"
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": date,
        "adults": adults,
        "currencyCode": currency,
        "max": max_results,
    }
    r = requests.get(search_url, headers=_auth_headers(), params=params, timeout=35)
    r.raise_for_status()
    candidates = r.json().get("data", [])

    flights_map: Dict[tuple, Dict] = {}

    for c in candidates:
        try:
            priced = _price_offer(c)

            # Filter to HY flights only
            first_seg = priced["itineraries"][0]["segments"][0]
            if first_seg["carrierCode"] != "HY":
                continue

            dep_airport = first_seg["departure"]["iataCode"]
            arr_airport = priced["itineraries"][0]["segments"][-1]["arrival"]["iataCode"]
            flight_no = f"{first_seg['carrierCode']} {first_seg['number']}"
            dep_time_iso = first_seg["departure"]["at"]
            dep_hhmm = dep_time_iso.split("T")[1][:5] if "T" in dep_time_iso else dep_time_iso

            # Get cabin + booking class
            tp = priced.get("travelerPricings", [])[0]
            fare_info = tp.get("fareDetailsBySegment", [])[0]
            cabin = fare_info.get("cabin", "").title()
            booking_class = fare_info.get("class", "")

            # Price
            price_total = priced["price"].get("grandTotal") or priced["price"]["total"]
            currency_code = priced["price"].get("currency", currency)

            key = (flight_no, dep_hhmm)  # group by exact flight & departure time

            if key not in flights_map:
                flights_map[key] = {
                    "dep_airport": dep_airport,
                    "arr_airport": arr_airport,
                    "flight_no": flight_no,
                    "dep_time": dep_hhmm,
                    "classes": []
                }

            flights_map[key]["classes"].append({
                "cabin": cabin,
                "booking_class": booking_class,
                "price_total": price_total,
                "currency": currency_code
            })

        except Exception:
            continue

    # Sort classes inside each flight by price
    for flight in flights_map.values():
        flight["classes"].sort(key=lambda x: float(x["price_total"]))

    return list(flights_map.values())
