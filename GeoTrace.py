import logging,json,os
import ipapi
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup,Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest,TelegramError
from telegram.constants import ParseMode
from config import *
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your ipapi key
API_KEY = API_KEY
url = f"https://api.ipapi.com/check?access_key={API_KEY}"
CHANNEL_LINK = F"https://t.me/python_tools9"
IMAGE_URL = "https://drive.google.com/uc?export=view&id=1KBGv6683FnQC96oSfKCYOv3lt3WFopwI" 
ADMIN_ID=ADMIN_ID
NOTIFY_CHANNEL = NOTIFY_CHANNEL 


USER_IDS_FILE = "user_ids.json"

def load_user_ids():
    try:
        with open(USER_IDS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_user_id(user_id):
    try:
        try:
            with open(USER_IDS_FILE, "r") as f:
                user_ids = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            user_ids = []
        
        if user_id not in user_ids:
            user_ids.append(user_id)
            with open(USER_IDS_FILE, "w") as f:
                json.dump(user_ids, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving user ID: {e}")

async def send_channel_notification(bot: Bot, user_id: int, username: str) -> None:
    message = (
        f"<b>📢 New user started the Geo-Trace bot!</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"👤 <b>Username:</b> @{username}\n\n"
    )
    try:
        print(f"New user join: {user_id}")
        await bot.send_message(NOTIFY_CHANNEL, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error sending notification to channel: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome image and message when /start is used"""
    user = update.effective_user
    username = user.username or "Unknown"
    user_id = user.id

    save_user_id(user_id)

    bot = context.bot
    await send_channel_notification(bot, user_id, username)

    welcome_message = (f"<b>Welcome to GetGeoLocation Bot!</b>\n\n"
                       f"Use <b>/ip -ip_address- </b> to get the location of any IP 🌍.\n\n"
                       f"Use <b>/help - </b> to know about BOT.\n"
                       f"Here are your details:\n\n"
                       f"👤 <b>Username:</b> <b>@{username}</b>\n"
                       f"🔑 <b>User ID:</b> <code>{user_id}</code>\n\n"
                       f"✨ Let's start exploring IP addresses! 🌐")

    keyboard = [
        [InlineKeyboardButton("Join our Channel 📢", url=CHANNEL_LINK)],
        [InlineKeyboardButton("Developer🔑", "https://t.me/gundaaaaaa")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(photo=IMAGE_URL, caption=welcome_message, parse_mode="html", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides information about available commands"""
    help_message = (
        "*📢Welcome to the GeoTrace BOT Help Guide!*\n\n"
        "*Here are the available commands:*\n\n"
        "1. /start - Start the bot and get a welcome message along with your user info. 🌟\n"
        "2. /ip [IP_ADDRESS] - Get the location and information for any IP address. 🌍\n"
        "3. /info - Get detailed information about your user profile. 📸\n\n"
        "*If you have any questions, feel free to reach out! 😊*\n\n"
        
    )
    
    keyboard = [
        [InlineKeyboardButton("Join our Channel 📢", url=CHANNEL_LINK)],
        [InlineKeyboardButton("Developer🔑", url="https://t.me/gundaaaaaa")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_message, 
        parse_mode=ParseMode.MARKDOWN, 
        reply_markup=reply_markup
    )

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Allows the admin to send a broadcast message to all users with better error handling.
    """
    if update.effective_user.id not in ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    args = context.args

    if len(args) < 1:
        await update.message.reply_text("Usage: /broad <message>\nPlease provide a message to broadcast.")
        return

    message = ' '.join(args)

    if os.path.exists(USER_IDS_FILE):
        with open(USER_IDS_FILE, 'r') as file:
            user_ids = json.load(file)
    else:
        user_ids = []

    successful = 0
    failed = 0
    skipped = 0
    failed_user_ids = []  

    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            successful += 1 
        except BadRequest as e:
            if 'blocked' in str(e).lower():
                skipped += 1
                failed_user_ids.append(user_id)  
            else:
                failed += 1 
            print(f"Error sending message to user {user_id}: {e}")
        except TelegramError as e:
            failed += 1
            print(f"Error sending message to user {user_id}: {e}")
        except Exception as e:
            failed += 1
            print(f"Unexpected error with user {user_id}: {e}")

    summary_message = (
        f"📢 **Broadcast completed!**\n\n"
        f"👥 **Total users:** {len(user_ids)}\n"
        f"✅ **Message sent successfully to:** {successful} users\n"
        f"❌ **Failed to send to:** {failed} users\n"
        f"⛔ **Skipped (blocked users):** {skipped} users\n\n"
        f"⚠️ **Failed user IDs (Blocked/Invalid):** {', '.join(map(str, failed_user_ids)) if failed_user_ids else 'None'}"
    )


    await update.message.reply_text(summary_message,parse_mode="MARKDOWN")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays user info with their profile picture (if available)"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "Unknown"
    first_name = user.first_name or "No name"
    last_name = user.last_name or "No last name"
    
    info_message = (
        f"*User Info:*\n\n"
        f"👤 *First Name:* {first_name}\n"
        f"👥 *Last Name:* {last_name}\n"
        f"🆔 *User ID:* `{user_id}`\n"
        f"📝 *Username:* @{username}\n"
    )
    
    profile_photos = await user.get_profile_photos()
    
    if profile_photos.total_count > 0:
        profile_picture = profile_photos.photos[0][-1].file_id  
        await update.message.reply_photo(
            photo=profile_picture, 
            caption=info_message, 
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        keyboard = [
            [InlineKeyboardButton("Join our Channel 📢", url="https://t.me/gundaaaaaa")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            info_message, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=reply_markup
        )


async def ip_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays IP info when /ip <ip_address> command is used"""
    if len(context.args) != 1:
        await update.message.reply_text('Usage: /ip <b>ip_address</b>', parse_mode="html")
        return

    ip_address = context.args[0]

    try:
        location = ipapi.location(ip_address)

        info_message = "<b>IP Address Information:</b>\n\n"

        for key, value in location.items():
            info_message += f"<b>⛔{key}:</b> <code>{value}</code>\n"

        await update.message.reply_text(info_message, parse_mode="html")

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}", parse_mode="html")



def main() -> None:
    """Start the bot and set up the handlers"""
    TELEGRAM_TOKEN = "7725555068:AAFPbtq432nGsN-sBakCNTw2nnrLdp-PyiY"

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ip", ip_info))
    application.add_handler(CommandHandler("broad", handle_broadcast))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()


if __name__ == '__main__':
    main()
