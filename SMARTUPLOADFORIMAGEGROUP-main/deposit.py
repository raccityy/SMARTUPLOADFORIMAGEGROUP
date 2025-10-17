from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from text_utils import code_wrap, html_escape

def handle_deposit(call):
    chat_id = call.message.chat.id
    image_url = 'https://raw.githubusercontent.com/raccityy/raccityy.github.io/refs/heads/main/deposit.jpg'
    text = (
        "💰 <b>DEPOSIT FUNDS</b>\n\n"
        "Kindly click on the <b>Add</b> button to generate your wallet.\n"
        "💡 Note that all your funds are safe with us."
    )
    markup = InlineKeyboardMarkup(row_width=2)
    # First row: one button
    markup.add(InlineKeyboardButton("➕ Add", callback_data="deposit_add"))
    # Second row: two buttons
    markup.add(
        InlineKeyboardButton("💸 Withdraw", callback_data="deposit_withdraw"),
        InlineKeyboardButton("💰 SOL Balance", callback_data="deposit_balance")
    )
    # Third row: back and menu buttons
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data="deposit_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="deposit_mainmenu")
    )
    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup) 