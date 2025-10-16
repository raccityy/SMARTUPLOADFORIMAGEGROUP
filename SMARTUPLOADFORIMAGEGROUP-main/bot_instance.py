import os
import telebot
from telebot import TeleBot

# Load Telegram bot token securely from environment
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()

# Basic token validation: prevents starting with an obviously invalid/missing token
if not bot_token or ":" not in bot_token:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable. Set it before running the bot.")

bot = telebot.TeleBot(bot_token, parse_mode='HTML')
