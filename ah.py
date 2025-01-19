import os
import psutil
from telethon import TelegramClient, events, Button
from pymongo import MongoClient
from colorama import init

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
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# Helper functions for MongoDB
def save_account_to_db(api_id, api_hash, phone_number):
    accounts_collection.update_one(
        {"phone_number": phone_number},
        {"$set": {"api_id": api_id, "api_hash": api_hash, "phone_number": phone_number}},
        upsert=True
    )

def get_all_accounts():
    return list(accounts_collection.find())

def remove_account_from_db(phone_number):
    accounts_collection.delete_one({"phone_number": phone_number})

async def main_menu(event):
    """Displays the main menu."""
    await event.respond(
        "🤖 **Main Menu**\nChoose an option below:",
        buttons=[
            [Button.inline("📡 Host Account", b"host_account")],
            [Button.inline("🔄 List Accounts", b"list_accounts")],
            [Button.inline("📊 Server Stats", b"server_stats")],
            [Button.inline("👤 Add User", b"add_user")],
            [Button.inline("❌ Remove Account", b"remove_account")],
        ]
    )

@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Welcome message with inline buttons."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    await main_menu(event)

@bot.on(events.CallbackQuery(data=b"host_account"))
async def host_account_callback(event):
    """Starts the hosting process for a new account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.answer("🚫 You are not authorized to use this feature.", alert=True)
        return

    user_states[user_id] = {'step': 'awaiting_credentials'}
    await event.edit(
        "📩 Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`",
        buttons=[Button.inline("🔙 Back", b"back_to_menu")]
    )

@bot.on(events.CallbackQuery(data=b"list_accounts"))
async def list_accounts_callback(event):
    """Lists all hosted accounts."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.answer("🚫 You are not authorized to use this feature.", alert=True)
        return

    accounts = get_all_accounts()
    if not accounts:
        await event.edit(
            "📭 **No accounts are currently hosted.**",
            buttons=[Button.inline("🔙 Back", b"back_to_menu")]
        )
        return

    account_list = '\n'.join([f"{i+1}. {account['phone_number']}" for i, account in enumerate(accounts)])
    await event.edit(
        f"📋 **Hosted Accounts:**\n{account_list}",
        buttons=[Button.inline("🔙 Back", b"back_to_menu")]
    )

@bot.on(events.CallbackQuery(data=b"server_stats"))
async def server_stats_callback(event):
    """Displays server stats and hosting capacity."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.answer("🚫 You are not authorized to use this feature.", alert=True)
        return

    ram_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)
    total_accounts = accounts_collection.count_documents({})
    hosting_capacity = max(0, 50 - total_accounts)

    message = (
        f"📊 **Server Stats**:\n"
        f"💾 RAM Usage: {ram_usage}%\n"
        f"⚙️ CPU Usage: {cpu_usage}%\n"
        f"📱 Hosted Accounts: {total_accounts}\n"
        f"🔓 Remaining Capacity: {hosting_capacity} accounts"
    )
    await event.edit(
        message,
        buttons=[Button.inline("🔙 Back", b"back_to_menu")]
    )

@bot.on(events.CallbackQuery(data=b"add_user"))
async def add_user_callback(event):
    """Prompts the owner to add a new user."""
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.answer("🚫 You are not authorized to use this feature.", alert=True)
        return

    user_states[user_id] = {'step': 'awaiting_add_user'}
    await event.edit(
        "👤 Send the user ID of the person you want to add.",
        buttons=[Button.inline("🔙 Back", b"back_to_menu")]
    )

@bot.on(events.CallbackQuery(data=b"remove_account"))
async def remove_account_callback(event):
    """Prompts the user to remove an account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.answer("🚫 You are not authorized to use this feature.", alert=True)
        return

    user_states[user_id] = {'step': 'awaiting_remove_account'}
    await event.edit(
        "❌ Send the phone number of the account you want to remove.",
        buttons=[Button.inline("🔙 Back", b"back_to_menu")]
    )

@bot.on(events.CallbackQuery(data=b"back_to_menu"))
async def back_to_menu_callback(event):
    """Handles navigation back to the main menu."""
    await main_menu(event)

@bot.on(events.NewMessage)
async def handle_user_input(event):
    """Handles dynamic user input."""
    user_id = event.sender_id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    if state.get('step') == 'awaiting_add_user':
        try:
            new_user_id = int(event.text.strip())
            ALLOWED_USERS.add(new_user_id)
            await event.reply(f"✅ User {new_user_id} has been added to the allowed list.")
            del user_states[user_id]
        except ValueError:
            await event.reply("❌ Invalid user ID.")

    elif state.get('step') == 'awaiting_remove_account':
        phone_number = event.text.strip()
        remove_account_from_db(phone_number)
        await event.reply(f"✅ Account {phone_number} has been removed.")
        del user_states[user_id]

# Bot startup message to owner
async def send_startup_message():
    ram_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)
    total_accounts = accounts_collection.count_documents({})

    message = (
        f"🚀 **Bot Started**\n"
        f"🤖 Users: {len(ALLOWED_USERS)}\n"
        f"💾 RAM Usage: {ram_usage}%\n"
        f"⚙️ CPU Usage: {cpu_usage}%\n"
        f"📱 Hosted Accounts: {total_accounts}"
    )
    await bot.send_message(OWNER_ID, message)

# Run the bot
print("Bot is starting...")
bot.start(bot_token=BOT_API_TOKEN)
bot.loop.run_until_complete(send_startup_message())
bot.run_until_disconnected()
