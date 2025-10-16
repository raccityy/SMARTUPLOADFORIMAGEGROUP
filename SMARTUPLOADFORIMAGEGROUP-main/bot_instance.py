import os
import telebot
from telebot import TeleBot

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not bot_token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Set it as an environment variable before starting the bot.")

bot = telebot.TeleBot(bot_token, parse_mode='HTML')
