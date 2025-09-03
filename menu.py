# import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot

def start_message(message):
    chat_id = message.chat.id

    image_url = "https://github.com/raccityy/smart-second-bot/blob/main/statsmat.jpg?raw=true"

    text = """
Welcome to Pumpfun Bumper Bot

The fastest and cheapest Telegram bot for creating bump orders.

Supported Platform: Pumpfun and Raydium.

Pumpfun BumpBot

charges a one time  fee of 0.3,0.4,0.5,0.6SOL per token, making it the cheapest bump bot ever!


trending channel:
https://t.me/pumpmints
"""

    markup = InlineKeyboardMarkup()
    start_button = InlineKeyboardButton("🟢Start bumping", callback_data="startbump")
    volume = InlineKeyboardButton("💉Volume Boost", callback_data="volume")
    premium = InlineKeyboardButton("♻️Premium Trend", callback_data="premium")
    deposit = InlineKeyboardButton("💹Deposit", callback_data="deposit")
    connect = InlineKeyboardButton("🛡️Connect wallet", callback_data="connect")
    dexscreener = InlineKeyboardButton("⭕Dexscreener", callback_data="dexscreener")
    support = InlineKeyboardButton("💬SUPPORT", url="https://t.me/dogeuge")
    markup.add(start_button)
    markup.add(volume, premium)
    markup.add(deposit, connect)
    markup.add(dexscreener, support)



    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup)
    # bot.send_message(chat_id, text, reply_markup=markup, parse_mode="markdown")




