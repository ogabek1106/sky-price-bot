import os
from dotenv import load_dotenv

# Load .env file locally (ignored in Railway deployment)
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Amadeus API Credentials
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# Amadeus API Host
# Default to test environment; override in Railway vars when going live
AMADEUS_HOST = os.getenv("AMADEUS_HOST", "https://test.api.amadeus.com")
