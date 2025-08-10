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
    priced = r.json()["data"]["flightOffers"][0]
    return priced

def _normalize(priced_offer: dict) -> dict:
    """
    Extract display fields for the bot.
    """
    # first itinerary / first segment (outbound, first leg)
    segs = priced_offer["itineraries"][0]["segments"]
    first = segs[0]
    dep_airport = first["departure"]["iataCode"]
    arr_airport = segs[-1]["arrival"]["iataCode"]

    # flight number like "HY 604"
    marketing = first["carrierCode"]
    number = first["number"]
    flight_no = f"{marketing} {number}"

    # time "HH:MM" from ISO (local time as returned by Amadeus)
    dep_time_iso = first["departure"]["at"]  # e.g., "2025-08-25T11:45:00"
    dep_hhmm = dep_time_iso.split("T")[1][:5] if "T" in dep_time_iso else dep_time_iso

    # cabin + booking class (K, Y, etc.) — from travelerPricings[0]
    cabin = "ECONOMY"
    booking_class = ""
    try:
        first_seg_id = first["id"]
        tp = priced_offer.get("travelerPricings", [])[0]
        for f in tp.get("fareDetailsBySegment", []):
            if str(f.get("segmentId")) == str(first_seg_id):
                cabin = f.get("cabin", cabin)          # e.g., "ECONOMY"
                booking_class = f.get("class", "")     # e.g., "K"
                break
    except Exception:
        pass

    # price
    price_total = priced_offer["price"].get("grandTotal") or priced_offer["price"]["total"]
    currency = priced_offer["price"].get("currency", "RUB")

    return {
        "dep_airport": dep_airport,
        "arr_airport": arr_airport,
        "flight_no": flight_no,
        "dep_time": dep_hhmm,
        "cabin": cabin.title(),         # "Economy"
        "booking_class": booking_class, # "K"
        "price_total": price_total,
        "currency": currency,
        "raw": priced_offer,
    }

def search_validated_offers(
    origin: str,
    destination: str,
    date: str,
    adults: int = 1,
    currency: str = "RUB",
    max_results: int = 5
) -> List[Dict[str, Any]]:
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
