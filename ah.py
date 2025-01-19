import os
import json
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from pymongo import MongoClient
from colorama import init, Fore
import pyfiglet
import asyncio

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "8015878481:AAGgbl0Ssx37pATFSISWqUu731qBpdBio68"

# MongoDB Configuration
MONGO_URI = "mongodb+srv://uchitraprobot2:Orion@cluster0.3es1c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "telegram_bot"
COLLECTION_NAME = "hosted_accounts"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
accounts_collection = db[COLLECTION_NAME]

# Define the bot owner and allowed users
OWNER_ID = 6748827895  # Replace with the owner user ID
ALLOWED_USERS = set([OWNER_ID])  # Initially allow only the owner

# User states to track ongoing processes
user_states = {}

# Initialize Telegram bot
bot_client = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# Helper functions for MongoDB
def save_account_to_db(api_id, api_hash, phone_number):
    """Save an account to the MongoDB database."""
    accounts_collection.update_one(
        {"phone_number": phone_number},
        {"$set": {"api_id": api_id, "api_hash": api_hash, "phone_number": phone_number}},
        upsert=True
    )

def get_all_accounts():
    """Retrieve all hosted accounts from the database."""
    return list(accounts_collection.find())

def remove_account_from_db(phone_number):
    """Remove an account from the database."""
    accounts_collection.delete_one({"phone_number": phone_number})

# Function to display banner
def display_banner():
    print(Fore.RED + pyfiglet.figlet_format("LEGITDEALS9"))
    print(Fore.GREEN + "Made by @Legitdeals9\n")

# Handle OTP during login
@bot_client.on(events.NewMessage)
async def handle_otp(event):
    user_id = event.sender_id
    text = event.text.strip()

    if user_id != OWNER_ID:
        return

    if text.count('|') == 2:
        api_id, api_hash, phone_number = text.split('|')
        session_name = f"session_{phone_number}"
        user_client = TelegramClient(session_name, api_id, api_hash)

        try:
            await user_client.start(phone=phone_number)
            if not await user_client.is_user_authorized():
                await user_client.send_code_request(phone_number)
                await event.reply("📲 OTP sent to your phone. Please provide the OTP.")
                return
            else:
                await event.reply(f"✅ Account {phone_number} is already authorized!")
                save_account_to_db(api_id, api_hash, phone_number)

        except FloodWaitError as e:
            await event.reply(f"⚠️ You are sending requests too quickly. Please wait for {e.seconds} seconds.")
        except Exception as e:
            await event.reply(f"❌ Error: {e}")

# Handle /start command
@bot_client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Welcome message for users."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("🚫 You are not authorized to use this bot.")
        return

    await event.reply(
        "🤖 Welcome to the Hosting Bot! Use the commands below:\n\n"
        "📡 /host - Host a new Telegram account\n"
        "🔄 /accounts - List hosted accounts\n"
        "❌ /remove - Remove a hosted account\n"
        "📊 /stats - View server stats\n"
        "👤 /add {user_id} - Add a user to the allowed list (owner only)\n\n"
        "Made by - [dev](t.me/Uncountableaura)"
    )

# Helper function for displaying stats
@bot_client.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    """Displays server stats and hosted accounts information."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("🚫 You are not authorized to use this bot.")
        return

    # Fetch system stats
    ram_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)
    total_accounts = accounts_collection.count_documents({})
    hosting_capacity = max(0, 50 - total_accounts)  # Assuming a limit of 50 accounts

    message = (
        f"📊 **Server Stats**:\n"
        f"💾 RAM Usage: {ram_usage}%\n"
        f"⚙️ CPU Usage: {cpu_usage}%\n"
        f"📱 Hosted Accounts: {total_accounts}\n"
        f"🔓 Remaining Capacity: {hosting_capacity} accounts\n\n"
        "Made by - [dev](t.me/Uncountableaura)"
    )
    await event.reply(message)

# Function for adding a user to allowed list (owner only)
@bot_client.on(events.NewMessage(pattern='/add'))
async def add_user(event):
    """Adds a user to the allowed list."""
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("🚫 You are not authorized to use this command.")
        return

    message_parts = event.text.split(' ')
    if len(message_parts) != 2:
        await event.reply("⚠️ Invalid format. Use: /add <user_id>")
        return

    new_user_id = int(message_parts[1])
    ALLOWED_USERS.add(new_user_id)
    await event.reply(f"✅ User {new_user_id} has been added to the allowed list.")

# Function for listing all hosted accounts
@bot_client.on(events.NewMessage(pattern='/accounts'))
async def accounts_command(event):
    """Lists all hosted accounts."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("🚫 You are not authorized to use this bot.")
        return

    accounts = get_all_accounts()
    if not accounts:
        await event.reply("📭 No accounts are currently hosted.")
        return

    account_list = '\n'.join([f"{i+1}. {account['phone_number']}" for i, account in enumerate(accounts)])
    await event.reply(f"📋 **Hosted Accounts**:\n{account_list}\n\nMade by - [dev](t.me/Uncountableaura)")

# Handle /remove command to remove hosted accounts
@bot_client.on(events.NewMessage(pattern='/remove'))
async def remove_command(event):
    """Removes a hosted account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("🚫 You are not authorized to use this command.")
        return

    await event.reply("🔢 Send the phone number of the account you want to remove.")
    user_states[user_id] = {'step': 'awaiting_remove'}

@bot_client.on(events.NewMessage)
async def handle_remove(event):
    """Handles account removal."""
    user_id = event.sender_id
    if user_id not in user_states or user_states[user_id].get('step') != 'awaiting_remove':
        return

    phone_number = event.text.strip()
    remove_account_from_db(phone_number)
    await event.reply(f"✅ Account {phone_number} has been removed.")
    del user_states[user_id]

# Run the bot
print("Bot is running...")
bot_client.start(bot_token=BOT_API_TOKEN)
bot_client.run_until_disconnected()
