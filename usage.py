from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB Configuration
MONGO_URI = "mongodb+srv://jc07cv9k3k:bEWsTrbPgMpSQe2z@cluster0.nfbxb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/"  # Replace with your MongoDB URI
client = MongoClient(MONGO_URI)
db = client['online_status_bot']
user_collection = db['user_status']

# Log when a user sends a message (simulating online activity)
async def log_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username or "Unknown User"
    user = user_collection.find_one({"username": username})

    if user:
        # If user is currently offline, mark them online
        if user["status"] == "offline":
            user_collection.update_one(
                {"username": username},
                {"$set": {"status": "online", "last_online": datetime.utcnow()}}
            )
    else:
        # Add user to the database
        user_collection.insert_one({
            "username": username,
            "status": "online",
            "last_online": datetime.utcnow(),
            "online_duration": 0
        })

# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! The bot is tracking your activity. Use /fetch to see your online duration.")

# Command to fetch user's total online time
async def fetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username or "Unknown User"
    user = user_collection.find_one({"username": username})

    if not user:
        await update.message.reply_text("You are not being tracked yet.")
        return

    # Calculate total duration
    total_duration = user["online_duration"]
    if user["status"] == "online":
        # Add current online session if still online
        last_online = user["last_online"]
        total_duration += (datetime.utcnow() - last_online).total_seconds()

    total_time = str(timedelta(seconds=int(total_duration)))
    await update.message.reply_text(f"@{username}, you've been online for a total of {total_time}.")

# Command to stop tracking
async def stop_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username or "Unknown User"
    user_collection.delete_one({"username": username})
    await update.message.reply_text(f"Stopped tracking @{username}.")

# Simulate offline status for users who are inactive for a threshold
async def check_inactive_users(context: ContextTypes.DEFAULT_TYPE) -> None:
    threshold = timedelta(minutes=5)  # Inactivity threshold
    now = datetime.utcnow()
    users = user_collection.find({"status": "online"})

    for user in users:
        last_online = user["last_online"]
        if (now - last_online) > threshold:
            # Mark user as offline and calculate session duration
            session_duration = (now - last_online).total_seconds()
            user_collection.update_one(
                {"username": user["username"]},
                {
                    "$set": {"status": "offline"},
                    "$inc": {"online_duration": session_duration}
                }
            )

# Main function to set up the bot
def main() -> None:
    TOKEN = "7941421820:AAHF7nB24H9ucSi-cwUfCqCS1DSH0LorDfs"  # Replace with your bot's token
    application = Application.builder().token(TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fetch", fetch))
    application.add_handler(CommandHandler("stop", stop_tracking))

    # Message handler to log activity
    application.add_handler(MessageHandler(filters.ALL, log_activity))

    # Job to check inactive users
    application.job_queue.run_repeating(check_inactive_users, interval=60)

    application.run_polling()

if __name__ == "__main__":
    main()
