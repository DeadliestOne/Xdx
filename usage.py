from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline
from pymongo import MongoClient
from datetime import datetime
import requests

# Replace with your API credentials from my.telegram.org
API_ID = '26416419'
API_HASH = 'c109c77f5823c847b1aeb7fbd4990cc4'
PHONE_NUMBER = '+8801634532670'  # Your Telegram account phone number

# Replace with your Telegram Bot Token and Chat ID
BOT_TOKEN = "7941421820:AAHF7nB24H9ucSi-cwUfCqCS1DSH0LorDfs"
CHAT_ID = "6748827895"  # Your Telegram user ID to receive notifications

# MongoDB configuration
MONGO_URI = "mongodb+srv://jc07cv9k3k:bEWsTrbPgMpSQe2z@cluster0.nfbxb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/"
client = MongoClient(MONGO_URI)
db = client['online_status_bot']
tracked_users = db['tracked_users']  # Collection to store tracking information

# Initialize Telethon client
telegram_client = TelegramClient('user_session', API_ID, API_HASH)

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
    user = await telegram_client.get_entity(username)
    if not tracked_users.find_one({"id": user.id}):
        tracked_users.insert_one({
            "id": user.id,
            "username": username,
            "online_logs": [],
        })
        return f"Started tracking @{username}."
    else:
        return f"User @{username} is already being tracked."

@telegram_client.on(events.UserUpdate)
async def handle_user_update(event):
    """Handle online/offline updates for tracked users."""
    if event.user_id:
        user = await telegram_client.get_entity(event.user_id)
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

async def main():
    """Main logic."""
    await telegram_client.start(PHONE_NUMBER)
    print("Telegram Client has started.")
    
    # Example: Add a user to track
    username_to_track = input("Enter the username to track (e.g., @example_user): ")
    print(await add_user_to_track(username_to_track))
    
    # Example: Fetch user status
    username_to_fetch = input("Enter the username to fetch status for (e.g., @example_user): ")
    status_report = await fetch_user_status(username_to_fetch)
    print(status_report)
    await send_bot_message(status_report)
    
    # Keep the client running to monitor status
    await telegram_client.run_until_disconnected()

if __name__ == "__main__":
    telegram_client.loop.run_until_complete(main())
