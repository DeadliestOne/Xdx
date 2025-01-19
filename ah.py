import os
import psutil
from telethon import TelegramClient, events
from pymongo import MongoClient
from colorama import init

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "8015878481:AAGgbl0Ssx37pATFSISWqUu731qBpdBio68"

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"  # Replace with your MongoDB connection string
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
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

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

@bot.on(events.NewMessage(pattern='/start'))
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
        "👤 /add {user_id} - Add a user to the allowed list (owner only)"
    )

@bot.on(events.NewMessage(pattern='/stats'))
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
        f"🔓 Remaining Capacity: {hosting_capacity} accounts"
    )
    await event.reply(message)

@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    """Starts the hosting process for a new account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("🚫 You are not authorized to use this command.")
        return

    user_states[user_id] = {'step': 'awaiting_credentials'}
    await event.reply("📩 Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")

@bot.on(events.NewMessage)
async def process_input(event):
    """Processes user input for hosting accounts."""
    user_id = event.sender_id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    if state['step'] == 'awaiting_credentials':
        data = event.text.split('|')
        if len(data) != 3:
            await event.reply("⚠️ Invalid format. Please send data as:\n`API_ID|API_HASH|PHONE_NUMBER`")
            return

        api_id, api_hash, phone_number = data
        session_name = f"session_{phone_number}"
        client = TelegramClient(session_name, api_id, api_hash)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                state.update({'step': 'awaiting_otp', 'client': client, 'phone_number': phone_number})
                await event.reply("📲 OTP sent to your phone. Reply with the OTP.")
            else:
                save_account_to_db(api_id, api_hash, phone_number)
                await client.disconnect()
                await event.reply(f"✅ Account {phone_number} successfully hosted!")
                del user_states[user_id]
        except Exception as e:
            await event.reply(f"❌ Error: {e}")
            del user_states[user_id]

    elif state['step'] == 'awaiting_otp':
        otp = event.text.strip()
        client = state['client']
        phone_number = state['phone_number']

        try:
            await client.sign_in(phone_number, otp)
            save_account_to_db(client.api_id, client.api_hash, phone_number)
            await event.reply(f"✅ Account {phone_number} successfully hosted!")
            del user_states[user_id]
        except Exception as e:
            await event.reply(f"❌ Error: {e}")
            del user_states[user_id]

@bot.on(events.NewMessage(pattern='/accounts'))
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
    await event.reply(f"📋 **Hosted Accounts**:\n{account_list}")

@bot.on(events.NewMessage(pattern='/remove'))
async def remove_command(event):
    """Removes a hosted account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("🚫 You are not authorized to use this command.")
        return

    await event.reply("🔢 Send the phone number of the account you want to remove.")

    user_states[user_id] = {'step': 'awaiting_remove'}

@bot.on(events.NewMessage)
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
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
