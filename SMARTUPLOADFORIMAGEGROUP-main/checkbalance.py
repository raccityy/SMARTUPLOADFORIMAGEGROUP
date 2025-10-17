# Balance and Order Management for PUMPFUN TREND BOT
import time
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot

# File to store user balances and orders
BALANCE_FILE = "user_balances.json"

def load_balances():
    """Load user balances from file"""
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_balances(balances):
    """Save user balances to file"""
    with open(BALANCE_FILE, 'w') as f:
        json.dump(balances, f, indent=2)

def get_user_balance(user_id):
    """Get user's current balance"""
    balances = load_balances()
    return balances.get(str(user_id), 0.0)

def update_user_balance(user_id, amount, tx_hash=None):
    """Update user's balance and add transaction record"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str not in balances:
        balances[user_id_str] = {
            'balance': 0.0,
            'transactions': []
        }
    
    # Update balance
    balances[user_id_str]['balance'] += amount
    
    # Add transaction record
    if tx_hash:
        transaction = {
            'tx_hash': tx_hash,
            'amount': amount,
            'timestamp': time.time(),
            'type': 'deposit' if amount > 0 else 'withdrawal'
        }
        balances[user_id_str]['transactions'].append(transaction)
    
    save_balances(balances)
    return balances[user_id_str]['balance']

def get_user_orders(user_id):
    """Get user's order history"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str not in balances:
        return []
    
    return balances[user_id_str].get('transactions', [])

def show_balance_menu(call):
    """Show the main balance menu"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    # Get user's current balance
    balance = get_user_balance(user_id)
    orders = get_user_orders(user_id)
    
    # Calculate recent activity
    recent_orders = orders[-5:] if orders else []
    
    balance_text = f"""
💰 <b>YOUR ACCOUNT BALANCE</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💳 <b>CURRENT BALANCE</b>
• Available: <b>{balance:.4f} SOL</b>
• Status: <b>{"🟢 Active" if balance > 0 else "🔴 No Funds"}</b>

📊 <b>ACCOUNT SUMMARY</b>
• Total Orders: <b>{len(orders)}</b>
• Total Deposited: <b>{sum(tx['amount'] for tx in orders if tx['type'] == 'deposit'):.4f} SOL</b>
• Total Withdrawn: <b>{abs(sum(tx['amount'] for tx in orders if tx['type'] == 'withdrawal')):.4f} SOL</b>

