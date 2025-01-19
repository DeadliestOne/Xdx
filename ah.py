import os
import psutil
from telethon import TelegramClient, events
from telethon.tl.types import InputPeerChannel
from telethon import Button
from pymongo import MongoClient
from colorama import init

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "8015878481:AAGgbl0Ssx37pATFSISWqUu731qBpdBio68"

# MongoDB Configuration
MONGO_URI = "mongodb+srv://uchitraprobot2:Orion@cluster0.3es1c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB connection string
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
    """Welcome message for users with inline buttons."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("🚫 You are not authorized to use this bot.")
        return

    buttons = [
        [Button.inline("📱 Host Account", b"host_account")],
        [Button.inline("📋 List Accounts", b"list_accounts")],
        [Button.inline("🔄 Start Ad Forwarding", b"start_forwarding")],
        [Button.inline("📊 Stats", b"bot_stats")],
        [Button.inline("❌ Remove Account", b"remove_account")]
    ]

    await event.reply(
        "🤖 Welcome to the Hosting & Ad Forwarding Bot! Choose an option below:",
        buttons=buttons
    )

@bot.on(events.CallbackQuery)
async def handle_buttons(event):
    """Handle inline button clicks for the user interface."""
    user_id = event.sender_id
    data = event.data.decode()

    if data == "host_account":
        # Start hosting process (API ID, API Hash, Phone Number)
        user_states[user_id] = {'step': 'awaiting_credentials'}
        await event.answer("📩 Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")
    
    elif data == "list_accounts":
        # List hosted accounts
        accounts = get_all_accounts()
        if not accounts:
            await event.answer("📭 No accounts are currently hosted.")
        else:
            account_list = '\n'.join([f"{i+1}. {account['phone_number']}" for i, account in enumerate(accounts)])
            await event.answer(f"📋 **Hosted Accounts**:\n{account_list}")
    
    elif data == "start_forwarding":
        # Start the ad forwarding process
        user_states[user_id] = {'step': 'select_source'}
        await event.answer("🔄 Choose the source channel to forward ads from:")

        # Fetch available channels and show buttons for each
        # Example: list of channels the bot is part of or provided manually
        buttons = [
            [Button.inline("📢 Source Channel 1", b"source_channel_1")],
            [Button.inline("📢 Source Channel 2", b"source_channel_2")],
        ]
        await event.edit("📡 Select the source channel to forward ads from:", buttons=buttons)

    elif data == "bot_stats":
        # Show bot stats (CPU, RAM, etc.)
        ram_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)
        total_accounts = accounts_collection.count_documents({})
        hosting_capacity = max(0, 50 - total_accounts)  # Assuming a limit of 50 accounts

        stats_message = (
            f"📊 **Server Stats**:\n"
            f"💾 RAM Usage: {ram_usage}%\n"
            f"⚙️ CPU Usage: {cpu_usage}%\n"
            f"📱 Hosted Accounts: {total_accounts}\n"
            f"🔓 Remaining Capacity: {hosting_capacity} accounts"
        )
        await event.answer(stats_message)
    
    elif data == "remove_account":
        # Remove hosted account
        user_states[user_id] = {'step': 'awaiting_remove'}
        await event.answer("🔢 Send the phone number of the account you want to remove.")

# Handling forwarding
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

    elif state['step'] == 'awaiting_remove':
        phone_number = event.text.strip()
        remove_account_from_db(phone_number)
        await event.reply(f"✅ Account {phone_number} has been removed.")
        del user_states[user_id]

# Run the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
