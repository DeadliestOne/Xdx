from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline, User
from pymongo import MongoClient
from datetime import datetime
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Replace with your API credentials from my.telegram.org
API_ID = '26416419'
API_HASH = 'c109c77f5823c847b1aeb7fbd4990cc4'
PHONE_NUMBER = '+8801634532670'# Your Telegram account phone number

# Replace with your Telegram Bot Token and Chat ID
BOT_TOKEN = "7941421820:AAHF7nB24H9ucSi-cwUfCqCS1DSH0LorDfs"
CHAT_ID = "-1002405049591"  # Your Telegram user ID to receive notifications

# MongoDB configuration
MONGO_URI = "mongodb+srv://jc07cv9k3k:bEWsTrbPgMpSQe2z@cluster0.nfbxb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/"
client = MongoClient(MONGO_URI)
db = client['online_status_bot']
tracked_users = db['tracked_users']  #  toCollection to store tracking information

# Initialize Telethon client
telegram_client = TelegramClient('user_session', API_ID, API_HASH)

# Initialize Telegram bot using python-telegram-bot
updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

async def send_bot_message(message):
    """Send a message via Telegram Bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"Message sent: {message}")
    else:
        print(f"Failed to send message. Response: {response.text}")

async def add_user_to_track(username):
    """Add a user to track."""
    try:
        user = await telegram_client.get_entity(username)
        
        # Ensure it's a user, not a channel or group
        if isinstance(user, User):  # Check if the entity is a user
            # Check if the user is already in the tracking list
            if not tracked_users.find_one({"id": user.id}):
                tracked_users.insert_one({
                    "id": user.id,
                    "username": username,
                    "online_logs": [],
                })
                return f"Started tracking @{username}."
            else:
                return f"User @{username} is already being tracked."
        else:
            return f"@{username} is not a valid user. Please provide a valid username."
    
    except Exception as e:
        return f"Error adding user: {e}"

@telegram_client.on(events.UserUpdate)
async def handle_user_update(event):
    """Handle online/offline updates for tracked users."""
    if event.user_id:
        user = await telegram_client.get_entity(event.user_id)

        # Only proceed if the entity is a user
        if isinstance(user, User):
            tracked_user = tracked_users.find_one({"id": user.id})
            
            if tracked_user:
                now = datetime.utcnow()
                if isinstance(user.status, UserStatusOnline):
                    log = f"{user.username} is online at {now.strftime('%Y-%m-%d %H:%M:%S')}."
                    print(log)
                    tracked_users.update_one(
                        {"id": user.id},
                        {"$push": {"online_logs": {"status": "online", "time": now}}}
                    )
                    await send_bot_message(log)
                elif isinstance(user.status, UserStatusOffline):
                    log = f"{user.username} is offline at {now.strftime('%Y-%m-%d %H:%M:%S')}."
                    print(log)
                    tracked_users.update_one(
                        {"id": user.id},
                        {"$push": {"online_logs": {"status": "offline", "time": now}}}
                    )
                    await send_bot_message(log)

async def fetch_user_status(username):
    """Fetch the online status logs of a user."""
    user = tracked_users.find_one({"username": username})
    if not user:
        return f"No tracking data found for @{username}."
    
    logs = user.get("online_logs", [])
    if not logs:
        return f"No activity logs found for @{username}."
    
    report = [f"Activity logs for @{username}:"]
    for log in logs:
        status = log["status"]
        time = log["time"].strftime("%Y-%m-%d %H:%M:%S")
        report.append(f"{status.title()} at {time}")
    return "\n".join(report)

# Command to notice a user and start tracking
def notice(update: Update, context: CallbackContext):
    """Add a user to track."""
    if context.args:
        username = context.args[0]
        response = telegram_client.loop.run_until_complete(add_user_to_track(username))
        update.message.reply_text(response)
    else:
        update.message.reply_text("Please provide a username to track.")

# Command to fetch user logs
def fetch(update: Update, context: CallbackContext):
    """Fetch user activity logs."""
    if context.args:
        username = context.args[0]
        response = telegram_client.loop.run_until_complete(fetch_user_status(username))
        update.message.reply_text(response)
    else:
        update.message.reply_text("Please provide a username to fetch logs.")

# Add command handlers to the bot
dispatcher.add_handler(CommandHandler("notice", notice))
dispatcher.add_handler(CommandHandler("fetch", fetch))

async def monitor_and_start_tracking():
    """Start tracking users' current status when the bot starts."""
    # Check all the users you want to track and ensure they're in the database
    tracked_usernames = ["@example_user1", "@example_user2"]  # Add usernames to track

    for username in tracked_usernames:
        await add_user_to_track(username)

    # Fetch initial status for all tracked users
    for username in tracked_usernames:
        user = await telegram_client.get_entity(username)
        tracked_user = tracked_users.find_one({"id": user.id})
        if tracked_user:
            status = user.status
            now = datetime.utcnow()
            if isinstance(status, UserStatusOnline):
                log = f"{user.username} was online at {now.strftime('%Y-%m-%d %H:%M:%S')}."
                tracked_users.update_one(
                    {"id": user.id},
                    {"$push": {"online_logs": {"status": "online", "time": now}}}
                )
            elif isinstance(status, UserStatusOffline):
                log = f"{user.username} was offline at {now.strftime('%Y-%m-%d %H:%M:%S')}."
                tracked_users.update_one(
                    {"id": user.id},
                    {"$push": {"online_logs": {"status": "offline", "time": now}}}
                )
            await send_bot_message(log)

async def main():
    """Main logic."""
    # Start the Telethon client
    await telegram_client.start(PHONE_NUMBER)
    print("Telegram Client has started.")
    
    # Start monitoring and tracking user statuses
    await monitor_and_start_tracking()

    # Start the bot to handle Telegram commands
    updater.start_polling()

    # Keep the client running to monitor status
    await telegram_client.run_until_disconnected()

if __name__ == "__main__":
    telegram_client.loop.run_until_complete(main())
