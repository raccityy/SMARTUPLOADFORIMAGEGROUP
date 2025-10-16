"""
Enhanced Group Messaging System for Telegram Bot

This module handles all group-to-user messaging functionality with comprehensive media support.
Features:
- Support for all media types (photos, videos, GIFs, documents, audio, etc.)
- Continuous reply mode for multiple messages
- Admin commands for managing reply sessions
- Automatic media type detection and forwarding
- Confirmation messages for successful forwards

Admin Commands:
- /exit_reply - Exit continuous reply mode
- /reply_status - Check current reply status
"""

import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot
from text_utils import code_wrap, html_escape
import logging

# Load group chat ID from environment for security
_group_id_env = os.environ.get("TELEGRAM_GROUP_CHAT_ID", "").strip()
if not _group_id_env:
    raise RuntimeError("Missing TELEGRAM_GROUP_CHAT_ID environment variable. Set your Telegram group/chat ID.")
try:
    group_chat_id = int(_group_id_env)
except ValueError as e:
    raise RuntimeError("Invalid TELEGRAM_GROUP_CHAT_ID; it must be an integer.") from e

# Store mapping from group message_id to user chat_id
reply_targets = {}

# Store mapping from admin chat_id to user chat_id for reply flow
admin_reply_state = {}

# Store admin reply modes (for continuous reply mode)
admin_reply_modes = {}

def send_payment_verification_to_group(user, price, ca, tx_hash, user_chat_id=None):
    text = (
        f"🧾 <b>Payment Verification Request</b>\n\n"
        f"User: @{html_escape(str(user))}\n"
        f"Price: {code_wrap(str(price))}\n"
        f"CA: {code_wrap(str(ca))}\n"
        f"TX: {code_wrap(str(tx_hash))}\n\n"
        f"Please verify this transaction."
    )
    markup = InlineKeyboardMarkup()
    reply_btn = InlineKeyboardButton("reply", callback_data=f"group_reply_{user_chat_id}")
    close_btn = InlineKeyboardButton("close", callback_data=f"group_close_{user_chat_id}")
    markup.add(reply_btn, close_btn)
    sent = bot.send_message(group_chat_id, text, reply_markup=markup)
    if user_chat_id:
        reply_targets[sent.message_id] = user_chat_id


def handle_group_callback(call):
    if call.data.startswith("group_reply_"):
        # Extract user_chat_id from callback data
        user_chat_id = call.data.split("group_reply_")[1]
        admin_reply_state[call.from_user.id] = user_chat_id
        admin_reply_modes[call.from_user.id] = user_chat_id  # Enable continuous reply mode
        
        # Enhanced reply prompt with media support info
        reply_text = (
            "📝 <b>Reply Mode Activated</b>\n\n"
            "You can now send any of the following to the user:\n"
            "• 📝 Text\n"
            "• 🖼️ Photos\n"
            "• 🎥 Videos\n"
            "• 🎬 GIFs/Animations\n"
            "• 📄 Documents\n"
            "• 🎵 Audio\n"
            "• 🎤 Voice Messages\n"
            "• 📍 Locations\n"
            "• 👤 Contacts\n"
            "• 🎲 Stickers\n\n"
            "💡 <b>Commands</b>\n"
            "• /exit_reply — Stop replying\n"
            "• /reply_status — Check current status\n\n"
            "Send your message now."
        )
        bot.send_message(call.message.chat.id, reply_text)
        
    elif call.data.startswith("group_close_"):
        bot.delete_message(call.message.chat.id, call.message.message_id)

# Handler to process admin replies in the group (called from main.py)
def handle_admin_reply(message):
    admin_id = message.from_user.id
    print(f"DEBUG: Group message received from admin {admin_id}, content type: {message.content_type}")
    
    # Handle admin commands
    if message.text:
        command = message.text.strip()
        
        if command == "/exit_reply":
            if admin_id in admin_reply_modes:
                user_chat_id = admin_reply_modes.pop(admin_id)
                admin_reply_state.pop(admin_id, None)  # Also remove from single reply state
                bot.send_message(message.chat.id, f"✅ Exited reply mode for user {user_chat_id}")
            else:
                bot.send_message(message.chat.id, "❌ You're not currently in reply mode")
            return
        
        elif command == "/reply_status":
            if admin_id in admin_reply_modes:
                user_chat_id = admin_reply_modes[admin_id]
                bot.send_message(message.chat.id, f"📝 Currently in continuous reply mode for user {user_chat_id}")
            elif admin_id in admin_reply_state:
                user_chat_id = admin_reply_state[admin_id]
                bot.send_message(message.chat.id, f"📝 Currently in single reply mode for user {user_chat_id}")
            else:
                bot.send_message(message.chat.id, "❌ Not currently in reply mode")
            return
    
    # Handle single reply mode (one-time reply)
    if admin_id in admin_reply_state and admin_id not in admin_reply_modes:
        user_chat_id = admin_reply_state.pop(admin_id)
        
        # Forward the message to user with enhanced media support
        handle_media_forwarding_with_confirmation(message, user_chat_id)
        
        # Note: Confirmation is now handled by handle_media_forwarding_with_confirmation
        # so we don't need the simple "Reply sent to user" message here
    
    # Handle continuous reply mode
    elif admin_id in admin_reply_modes:
        user_chat_id = admin_reply_modes[admin_id]
        
        # Forward the message to user with enhanced media support
        handle_media_forwarding_with_confirmation(message, user_chat_id)

