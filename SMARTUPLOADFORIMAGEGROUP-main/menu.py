# import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot

# Link targets (replace with your real links)
PUMPFUN_URL = "https://pump.fun/"
RAYDIUM_URL = "https://raydium.io/"
PUMPSWAP_URL = "https://pumpswap.fun/"
MOONSHOT_URL = "https://moonshot.xyz/"
LETSBONK_URL = "https://letsbonk.com/"
DEXPAD_URL = "https://dexscreener.com/"  # Or your Dexpad/screener link

def start_message(message):
    chat_id = message.chat.id

    image_url = "https://github.com/raccityy/smart-second-bot/blob/main/statsmat.jpg?raw=true"

    text = (
        "🟢Welcome to <b>PUMPFUN TREND BOT</b> service!\n\n"
        "New to volume bots? No worries — we made it super simple!\n"
        "━━━━━━━━━━━━━━\n"
        "<b>How it works</b> :\n"
        "1. Select how much bumps/volume to use.\n"
        "2. Pick how long to run and how massive you want your token to pump.\n"
        "3. Done! Our server handles the rest.\n"
        "━━━━━━━━━━━━━\n"
        "<b>Works on</b>\n"
        f"(<a href=\"{PUMPFUN_URL}\">Pumpfun</a>) •  (<a href=\"{RAYDIUM_URL}\">Raydium</a>)\n"
        f"(<a href=\"{PUMPSWAP_URL}\">PumpSwap</a>) •  (<a href=\"{MOONSHOT_URL}\">Moonshot</a>)\n"
        f"(<a href=\"{LETSBONK_URL}\">LetsBonk</a>) •  (<a href=\"{DEXPAD_URL}\">Dexpad/Screener</a>)\n\n"
        "From 0.3–0.4–0.5–0.6 SOL bumps boost trend with massive volume and high stability."
    )

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




