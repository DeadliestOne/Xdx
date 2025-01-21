from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient
from datetime import datetime

# MongoDB Configuration
MONGO_URI = "mongodb+srv://jc07cv9k3k:bEWsTrbPgMpSQe2z@cluster0.nfbxb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/"  # Replace with your MongoDB URI
client = MongoClient(MONGO_URI)
db = client['online_status_bot']
user_collection = db['user_status']

# Command to start the bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome! Use /notice {username} to track a user and /fetch to get stats.")

# Command to notice a user's activity
def notice(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("Usage: /notice {username}")
        return

    username = context.args[0]
    if user_collection.find_one({"username": username}):
        update.message.reply_text(f"Already tracking {username}.")
    else:
        user_collection.insert_one({"username": username, "status": "offline", "last_online": None, "online_duration": 0})
        update.message.reply_text(f"Started tracking {username}.")

# Command to fetch online duration
def fetch(update: Update, context: CallbackContext) -> None:
    tracked_users = list(user_collection.find())
    if not tracked_users:
        update.message.reply_text("No users being tracked.")
        return

    report = []
    for user in tracked_users:
        username = user['username']
        duration = user['online_duration']
        report.append(f"{username}: {duration} seconds online")

    update.message.reply_text("\n".join(report))

# Simulated online status tracking (placeholder function)
def update_online_status(username: str, status: str) -> None:
    user = user_collection.find_one({"username": username})
    if user:
        if status == "online" and user["status"] != "online":
            user_collection.update_one({"username": username}, {"$set": {"status": "online", "last_online": datetime.utcnow()}})
        elif status == "offline" and user["status"] == "online":
            last_online = user["last_online"]
            if last_online:
                online_duration = (datetime.utcnow() - last_online).total_seconds()
                user_collection.update_one({"username": username}, {
                    "$set": {"status": "offline"},
                    "$inc": {"online_duration": online_duration},
                })

# Main function to set up the bot
def main() -> None:
    TOKEN = "7941421820:AAHF7nB24H9ucSi-cwUfCqCS1DSH0LorDfs"  # Replace with your bot's token
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("notice", notice))
    dispatcher.add_handler(CommandHandler("fetch", fetch))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