📋 <b>RECENT ACTIVITY</b>
"""
    
    if recent_orders:
        for i, order in enumerate(reversed(recent_orders[-3:]), 1):
            order_type = "📥 Deposit" if order['type'] == 'deposit' else "📤 Withdrawal"
            amount = f"+{order['amount']:.4f}" if order['amount'] > 0 else f"{order['amount']:.4f}"
            time_str = time.strftime('%H:%M', time.localtime(order['timestamp']))
            balance_text += f"• {order_type}: <b>{amount} SOL</b> at {time_str}\n"
    else:
        balance_text += "• No recent activity\n"
    
    balance_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Last updated: {time.strftime('%H:%M:%S UTC')}</i>
"""
    
    # Create buttons
    markup = InlineKeyboardMarkup()
    
    # Main action buttons
    withdraw_btn = InlineKeyboardButton("💸 Withdraw", callback_data="balance_withdraw")
    order_history_btn = InlineKeyboardButton("📋 Order History", callback_data="balance_orders")
    deposit_btn = InlineKeyboardButton("💳 Deposit", callback_data="deposit")
    
    # Navigation buttons
    refresh_btn = InlineKeyboardButton("🔄 Refresh", callback_data="balance")
    back_to_menu_btn = InlineKeyboardButton("🏠 Main Menu", callback_data="mainmenu")
    
    markup.add(withdraw_btn, order_history_btn)
    markup.add(deposit_btn)
    markup.add(refresh_btn, back_to_menu_btn)
    
    try:
        # Try to edit the message first
        bot.edit_message_text(balance_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        # If editing fails (e.g., photo message), send a new message
        bot.send_message(chat_id, balance_text, reply_markup=markup, parse_mode="HTML")

def show_withdrawal_menu(call):
    """Show withdrawal options"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    balance = get_user_balance(user_id)
    
    if balance <= 0:
        no_funds_text = f"""
💸 <b>WITHDRAWAL REQUEST</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ <b>INSUFFICIENT FUNDS</b>
• Current Balance: <b>{balance:.4f} SOL</b>
• Required: <b>0.001 SOL minimum</b>

💡 <b>To withdraw funds:</b>
1. Deposit SOL to your account
2. Ensure balance is above 0.001 SOL
3. Try withdrawal again

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        markup = InlineKeyboardMarkup()
        deposit_btn = InlineKeyboardButton("💳 Deposit Now", callback_data="deposit")
        back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
        
        markup.add(deposit_btn)
    markup.add(back_btn)
    
    try:
        bot.edit_message_text(no_funds_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, no_funds_text, reply_markup=markup, parse_mode="HTML")
        return
    
    withdrawal_text = f"""
💸 <b>WITHDRAWAL REQUEST</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>AVAILABLE BALANCE</b>
• Current Balance: <b>{balance:.4f} SOL</b>
• Minimum Withdrawal: <b>0.001 SOL</b>
• Maximum Withdrawal: <b>{balance:.4f} SOL</b>

📝 <b>WITHDRAWAL OPTIONS</b>
• Enter amount to withdraw
• Or use quick withdrawal buttons
• Withdrawal processed within 24 hours

⚠️ <b>IMPORTANT</b>
• Ensure your wallet address is correct
• Network fees may apply
• Withdrawals are final and cannot be reversed
"""
    
    markup = InlineKeyboardMarkup()
    
    # Quick withdrawal buttons
    quick_25 = InlineKeyboardButton("25%", callback_data="withdraw_25")
    quick_50 = InlineKeyboardButton("50%", callback_data="withdraw_50")
    quick_75 = InlineKeyboardButton("75%", callback_data="withdraw_75")
    quick_all = InlineKeyboardButton("100%", callback_data="withdraw_all")
    
    # Custom amount and navigation
    custom_btn = InlineKeyboardButton("💵 Custom Amount", callback_data="withdraw_custom")
    back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
    refresh_btn = InlineKeyboardButton("🔄 Refresh", callback_data="balance_withdraw")
    
    markup.add(quick_25, quick_50)
    markup.add(quick_75, quick_all)
    markup.add(custom_btn)
    markup.add(back_btn, refresh_btn)
    
    try:
        bot.edit_message_text(withdrawal_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, withdrawal_text, reply_markup=markup, parse_mode="HTML")

def process_withdrawal(call, percentage):
    """Process withdrawal based on percentage"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    balance = get_user_balance(user_id)
    
    if percentage == "custom":
        # For custom amount, we'll need to handle text input
        bot.answer_callback_query(call.id, "💵 Please send the withdrawal amount in SOL (e.g., 0.5)")
        return
    
    # Calculate withdrawal amount
    if percentage == "25":
        amount = balance * 0.25
    elif percentage == "50":
        amount = balance * 0.50
    elif percentage == "75":
        amount = balance * 0.75
    elif percentage == "all":
        amount = balance
    else:
        amount = 0
    
    if amount < 0.001:
        bot.answer_callback_query(call.id, "❌ Amount too small! Minimum is 0.001 SOL")
        return
    
    # Process withdrawal
    new_balance = update_user_balance(user_id, -amount, f"withdraw_{int(time.time())}")
    
    withdrawal_text = f"""
✅ <b>WITHDRAWAL PROCESSED</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>WITHDRAWAL DETAILS</b>
• Amount Withdrawn: <b>{amount:.4f} SOL</b>
• Remaining Balance: <b>{new_balance:.4f} SOL</b>
• Transaction ID: <b>withdraw_{int(time.time())}</b>

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
    
    try:
        bot.edit_message_text(withdrawal_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, withdrawal_text, reply_markup=markup, parse_mode="HTML")

def show_order_history(call):
    """Show detailed order history"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    orders = get_user_orders(user_id)
    
    if not orders:
        no_orders_text = """
📋 <b>ORDER HISTORY</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📭 <b>NO ORDERS FOUND</b>
• You haven't made any transactions yet
• Start by depositing SOL to your account
• Your order history will appear here

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        markup = InlineKeyboardMarkup()
        deposit_btn = InlineKeyboardButton("💳 Deposit Now", callback_data="deposit")
        back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
        
        markup.add(deposit_btn)
        markup.add(back_btn)
        
        try:
            bot.edit_message_text(no_orders_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, no_orders_text, reply_markup=markup, parse_mode="HTML")
        return
    
    # Sort orders by timestamp (newest first)
    sorted_orders = sorted(orders, key=lambda x: x['timestamp'], reverse=True)
    
    history_text = f"""
📋 <b>ORDER HISTORY</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>TRANSACTION SUMMARY</b>
• Total Transactions: <b>{len(orders)}</b>
• Deposits: <b>{len([o for o in orders if o['type'] == 'deposit'])}</b>
• Withdrawals: <b>{len([o for o in orders if o['type'] == 'withdrawal'])}</b>

📝 <b>RECENT TRANSACTIONS</b>
"""
    
    # Show last 10 transactions
    for i, order in enumerate(sorted_orders[:10], 1):
        order_type = "📥" if order['type'] == 'deposit' else "📤"
        amount = f"+{order['amount']:.4f}" if order['amount'] > 0 else f"{order['amount']:.4f}"
        time_str = time.strftime('%m/%d %H:%M', time.localtime(order['timestamp']))
        tx_hash = order['tx_hash'][:8] + "..." if len(order['tx_hash']) > 8 else order['tx_hash']
        
        history_text += f"{i:2d}. {order_type} <b>{amount} SOL</b> | {time_str}\n"
        history_text += f"    TX: <code>{tx_hash}</code>\n\n"
    
    if len(orders) > 10:
        history_text += f"... and {len(orders) - 10} more transactions\n"
    
    history_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Showing last 10 transactions</i>
"""
    
    markup = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
    refresh_btn = InlineKeyboardButton("🔄 Refresh", callback_data="balance_orders")
    
    markup.add(back_btn, refresh_btn)
    
    try:
        bot.edit_message_text(history_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, history_text, reply_markup=markup, parse_mode="HTML")

def handle_balance_callback(call):
    """Handle all balance-related callbacks"""
    if call.data == "balance":
        show_balance_menu(call)
    elif call.data == "balance_withdraw":
        show_withdrawal_menu(call)
    elif call.data == "balance_orders":
        show_order_history(call)
    elif call.data.startswith("withdraw_"):
        percentage = call.data.split("_")[1]
        process_withdrawal(call, percentage)
    elif call.data == "withdraw_custom":
        # Add user to waiting list for custom withdrawal
        from main import custom_withdrawal_waiting
        custom_withdrawal_waiting.add(call.message.chat.id)
        
        custom_text = """
💵 <b>CUSTOM WITHDRAWAL</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>Enter Amount</b>
• Send the amount you want to withdraw
• Minimum: 0.001 SOL
• Maximum: 1000 SOL
• Example: 0.5

⚠️ <b>Important</b>
• Type /cancel to cancel
• Amount must be in SOL
• Check your balance first
"""
        
        markup = InlineKeyboardMarkup()
        cancel_btn = InlineKeyboardButton("❌ Cancel", callback_data="balance_withdraw")
        back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
        
        markup.add(cancel_btn, back_btn)
        
        try:
            bot.edit_message_text(custom_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, custom_text, reply_markup=markup, parse_mode="HTML")

def admin_update_balance(user_id, amount, tx_hash):
    """Admin function to update user balance"""
    new_balance = update_user_balance(user_id, amount, tx_hash)
    return new_balance

def get_balance_for_admin(user_id):
    """Get user balance for admin display"""
    balance = get_user_balance(user_id)
    orders = get_user_orders(user_id)
    return {
        'balance': balance,
        'total_orders': len(orders),
        'last_activity': orders[-1]['timestamp'] if orders else None
    }
