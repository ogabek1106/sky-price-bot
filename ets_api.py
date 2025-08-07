# ets_api.py

import requests

HEADERS = {
    "Content-Type": "application/json",
    "Cookie": "_clck=f8qmwv%7C2%7Cfy9%7C0%7C1918; etmsessid=5mVX7xxQwRIIYkVGU2CkUF9kreB0aZIDsh0lA4u6; laravel_session=eyJpdiI6InZKUnFDa2pReHd6NXQrZDVabDNpdEE9PSIsInZhbHVlIjoid2dONWZ6Z01nY2pYcU9wQWxycTA1QjJXWFFPVUorY1Jyb1BpNDJpeW1USk5sMmhJNTk0ay80RWhsWExJNWdxTmx2bnVMT2tGMXgyVkJ6RXBGY2tuM0dEampLTWR1VjI1UjcvQlduSmdmUUkvbVhrd3JNbVJMNHl1cGJTczRBajgiLCJtYWMiOiIwYmQwOWJhYjQ0MzIyY2NjMDNjZTM1ZDYyZDcyODhiZTNlY2E2MjM3YmM0NjEyZTdjMWJmNDI3ZmQwMTdiOGE0IiwidGFnIjoiIn0%3D; _clsk=1nzrked%7C1754565399909%7C4%7C1%7Cn.clarity.ms%2Fcollect"
}

NEXT_TOKEN_PAYLOAD = {
    "request_id": "f032d4de-b646-418a-971e-b8857a401f0c",
    "sort": "price",
    "next_token": "eyJpdiI6IkxDZ281YUU4V1Zmdmx6cXljd21EQnc9PSIsInZhbHVlIjoiUTlVa054..."
    # (Your full token inserted here — already done by me)
}


def get_ets_prices(origin_code, destination_code, date):
    try:
        url = "https://b2b.easybooking.uz/api/air/offers"
        response = requests.post(url, headers=HEADERS, json=NEXT_TOKEN_PAYLOAD)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("❌ API request failed:", e)
        return None
