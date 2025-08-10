# bot.py
from decimal import Decimal
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN
from amadeus_api import search_validated_offers
import logging

logging.basicConfig(level=logging.INFO)

SERVICE_FEE_RUB = 10200  # fixed fee to add on top of validated price

# 🧠 Parse user input
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

# 🌍 Airport name to code mapping
def get_airport_code(city):
    city_map = {
        "Tashkent": "TAS",
        "Samarkand": "SKD",
        "Fergana": "FEG",
        "Urgench": "UGC",
        "Bukhara": "BHK",
        "Namangan": "NMA",
        "Andijan": "AZN",
        "Nukus": "NCU",
        "Moscow": "MOW",
        "Istanbul": "IST",
        "Dubai": "DXB",
        "Antalya": "AYT",
        "Jeddah": "JED",
        "Seoul": "ICN"
    }
    return city_map.get(city, city.upper())

# 📩 Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    origin, destination, date = parse_user_input(text)

    if not all([origin, destination, date]):
        await update.message.reply_text("❌ Please use: `Tashkent to Moscow on 2025-08-25`", parse_mode="Markdown")
        return

    try:
        origin_code = get_airport_code(origin)
        destination_code = get_airport_code(destination)

        await update.message.reply_text("🔎 Checking real, validated prices…")

        deals = search_validated_offers(origin_code, destination_code, date, adults=1, currency="RUB", max_results=5)

        if not deals:
            await update.message.reply_text("⚠️ No confirmed fares right now (offers changed while validating). Try another date or route.")
            return

        lines = [f"🛫 {origin} → {destination} on {date}\n(Validated just now ✅)\n"]
        for d in deals[:5]:
            base_price = Decimal(str(d['price_total']))
            final_price = base_price + Decimal(SERVICE_FEE_RUB)
            lines.append(
                f"✈️ {d['flight_no']} ({d.get('validating_airline','')})\n"
                f"   {d['dep_time']} → {d['arr_time']}\n"
                f"   💰 {final_price:.0f} {d['currency']}"
            )

        await update.message.reply_text("\n\n".join(lines))

    except Exception as e:
        print("Error:", str(e))
        await update.message.reply_text(f"❌ Error occurred: {str(e)}")

# 🚀 Main entry
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🟢 Sky Price Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
