from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from ets_api import get_ets_prices
from config import BOT_TOKEN
import logging

logging.basicConfig(level=logging.INFO)

def parse_user_input(text):
    try:
        parts = text.lower().split(" to ")
        origin = parts[0].strip().title()
        rest = parts[1].split(" on ")
        destination = rest[0].strip().title()
        date = rest[1].strip()
        return origin, destination, date
    except Exception:
        return None, None, None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    origin, destination, date = parse_user_input(text)

    if not all([origin, destination, date]):
        await update.message.reply_text("❌ Please use format: `Tashkent to Moscow on 2025-08-25`")
        return

    try:
    origin_code = get_airport_code(origin)
    destination_code = get_airport_code(destination)
    data = search_flights(origin_code, destination_code, date)

    if not data or "data" not in data or not data["data"]:
        await update.message.reply_text("⚠️ No flights found. This might be because your cookies or `next_token` are expired. Please update them.")
        return

    msg = f"🛫 {origin} → {destination} on {date}\n\n"
    for offer in data["data"]:
        price = offer["price"]["total"]
        airline = offer["validatingAirlineCodes"][0]
        flight = offer["itineraries"][0]["segments"][0]["carrierCode"] + offer["itineraries"][0]["segments"][0]["number"]
        msg += f"✈️ {flight}: ₽{price}\n"

    await update.message.reply_text(msg)

except KeyError as e:
    print("KeyError:", str(e))
    await update.message.reply_text(f"❌ Missing expected data in response: {str(e)}")

except Exception as e:
    print("Error:", str(e))
    await update.message.reply_text(f"❌ Error occurred: {str(e)}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🟢 Sky Price Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
