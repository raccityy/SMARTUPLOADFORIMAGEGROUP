from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from text_utils import code_wrap, html_escape

def handle_deposit(call):
    chat_id = call.message.chat.id
    image_url = 'https://raw.githubusercontent.com/raccityy/raccityy.github.io/refs/heads/main/deposit.jpg'
    text = (
        "💰 <b>deposit funds</b>\n\n"
        "kindly click on the <b>add</b> button to generate your wallet.\n"
        "💡 note that all your funds are safe with us."
    )
    markup = InlineKeyboardMarkup(row_width=2)
    # First row: one button
    markup.add(InlineKeyboardButton("➕ add", callback_data="deposit_add"))
    # Second row: two buttons
    markup.add(
        InlineKeyboardButton("💸 withdraw", callback_data="deposit_withdraw"),
        InlineKeyboardButton("💰 sol balance", callback_data="deposit_balance")
    )
    # Third row: back and menu buttons
    markup.add(
        InlineKeyboardButton("🔙 back", callback_data="deposit_back"),
        InlineKeyboardButton("🔝 main menu", callback_data="deposit_mainmenu")
    )
    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup) 