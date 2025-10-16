# import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot

# Link targets with correct URLs
PUMPFUN_URL = "https://pump.fun/"
RAYDIUM_URL = "https://raydium.io/swap/?inputMint=sol&outputMint=4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R"
PUMPSWAP_URL = "https://swap.pump.fun/?input=So11111111111111111111111111111111111111112"
MOONSHOT_URL = "https://moonshot.money/"
LETSBONK_URL = "https://bonkcoin.com/"
DEXPAD_URL = "https://dexscreener.com/"

def start_message(message):
    chat_id = message.chat.id

    image_url = "https://github.com/raccityy/SMARTUPLOADFORIMAGEGROUP/blob/main/start.jpg?raw=true"

    text = (
        "🟢Welcome to <b>PUMPFUN TREND BOT</b> service!\n\n"
        "New to volume bots? No worries — we made it super simple!\n"
        "━━━━━━━━━━━━━━\n"
        "<b>How it works</b> :\n"
        "1. Select how much Bumps/volume to use.\n"
        "2. Pick how long to run and how Massive you want your Token to Pump.\n"
        "3. Done! Pump.fun Server handles the rest.\n"
        "━━━━━━━━━━━━━\n"
        "<b>Works on</b>\n"
        f":<a href=\"{PUMPFUN_URL}\">Pumpfun</a> •       :<a href=\"{RAYDIUM_URL}\">Raydium</a> •\n"
        f":<a href=\"{PUMPSWAP_URL}\">PumpSwap</a> •  :<a href=\"{MOONSHOT_URL}\">Moonshot</a> •\n"
        f":<a href=\"{LETSBONK_URL}\">LetsBonk</a> •     :<a href=\"{DEXPAD_URL}\">Dexpad/screener</a> •\n\n"
        "From 0.3-0.4-0.5-0.6 SOL bumps boost trend with mass volume of high stabilities."
    )

    markup = InlineKeyboardMarkup()
    start_button = InlineKeyboardButton("⚡️ Start B-Pump", callback_data="startbump")
    volume = InlineKeyboardButton("🧪 Volume Boost", callback_data="volume")
    premium = InlineKeyboardButton("💹Trending", callback_data="premium")
    deposit = InlineKeyboardButton("📥 Deposit", callback_data="deposit")
    stats = InlineKeyboardButton("📈 stats", callback_data="stats")
    connect = InlineKeyboardButton("🛡️ Connect wallet", callback_data="connect")
    dexscreener = InlineKeyboardButton("♻️ dex Trend", callback_data="dexscreener")
    support = InlineKeyboardButton("💬 Support", url="https://t.me/dogeuge")
    markup.add(start_button)
    markup.add(volume, premium)
    markup.add(deposit, stats)
    markup.add(connect, dexscreener)
    markup.add(support)



    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup)
    # bot.send_message(chat_id, text, reply_markup=markup, parse_mode="markdown")




