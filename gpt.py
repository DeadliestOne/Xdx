import os
import psutil
import asyncio
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from colorama import init
import random

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "8075027784:AAFJ80wXsED8_2oMlivB46RZZwI7sm7xcL4"

CREDENTIALS_FOLDER = 'sessions'

# Create sessions folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Initialize Telegram bot
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# Define the bot owner and allowed users
OWNER_ID = 6748827895  # Replace with the owner user ID
ALLOWED_USERS = set([OWNER_ID])  # Initially allow only the owner

# User states to track ongoing processes
user_states = {}
accounts = {}  # Hosted accounts


@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Welcome message for users."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this bot.")
        return

    await event.reply(
        "Welcome! Use the following commands:\n\n"
        "/host - Host a new Telegram account\n"
        "/forward - Start forwarding ads\n"
        "/accounts - List hosted accounts\n"
        "/remove - Remove a hosted account\n"
        "/add {user_id} - Add a user to the allowed list (owner only)\n"
        "/stats - View server stats and hosting capacity"
    )


@bot.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    """Displays server stats and hosted accounts information."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this bot.")
        return

    # Fetch system stats
    ram_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)
    total_accounts = len(accounts)
    hosting_capacity = max(0, 50 - total_accounts)  # Assuming a limit of 50 accounts

    message = (
        f"Server Stats:\n"
        f"RAM Usage: {ram_usage}%\n"
        f"CPU Usage: {cpu_usage}%\n"
        f"Hosted Accounts: {total_accounts}\n"
        f"Remaining Hosting Capacity: {hosting_capacity} accounts"
    )
    await event.reply(message)


@bot.on(events.NewMessage(pattern='/add'))
async def add_command(event):
    """Adds a user to the allowed list."""
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("You are not authorized to use this command.")
        return

    user_input = event.text.split()
    if len(user_input) != 2:
        await event.reply("Usage: /add {user_id}")
        return

    try:
        new_user_id = int(user_input[1])
        ALLOWED_USERS.add(new_user_id)
        await event.reply(f"User {new_user_id} added to the allowed list.")
    except ValueError:
        await event.reply("Invalid user ID.")


@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    """Starts the hosting process for a new account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    user_states[user_id] = {'step': 'awaiting_credentials'}
    await event.reply("Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")


@bot.on(events.NewMessage)
async def process_input(event):
    """Processes user input for hosting or forwarding accounts."""
    user_id = event.sender_id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    if state['step'] == 'awaiting_credentials':
        data = event.text.split('|')
        if len(data) != 3:
            await event.reply("Invalid format. Please send data as:\n`API_ID|API_HASH|PHONE_NUMBER`")
            return

        api_id, api_hash, phone_number = data
        session_name = f"{CREDENTIALS_FOLDER}/session_{user_id}_{phone_number}"
        client = TelegramClient(session_name, api_id, api_hash)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                state.update({'step': 'awaiting_otp', 'client': client, 'phone_number': phone_number})
                await event.reply("OTP sent to your phone. Reply with the OTP.")
            else:
                accounts[phone_number] = client
                await client.disconnect()
                await event.reply(f"Account {phone_number} successfully hosted!")
                del user_states[user_id]
        except Exception as e:
            await event.reply(f"Error: {e}")
            del user_states[user_id]

    elif state['step'] == 'awaiting_otp':
        otp = event.text.strip()
        client = state['client']
        phone_number = state['phone_number']

        try:
            await client.sign_in(phone_number, otp)
            accounts[phone_number] = client
            await event.reply(f"Account {phone_number} successfully hosted!")
            del user_states[user_id]
        except Exception as e:
            await event.reply(f"Error: {e}")
            del user_states[user_id]


@bot.on(events.NewMessage(pattern='/accounts'))
async def accounts_command(event):
    """Lists all hosted accounts."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    if not accounts:
        await event.reply("No accounts are hosted.")
        return

    account_list = '\n'.join([f"{i+1}. {phone}" for i, phone in enumerate(accounts.keys())])
    await event.reply(f"Hosted accounts:\n{account_list}")


# Run the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
