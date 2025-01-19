import asyncio
import os
import json
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError, PhoneCodeFloodError
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerUser
from pymongo import MongoClient

# MongoDB Configuration
MONGO_URI = "mongodb+srv://uchitraprobot2:Orion@cluster0.3es1c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "telegram_bot"
COLLECTION_NAME = "hosted_accounts"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
accounts_collection = db[COLLECTION_NAME]

# Session folder
CREDENTIALS_FOLDER = 'sessions'
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Save and load credentials
def save_credentials(session_name, credentials):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, 'w') as f:
        json.dump(credentials, f)

def load_credentials(session_name):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

# Bot token and owner ID
OWNER_ID = 6748827895  # Replace with the owner user ID
BOT_TOKEN = "8015878481:AAGgbl0Ssx37pATFSISWqUu731qBpdBio68"  # Replace with your bot token

# MongoDB Bot-related functions
def save_account_to_db(api_id, api_hash, phone_number):
    accounts_collection.update_one(
        {"phone_number": phone_number},
        {"$set": {"api_id": api_id, "api_hash": api_hash, "phone_number": phone_number}},
        upsert=True
    )

# Initialize the bot client
bot_client = TelegramClient('bot_session', api_id=26416419, api_hash='c109c77f5823c847b1aeb7fbd4990cc4')

# Initialize the Telegram client for user
async def initialize_user_client(api_id, api_hash, phone_number, session_name):
    user_client = TelegramClient(session_name, api_id, api_hash)
    await user_client.start(phone=phone_number)
    return user_client

# Bot command to start
@bot_client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
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

# Handling callback queries
@bot_client.on(events.CallbackQuery)
async def handle_buttons(event):
    user_id = event.sender_id
    data = event.data.decode()

    if data == "host_account":
        await event.answer("📩 Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")

    elif data == "list_accounts":
        accounts = accounts_collection.find()
        account_list = '\n'.join([f"{i+1}. {account['phone_number']}" for i, account in enumerate(accounts)])
        await event.answer(f"📋 **Hosted Accounts**:\n{account_list}")

    elif data == "start_forwarding":
        await event.answer("🔄 Starting Ad Forwarding...")

    elif data == "bot_stats":
        # Gather stats like RAM, CPU usage, etc.
        pass

    elif data == "remove_account":
        await event.answer("🔢 Send the phone number of the account you want to remove.")

# Handle incoming messages for account hosting
@bot_client.on(events.NewMessage)
async def process_input(event):
    user_id = event.sender_id
    text = event.text.strip()

    if user_id != OWNER_ID:
        return

    # Step: Hosting account
    if text.count('|') == 2:
        api_id, api_hash, phone_number = text.split('|')
        session_name = f"session_{phone_number}"

        user_client = await initialize_user_client(api_id, api_hash, phone_number, session_name)
        save_account_to_db(api_id, api_hash, phone_number)

        await user_client.disconnect()
        await event.reply(f"✅ Account {phone_number} successfully hosted!")

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

        except PhoneCodeFloodError:
            await event.reply("⚠️ You are sending requests too quickly. Please try again later.")
        except Exception as e:
            await event.reply(f"❌ Error: {e}")

# Remove account from the database
@bot_client.on(events.NewMessage)
async def remove_account(event):
    user_id = event.sender_id
    text = event.text.strip()

    if user_id != OWNER_ID:
        return

    if text.startswith("remove_"):
        phone_number = text.split("_")[1]
        accounts_collection.delete_one({"phone_number": phone_number})
        await event.reply(f"✅ Account {phone_number} has been removed.")

# Run the bot
print("Bot is running...")
bot_client.start(bot_token=BOT_TOKEN)
bot_client.run_until_disconnected()
