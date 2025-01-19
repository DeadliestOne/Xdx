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
    """Displays the main menu with inline buttons."""
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

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    """Handles the callback from the inline buttons."""
    action = event.data.decode()

    if action == 'host_account':
        await event.respond("📩 Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")
        user_states[event.sender_id] = {'step': 'awaiting_credentials'}
    
    elif action == 'list_accounts':
        accounts = get_all_accounts()
        if not accounts:
            await event.respond("📭 No accounts are currently hosted.")
            return

        account_list = '\n'.join([f"{i+1}. {account['phone_number']}" for i, account in enumerate(accounts)])
        await event.respond(f"📋 **Hosted Accounts**:\n{account_list}")

    elif action == 'server_stats':
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
        await event.respond(message)

    elif action == 'add_user':
        # Add user feature (for owner only)
        await event.respond("🔑 Send the user ID you want to add.")
        user_states[event.sender_id] = {'step': 'awaiting_add_user'}

    elif action == 'remove_account':
        await event.respond("🔢 Send the phone number of the account you want to remove.")
        user_states[event.sender_id] = {'step': 'awaiting_remove'}

@bot.on(events.NewMessage)
async def process_input(event):
    """Processes user input for hosting accounts and other commands."""
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

    elif state['step'] == 'awaiting_add_user':
        user_input = event.text.strip()
        if user_input.isdigit():
            new_user_id = int(user_input)
            ALLOWED_USERS.add(new_user_id)
            await event.reply(f"User {new_user_id} added to the allowed list.")
            del user_states[user_id]
        else:
            await event.reply("❌ Invalid user ID format.")

    elif state['step'] == 'awaiting_remove':
        phone_number = event.text.strip()
        remove_account_from_db(phone_number)
        await event.reply(f"✅ Account {phone_number} has been removed.")
        del user_states[user_id]

# Send startup message to the owner
async def send_startup_message():
    """Sends a message when the bot starts up."""
    owner = await bot.get_entity(OWNER_ID)
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    await bot.send_message(owner, f"✅ Bot Started!\n\n"
                                  f"⚙️ CPU Usage: {cpu_usage}%\n"
                                  f"💾 RAM Usage: {ram_usage}%\n"
                                  f"👤 Bot is running successfully.")

# Run the bot
print("Bot is starting...")
bot.start(bot_token=BOT_API_TOKEN)
bot.loop.run_until_complete(send_startup_message())
bot.run_until_disconnected()
