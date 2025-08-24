# app.py
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------- env ----------
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

TOKEN = os.getenv("BOT_TOKEN")
OWM_KEY = os.getenv("OWM_API_KEY")

if not TOKEN:
    raise RuntimeError("Error: BOT_TOKEN is empty. Check your .env file")
if not OWM_KEY:
    raise RuntimeError("Error: OWM_API_KEY is empty. Check your .env file")

# ---------- logging ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ---------- constants ----------
BASE_URL = "https://api.openweathermap.org/data/2.5/"

WEATHER_EMOJI = {
    "Clear":        "☀️",
    "Clouds":       "☁️",
    "Rain":         "🌧️",
    "Drizzle":      "🌦️",
    "Thunderstorm": "⛈️",
    "Snow":         "❄️",
    "Mist":         "🌫️",
}

START_TEXT = "Hi! I’m WeatherBot 🌤️\n\nChoose an action:"

def main_menu_markup(user_data: dict | None = None):
    rows = [
        [InlineKeyboardButton("Help ℹ️", callback_data="help")],
        [InlineKeyboardButton("Weather ☀️", callback_data="weather")],
    ]
    if user_data and user_data.get("last_city"):
        rows.append([InlineKeyboardButton("📍 My city", callback_data="my_city")])
    return InlineKeyboardMarkup(rows)

def weather_menu_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Today 🌤️", callback_data="today"),
            InlineKeyboardButton("Forecast 🌦️", callback_data="forecast"),
        ],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
    ])

# ---------- helpers ----------
def get_weather_emoji(main: str) -> str:
    return WEATHER_EMOJI.get(main, "🌈")

def format_timestamp_local(ts: int, tz_offset_sec: int) -> str:
    # Convert UTC timestamp + city timezone offset to local date/time
    return (datetime.utcfromtimestamp(ts) + timedelta(seconds=tz_offset_sec)).strftime("%d.%m %H:%M")

def request_json(endpoint: str, params: dict) -> dict:
    params = {**params, "appid": OWM_KEY, "units": "metric", "lang": "en"}
    try:
        r = requests.get(BASE_URL + endpoint, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logging.exception("HTTP error: %s", e)
        return {"_error": True}

def get_current_weather(city: str) -> str:
    data = request_json("weather", {"q": city})
    if data.get("_error"):
        return "❌ Weather service request failed. Please try again later."
    if data.get("cod") != 200:
        return f"❌ I can’t find the city “{city}”"

    w = data["weather"][0]
    m = data["main"]
    wind = data.get("wind", {})
    tz = int(data.get("timezone", 0))
    time_str = format_timestamp_local(data.get("dt", 0), tz)

    feels = m.get("feels_like")
    hum = m.get("humidity")
    speed = wind.get("speed")

    extras = []
    if feels is not None:
        extras.append(f"feels like {feels}°C")
    if speed is not None:
        extras.append(f"wind {speed} m/s")
    if hum is not None:
        extras.append(f"humidity {hum}%")
    extra_str = f" ({', '.join(extras)})" if extras else ""

    return (
        f"{get_weather_emoji(w['main'])} *Current weather in {city.title()}:* "
        f"{w['description'].capitalize()}, {m['temp']}°C{extra_str}\n"
        f"_Updated: {time_str}_"
    )

def get_three_day_forecast(city: str) -> str:
    data = request_json("forecast", {"q": city})
    if data.get("_error"):
        return "❌ Weather service request failed. Please try again later."
    if str(data.get("cod")) != "200":
        return f"❌ I can’t find the city “{city}”"

    tz = int(data["city"].get("timezone", 0))
    lines = [f"📅 *3-day forecast for {city.title()}:*"]
    # take ~now, +24h, +48h (API step 3h -> indices 0, 8, 16)
    for i in (0, 8, 16):
        entry = data["list"][i]
        dt_str = format_timestamp_local(entry["dt"], tz)
        main = entry["weather"][0]["main"]
        desc = entry["weather"][0]["description"].capitalize()
        temp = entry["main"]["temp"]
        lines.append(f"{get_weather_emoji(main)} {dt_str}: {desc}, {temp}°C")
    return "\n".join(lines)

# ---------- handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        START_TEXT,
        reply_markup=main_menu_markup(context.user_data),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "I can:\n"
        "• Help ℹ️ — show this message\n"
        "• Weather ☀️ — choose Today 🌤️ or Forecast 🌦️\n"
        "Then enter a city in English.\n\n"
        "Tip: after you’ve looked up a city once, use “📍 My city”.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]]
        ),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "help":
        await query.edit_message_text(
            "I can:\n"
            "• Help ℹ️ — show this message\n"
            "• Weather ☀️ — choose Today 🌤️ or Forecast 🌦️\n"
            "Then enter a city in English.\n\n"
            "Tip: after you’ve looked up a city once, use “📍 My city”.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]]
            ),
        )

    elif data == "weather":
        await query.edit_message_text("What would you like to see?",
                                      reply_markup=weather_menu_markup())

    elif data in ("today", "forecast"):
        context.user_data["mode"] = data
        context.user_data["awaiting_city"] = True
        await query.edit_message_text(
            "Please enter a city in English:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]]
            ),
        )

    elif data == "menu":
        context.user_data["awaiting_city"] = False
        await query.edit_message_text(
            START_TEXT,
            reply_markup=main_menu_markup(context.user_data)
        )

    elif data == "my_city":
        city = context.user_data.get("last_city")
        if not city:
            await query.edit_message_text(
                "No city saved yet. Tap Weather ☀️ and enter a city.",
                reply_markup=main_menu_markup(context.user_data),
            )
            return
        mode = context.user_data.get("mode", "today")
        resp = get_current_weather(city) if mode == "today" else get_three_day_forecast(city)
        await query.edit_message_text(
            resp,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        await query.message.reply_text(
            START_TEXT,
            reply_markup=main_menu_markup(context.user_data),
        )

async def city_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only handle text when we expect a city
    if not context.user_data.get("awaiting_city"):
        return await start(update, context)

    city = update.effective_message.text.strip()
    mode = context.user_data.get("mode", "today")
    resp = get_current_weather(city) if mode == "today" else get_three_day_forecast(city)

    await update.effective_message.reply_text(
        resp,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )
    # remember city for "📍 My city"
    context.user_data["last_city"] = city.title()
    context.user_data["awaiting_city"] = False
    await start(update, context)

# ---------- lifecycle ----------
async def on_start(app):
    me = await app.bot.get_me()
    logging.info("✅ Bot is up: @%s (id=%s)", me.username, me.id)

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, city_handler))

    app.post_init = on_start
    logging.info("🚀 Starting polling...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()
