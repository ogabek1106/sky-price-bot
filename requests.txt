import httpx

# Your cookies
cookies = {
    "_clck": "f8qmwv%7C2%7Cfy9%7C0%7C1918",
    "etmsessid": "5mVX7xxQwRIIYkVGU2CkUF9kreB0aZIDsh0lA4u6",
    "laravel_session": "eyJpdiI6InZKUnFDa2pReHd6NXQrZDVabDNpdEE9PSIsInZhbHVlIjoid2dONWZ6Z01nY2pYcU9wQWxycTA1QjJXWFFPVUorY1Jyb1BpNDJpeW1USk5sMmhJNTk0ay80RWhsWExJNWdxTmx2bnVMT2tGMXgyVkJ6RXBGY2tuM0dEampLTWR1VjI1UjcvQlduSmdmUUkvbVhrd3JNbVJMNHl1cGJTczRBajgiLCJtYWMiOiIwYmQwOWJhYjQ0MzIyY2NjMDNjZTM1ZDYyZDcyODhiZTNlY2E2MjM3YmM0NjEyZTdjMWJmNDI3ZmQwMTdiOGE0IiwidGFnIjoiIn0%3D",
    "_clsk": "1nzrked%7C1754565399909%7C4%7C1%7Cn.clarity.ms%2Fcollect"
}

# Your payload with next_token and request_id
payload = {
    "request_id": "f032d4de-b646-418a-971e-b8857a401f0c",
    "sort": "price",
    "next_token": "eyJpdiI6IkxDZ281YUU4V1Zmdmx6cXljd21EQnc9PSIsInZhbHVlIjoiUTlVa054ck1jOThta..."
}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://b2b.easybooking.uz",
    "Referer": "https://b2b.easybooking.uz/"
}

url = "https://b2b.easybooking.uz/api/air/offers"

# Function to fetch data
def fetch_flight_offers():
    try:
        response = httpx.post(url, headers=headers, cookies=cookies, json=payload, timeout=15.0)

        if response.status_code == 200:
            data = response.json()
            return data.get("data")  # List of offers
        else:
            print("❌ Failed:", response.status_code, response.text)
            return None

    except Exception as e:
        print("🚨 Error:", e)
        return None

# For local test
if __name__ == "__main__":
    offers = fetch_flight_offers()
    if offers:
        print(f"✅ Found {len(offers)} offers")
        for offer in offers[:3]:
            print(offer)
    else:
        print("❌ No offers found.")
