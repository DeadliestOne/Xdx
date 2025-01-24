import os
import asyncio
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from colorama import init
from pymongo import MongoClient
import random

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "7226701592:AAE7AGWAU0BXgw-PmLfhgarpCT4-2wrBdwE"
MONGO_URI = "mongodb+srv://uchitraprobot2:Orion@cluster0.3es1c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/"  # Replace with your MongoDB URI

CREDENTIALS_FOLDER = 'sessions'

# Create sessions folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Initialize Telegram bot
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['telegram_bot']  # Database name
users_collection = db['users']    # Collection for storing user information

# Initialize user states and hosted accounts
user_states = {}
accounts = {}  # Hosted accounts

# Get bot owner from the database or set it initially
OWNER_ID = 6748827895
owner_doc = users_collection.find_one({"role": "owner"})
if owner_doc:
    OWNER_ID = owner_doc["user_id"]
else:
    print("Owner not set. Set the OWNER_ID in the database.")

# Utility to check if a user is authorized
def is_authorized(user_id):
    user = users_collection.find_one({"user_id": user_id})
    return user is not None

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Welcome message for users."""
    user_id = event.sender_id

    if not is_authorized(user_id):
        await event.reply("You are not authorized to use this bot.")
        return

    await event.reply("Welcome! Use the following commands:\n\n"
                      "/host - Host a new Telegram account\n"
                      "/forward - Start forwarding ads\n"
                      "/accounts - List hosted accounts\n"
                      "/remove - Remove a hosted account\n"
                      "/adduser - Add an authorized user (owner only)\n"
                      "/removeuser - Remove an authorized user (owner only)")

@bot.on(events.NewMessage(pattern='/forward'))
async def forward_command(event):
    """Starts the ad forwarding process."""
    user_id = event.sender_id
    if not is_authorized(user_id):
        await event.reply("You are not authorized to use this bot.")
        return

    if user_id in user_states:
        await event.reply("You already have an active process. Please complete it before starting a new one.")
        return

    if not accounts:
        await event.reply("No accounts are hosted. Use /host or /addaccount to add accounts.")
        return

    user_states[user_id] = {'step': 'awaiting_message_count'}
    await event.reply("How many messages would you like to forward per group (1-5)?")

@bot.on(events.NewMessage)
async def process_input(event):
    """Processes user input for account hosting or forwarding."""
    user_id = event.sender_id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    # Handling forwarding process steps (message count, rounds, delay)
    if state['step'] == 'awaiting_message_count':
        try:
            message_count = int(event.text.strip())
            if 1 <= message_count <= 5:
                state['message_count'] = message_count
                state['step'] = 'awaiting_rounds'
                await event.reply("How many rounds of ads would you like to run?")
            else:
                await event.reply("Please choose a number between 1 and 5.")
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_rounds':
        try:
            rounds = int(event.text.strip())
            state['rounds'] = rounds
            state['step'] = 'awaiting_delay'
            await event.reply("Enter delay (in seconds) between rounds.")
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_delay':
        try:
            delay = int(event.text.strip())
            state['delay'] = delay
            await event.reply("Starting the ad forwarding process...")
            await forward_ads(state['message_count'], state['rounds'], state['delay'], user_id)
            del user_states[user_id]  # Clear user state after completing forwarding
        except ValueError:
            await event.reply("Please provide a valid number.")

async def forward_ads(message_count, rounds, delay, user_id):
    """Forwards ads to all groups for all hosted accounts."""
    for phone_number, client in accounts.items():
        await client.connect()
        saved_messages = await client.get_messages('me', limit=message_count)
        if not saved_messages or len(saved_messages) < message_count:
            await bot.send_message(user_id, f"Not enough messages in 'Saved Messages' for account {phone_number}.")
            continue

        for round_num in range(1, rounds + 1):
            await bot.send_message(user_id, f"Starting round {round_num} for account {phone_number}...")
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    group = dialog.entity
                    for message in saved_messages:
                        try:
                            await client.forward_messages(group.id, message)
                            print(f"Ad forwarded to {group.title} from account {phone_number}.")
                            # Random delay between messages
                            await asyncio.sleep(random.uniform(2, 4))
                        except FloodWaitError as e:
                            print(f"Rate limited. Waiting for {e.seconds} seconds.")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            print(f"Failed to forward to {group.title}: {e}")
            if round_num < rounds:
                print(f"Waiting {delay} seconds before the next round...")
                await asyncio.sleep(delay)
        await bot.send_message(user_id, f"Completed forwarding ads for account {phone_number}.")

# /adduser, /removeuser, and /accounts commands from the previous version remain the same

print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