def forward_message_to_user(message, user_chat_id):
    """Forward admin message to user, supporting all media types"""
    try:
        print(f"DEBUG: Forwarding message to user {user_chat_id}, content type: {message.content_type}")
        print(f"DEBUG: Message has photo: {bool(message.photo)}, video: {bool(message.video)}, text: {bool(message.text)}")
        
        # Handle photos (prioritize media over text)
        if message.photo:
            print("DEBUG: Processing photo message")
            # Get the highest quality photo
            photo = message.photo[-1]
            bot.send_photo(user_chat_id, photo.file_id, caption=message.caption)
        
        # Handle videos
        elif message.video:
            print("DEBUG: Processing video message")
            bot.send_video(user_chat_id, message.video.file_id, caption=message.caption)
        
        # Handle animations (GIFs)
        elif message.animation:
            print("DEBUG: Processing animation message")
            bot.send_animation(user_chat_id, message.animation.file_id, caption=message.caption)
        
        # Handle documents
        elif message.document:
            print("DEBUG: Processing document message")
            bot.send_document(user_chat_id, message.document.file_id, caption=message.caption)
        
        # Handle audio
        elif message.audio:
            print("DEBUG: Processing audio message")
            bot.send_audio(user_chat_id, message.audio.file_id, caption=message.caption)
        
        # Handle voice messages
        elif message.voice:
            print("DEBUG: Processing voice message")
            bot.send_voice(user_chat_id, message.voice.file_id, caption=message.caption)
        
        # Handle video notes (round videos)
        elif message.video_note:
            print("DEBUG: Processing video note message")
            bot.send_video_note(user_chat_id, message.video_note.file_id)
        
        # Handle stickers
        elif message.sticker:
            print("DEBUG: Processing sticker message")
            bot.send_sticker(user_chat_id, message.sticker.file_id)
        
        # Handle location
        elif message.location:
            print("DEBUG: Processing location message")
            bot.send_location(user_chat_id, message.location.latitude, message.location.longitude)
        
        # Handle contact
        elif message.contact:
            print("DEBUG: Processing contact message")
            bot.send_contact(user_chat_id, message.contact.phone_number, message.contact.first_name)
        
        # Handle poll (if supported by telebot version)
        elif hasattr(message, 'poll') and message.poll:
            print("DEBUG: Processing poll message")
            bot.send_poll(user_chat_id, message.poll.question, message.poll.options, is_anonymous=message.poll.is_anonymous)
        
        # Handle dice (if supported by telebot version)
        elif hasattr(message, 'dice') and message.dice:
            print("DEBUG: Processing dice message")
            bot.send_dice(user_chat_id, emoji=message.dice.emoji)
        
        # Handle venue (if supported by telebot version)
        elif hasattr(message, 'venue') and message.venue:
            print("DEBUG: Processing venue message")
            bot.send_venue(user_chat_id, message.venue.location.latitude, message.venue.location.longitude, 
                          message.venue.title, message.venue.address)
        
        # Handle text messages (only if no media is present)
        elif message.text:
            print("DEBUG: Processing text message")
            bot.send_message(user_chat_id, message.text)
        
        else:
            print("DEBUG: Unsupported message type")
            # Fallback for unsupported content types
            bot.send_message(user_chat_id, "Received unsupported message type from admin.")
            
    except Exception as e:
        # Send error message to user if forwarding fails
        bot.send_message(user_chat_id, f"Error forwarding message: {str(e)}")
        print(f"Error forwarding message to user {user_chat_id}: {e}")

def get_media_type_info(message):
    """Get information about the media type of a message"""
    if message.photo:
        return "📷 Photo"
    elif message.video:
        return "🎥 Video"
    elif message.animation:
        return "🎬 Animation/GIF"
    elif message.document:
        return "📄 Document"
    elif message.audio:
        return "🎵 Audio"
    elif message.voice:
        return "🎤 Voice Message"
    elif message.video_note:
        return "📹 Video Note"
    elif message.sticker:
        return "🎲 Sticker"
    elif message.location:
        return "📍 Location"
    elif message.contact:
        return "👤 Contact"
    elif hasattr(message, 'poll') and message.poll:
        return "📊 Poll"
    elif hasattr(message, 'dice') and message.dice:
        return "🎲 Dice"
    elif hasattr(message, 'venue') and message.venue:
        return "🏢 Venue"
    elif message.text:
        return "📝 Text"
    else:
        return "❓ Unknown"

def send_media_confirmation_to_group(admin_id, user_chat_id, media_type):
    """Send confirmation to group when media is forwarded"""
    try:
        confirmation_text = f"✅ {media_type} forwarded to user (ID: {user_chat_id})"
        bot.send_message(group_chat_id, confirmation_text)
    except Exception as e:
        print(f"Error sending confirmation to group: {e}")

def handle_media_forwarding_with_confirmation(message, user_chat_id):
    """Enhanced media forwarding with confirmation"""
    media_type = get_media_type_info(message)
    
    # Forward the message
    forward_message_to_user(message, user_chat_id)
    
    # Send confirmation to group
    send_media_confirmation_to_group(message.from_user.id, user_chat_id, media_type)
