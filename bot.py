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
        data = get_ets_prices()

        if not data or "offers" not in data:
            await update.message.reply_text("⚠️ Could not fetch prices right now.")
            return

        msg = f"🛫 {origin} → {destination} on {date}\n\n"
        for offer in data["offers"][:10]:  # Limit to 10 results
            price = offer.get("price", {}).get("amount", "???")
            airline = offer.get("validating_carrier", "Unknown")
            flight = offer.get("segments", [{}])[0].get("flight_number", "???")
            msg += f"✈️ {flight} ({airline}): ₽{price}\n"

        await update.message.reply_text(msg)
    except Exception as e:
        print(e)
        await update.message.reply_text("⚠️ Could not find flights. Check format or try later.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🟢 Sky Price Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
