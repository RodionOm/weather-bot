# WeatherBot (Telegram)

A simple Telegram bot that shows the **current weather** and a **compact 3‑day forecast** using OpenWeatherMap.

## Features

* Button menu: **Help**, **Weather**, **Today**, **Forecast**, **📍 My city**, **⬅️ Back to Menu**.
* Remembers your last city.
* Weather emojis and neat Markdown formatting.
* Expects city names **in English**.

## Requirements 

* Python **3.10+**.
* Accounts/keys:

  * **Telegram Bot Token** (via @BotFather)
  * **OpenWeatherMap API key** ([https://openweathermap.org/](https://openweathermap.org/))

## Installation & Run

```bash
# 1) Clone the repository
git clone <repo_url>
cd <repo_folder>

# 2) (recommended) Create & activate a virtual env
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate

# 3) Install dependencies (pinned)
pip install -U pip
pip install -r requirements.txt

# 4) Create a .env file next to app.py and fill your keys
# (You can also keep a .env.example in the repo.)

# 5) Start the bot
python app.py
```

## Environment variables (.env)

The **.env** file must be in the same folder as `app.py`.

```env
BOT_TOKEN=123456789:AA...            # Telegram bot token
OWM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx # OpenWeatherMap API key
```

If any variable is missing, the app will stop with a clear error.

## Project structure

```
project/
├─ app.py          # bot code (handlers, menus, OWM requests)
├─ .env            # your secrets (do NOT commit)
├─ .env.example    # optional template (no secrets)
├─ requirements.txt
└─ .gitignore
```

## How it works (brief)

* Polling via `ApplicationBuilder().token(TOKEN).build()` and `run_polling()`.
* Requests to OWM endpoints: `https://api.openweathermap.org/data/2.5/weather` and `.../forecast` with `units=metric&lang=en`.
* Timestamps are converted to local time using the city timezone offset from OWM.
* Forecast shows \~now / +24h / +48h (indices 0, 8, 16 in the 3‑hour forecast list).

## Troubleshooting

* **`Error: BOT_TOKEN is empty` / `OWM_API_KEY is empty`** — check your `.env` location (same folder as `app.py`) and values.
* **Bot doesn’t respond** — ensure `python app.py` is running, the token is valid, and you have internet access.
* **City not found** — check spelling in English (e.g., `Kyiv`, `New York`).

## License

MIT
