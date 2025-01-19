import asyncio
import os
import json
from telethon import TelegramClient, errors
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerUser, InputPeerChannel
from telethon import Button
from pymongo import MongoClient
from colorama import init, Fore
import pyfiglet
from telethon.tl import types

# Initialize colorama for colored output
init(autoreset=True)

CREDENTIALS_FOLDER = 'sessions'
MONGO_URI = "mongodb+srv://uchitraprobot2:Orion@cluster0.3es1c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB connection string
DB_NAME = "telegram_bot"
COLLECTION_NAME = "hosted_accounts"

# MongoDB Configuration
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
accounts_collection = db[COLLECTION_NAME]

# Create a session folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Function to save credentials to a file
def save_credentials(session_name, credentials):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, 'w') as f:
        json.dump(credentials, f)

# Function to load credentials from a file
def load_credentials(session_name):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

# Function to save account details to MongoDB
def save_account_to_db(api_id, api_hash, phone_number):
    accounts_collection.update_one(
        {"phone_number": phone_number},
        {"$set": {"api_id": api_id, "api_hash": api_hash, "phone_number": phone_number}},
        upsert=True
    )

# Function to get all accounts from MongoDB
def get_all_accounts():
    return list(accounts_collection.find())

# Function to remove an account from MongoDB
def remove_account_from_db(phone_number):
    accounts_collection.delete_one({"phone_number": phone_number})

# Function to display banner
def display_banner():
    print(Fore.RED + pyfiglet.figlet_format("rio"))
    print(Fore.GREEN + "Made by @evyti\n")

# Function to forward messages to all groups
async def login_and_forward(api_id, api_hash, phone_number, session_name):
    client = TelegramClient(session_name, api_id, api_hash)

    await client.start(phone=phone_number)

    try:
        if await client.is_user_authorized() is False:
            await client.send_code_request(phone_number)
            await client.sign_in(phone_number)
    except SessionPasswordNeededError:
        password = input("Two-factor authentication enabled. Enter your password: ")
        await client.sign_in(password=password)

    saved_messages_peer = await client.get_input_entity('me')
    
    # Corrected GetHistoryRequest with missing arguments
    history = await client(GetHistoryRequest(
        peer=saved_messages_peer,
        limit=1,
        offset_id=0,
        offset_date=None,
        add_offset=0,
        max_id=0,
        min_id=0,
        hash=0
    ))

    if not history.messages:
        print("No messages found in 'Saved Messages'")
        return

    last_message = history.messages[0]

    # Ask how many times and delay after login
    repeat_count = int(input(f"How many times do you want to send the message to all groups for {session_name}? "))
    delay_between_rounds = int(input(f"Enter the delay (in seconds) between each round for {session_name}: "))

    for round_num in range(1, repeat_count + 1):
        print(f"\nStarting round {round_num} of forwarding messages to all groups for {session_name}.")

        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group = dialog.entity
                try:
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                except Exception as e:
                    print(Fore.RED + f"Failed to forward message to {group.title}: {str(e)}")
                await asyncio.sleep(3)

        if round_num < repeat_count:
            print(f"Delaying for {delay_between_rounds} seconds before the next round.")
            await asyncio.sleep(delay_between_rounds)

    await client.disconnect()

# Function to leave unwanted groups
async def leave_unwanted_groups(client):
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group = dialog.entity
            try:
                await client.send_message(group.id, "dm @Legitdeals9")
                print(Fore.GREEN + f"Message sent to {group.title}")
            except Exception as e:
                print(Fore.RED + f"Leaving {group.title} as message sending failed: {e}")
                await client(LeaveChannelRequest(group))
                print(Fore.YELLOW + f"Left group {group.title}")

# MongoDB bot functionality
from telethon import TelegramClient, events, Button

OWNER_ID = 6748827895  # Replace with the owner user ID
ALLOWED_USERS = set([OWNER_ID])  # Initially allow only the owner

user_states = {}

# Initialize Telegram bot
bot = TelegramClient('bot_session', 26416419, 'c109c77f5823c847b1aeb7fbd4990cc4')

@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
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
    user_id = event.sender_id
    data = event.data.decode()

    if data == "host_account":
        user_states[user_id] = {'step': 'awaiting_credentials'}
        await event.answer("📩 Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")
    
    elif data == "list_accounts":
        accounts = get_all_accounts()
        if not accounts:
            await event.answer("📭 No accounts are currently hosted.")
        else:
            account_list = '\n'.join([f"{i+1}. {account['phone_number']}" for i, account in enumerate(accounts)])
            await event.answer(f"📋 **Hosted Accounts**:\n{account_list}")
    
    elif data == "start_forwarding":
        user_states[user_id] = {'step': 'start_forwarding'}
        await event.answer("🔄 Starting Ad Forwarding... It will use the most recent saved message as the source.")
        # Start forwarding automatically without asking for the source channel

    elif data == "bot_stats":
        ram_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)
        total_accounts = accounts_collection.count_documents({})
        hosting_capacity = max(0, 50 - total_accounts)

        stats_message = (
            f"📊 **Server Stats**:\n"
            f"💾 RAM Usage: {ram_usage}%\n"
            f"⚙️ CPU Usage: {cpu_usage}%\n"
            f"📱 Hosted Accounts: {total_accounts}\n"
            f"🔓 Remaining Capacity: {hosting_capacity} accounts"
        )
        await event.answer(stats_message)
    
    elif data == "remove_account":
        user_states[user_id] = {'step': 'awaiting_remove'}
        await event.answer("🔢 Send the phone number of the account you want to remove.")

@bot.on(events.NewMessage)
async def process_input(event):
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
bot.start(bot_token="YOUR_BOT_TOKEN")
bot.run_until_disconnected()
