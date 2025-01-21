from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline, User
from pymongo import MongoClient
from datetime import datetime
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Replace with your API credentials from my.telegram.org
API_ID = '26416419'
API_HASH = 'c109c77f5823c847b1aeb7fbd4990cc4'
PHONE_NUMBER = '+8801634532670'# Your Telegram account phone number

# Replace with your Telegram Bot Token and Chat ID
BOT_TOKEN = "7941421820:AAHF7nB24H9ucSi-cwUfCqCS1DSH0LorDfs"
CHAT_ID = "6748827895"  # Your Telegram user ID to receive notifications

# MongoDB configuration
MONGO_URI = "mongodb+srv://jc07cv9k3k:bEWsTrbPgMpSQe2z@cluster0.nfbxb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/"
client = MongoClient(MONGO_URI)
db = client['online_status_bot']
tracked_users = db['tracked_users']  #  Collection to store tracking information

# Initialize Telethon client
telegram_client = TelegramClient('user_session', API_ID, API_HASH)

# Initialize Telegram bot using python-telegram-bot v20
application = Application.builder().token(BOT_TOKEN).build()

async def send_bot_message(message):
    """Send a message via Telegram Bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"Message sent: {message}")
        else:
            print(f"Failed to send message. Response: {response.text}")
    except Exception as e:
        print(f"Error while sending message: {e}")

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
        try:
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
        except Exception as e:
            print(f"Error while processing user update: {e}")

async def fetch_user_status(username):
    """Fetch the online status logs of a user."""
    try:
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
    except Exception as e:
        return f"Error fetching logs for @{username}: {e}"

# Command to notice a user and start tracking
async def notice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a user to track."""
    try:
        if context.args:
            username = context.args[0]
            response = await add_user_to_track(username)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Please provide a username to track.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Command to fetch user logs
async def fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch user activity logs."""
    try:
        if context.args:
            username = context.args[0]
            response = await fetch_user_status(username)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Please provide a username to fetch logs.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Add command handlers to the bot
application.add_handler(CommandHandler("notice", notice))
application.add_handler(CommandHandler("fetch", fetch))

async def monitor_and_start_tracking():
    """Start tracking users' current status when the bot starts."""
    tracked_usernames = ["@your_ishani", "@your_ishani"]  # Add usernames to track

    for username in tracked_usernames:
        response = await add_user_to_track(username)
        print(response)

    # Fetch initial status for all tracked users
    for username in tracked_usernames:
        try:
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
        except Exception as e:
            print(f"Error while tracking {username}: {e}")

async def main():
    """Main logic."""
    try:
        # Start the Telethon client
        await telegram_client.start(PHONE_NUMBER)
        print("Telegram Client has started.")
        
        # Start monitoring and tracking user statuses
        await monitor_and_start_tracking()

        # Start the bot to handle Telegram commands
        await application.initialize()
        await application.start_polling()

        # Keep the client running to monitor status
        await telegram_client.run_until_disconnected()
    except Exception as e:
        print(f"Error during bot execution: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
