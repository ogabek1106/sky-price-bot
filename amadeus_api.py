# amadeus_api.py
import os
import time
import requests
from typing import List, Dict, Any
from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET

BASE_URL = os.getenv("AMADEUS_HOST", "https://test.api.amadeus.com")

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
    return {"Authorization": f"Bearer {_get_access_token()}",
            "Content-Type": "application/json"}

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
    priced = r.json()["data"]["flightOffers"][0]
    return priced

def _normalize(priced_offer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract what the bot needs to display, from a priced offer.
    """
    price_total = priced_offer["price"]["grandTotal"] if "grandTotal" in priced_offer["price"] else priced_offer["price"]["total"]
    validating = None
    if priced_offer.get("validatingAirlineCodes"):
        validating = priced_offer["validatingAirlineCodes"][0]

    # Basic times/flight number from first & last segments
    segs = priced_offer["itineraries"][0]["segments"]
    first, last = segs[0], segs[-1]
    dep_time = first["departure"]["at"]
    arr_time = last["arrival"]["at"]
    flight_no = f'{first["carrierCode"]}{first["number"]}'

    return {
        "price_total": price_total,
        "currency": priced_offer["price"].get("currency", "RUB"),
        "validating_airline": validating,
        "flight_no": flight_no,
        "dep_time": dep_time,
        "arr_time": arr_time,
        "raw": priced_offer,  # keep full payload for later booking if needed
    }

def search_validated_offers(origin: str, destination: str, date: str, adults: int = 1, currency: str = "RUB", max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search → immediately re-price → return only *validated* offers (normalized).
    """
    # 1) Search (candidate fares; not final)
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

    # 2) Re-price top N and keep only successful ones
    confirmed: List[Dict[str, Any]] = []
    for c in candidates:
        try:
            priced = _price_offer(c)
            confirmed.append(_normalize(priced))
        except Exception:
            # offer vanished or price changed too much -> skip it
            continue

    # 3) Sort by final price
    confirmed.sort(key=lambda x: float(x["price_total"]))
    return confirmed
