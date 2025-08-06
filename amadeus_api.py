import requests
from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET

def get_access_token():
    url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
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
    token = get_access_token()
    url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': date,
        'adults': 1,
        'currencyCode': 'RUB',
        'max': 3
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()
