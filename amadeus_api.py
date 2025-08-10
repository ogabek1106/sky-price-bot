# amadeus_api.py
import os
import requests
from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET

BASE_URL = os.getenv("AMADEUS_HOST", "https://test.api.amadeus.com")

def get_access_token():
    url = f"{BASE_URL}/v1/security/oauth2/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': AMADEUS_CLIENT_ID,
        'client_secret': AMADEUS_CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']

def search_flights(origin, destination, date):
    """Search flights and immediately re-price top results to avoid ghost fares."""
    token = get_access_token()

    # Step 1 — Search
    search_url = f"{BASE_URL}/v2/shopping/flight-offers"
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': date,
        'adults': 1,
        'currencyCode': 'RUB',
        'max': 3
    }
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(search_url, headers=headers, params=params)
    resp.raise_for_status()
    offers = resp.json().get('data', [])

    confirmed_offers = []
    for offer in offers:
        try:
            priced = price_offer(token, offer)
            confirmed_offers.append(priced)
        except Exception:
            continue

    return confirmed_offers

def price_offer(token, offer):
    """Confirm price for a given offer (final step before showing to user)."""
    price_url = f"{BASE_URL}/v1/shopping/flight-offers/pricing"
    payload = {
        "data": {
            "type": "flight-offers-pricing",
            "flightOffers": [offer]
        }
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    resp = requests.post(price_url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()
