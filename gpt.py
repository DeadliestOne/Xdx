import os
import asyncio
import psutil  # For system stats
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from colorama import init
import random

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "7571130552:AAEG4RzTbLLibOS0wICJwgTkIFMF1d402uI"

CREDENTIALS_FOLDER = 'sessions'

# Create sessions folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Initialize Telegram bot without proxy support
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# Define the bot owner and allowed users
OWNER_ID = 6748827895  # Replace with the owner user ID
ALLOWED_USERS = set([OWNER_ID])  # Initially allow only the owner

# User states to track ongoing processes
user_states = {}
accounts = {}  # Hosted accounts

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Welcome message with inline buttons."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this bot. Contact @UncountableAura for access.")
        return

    buttons = [
        [Button.inline("Host New Account", b"host_account"), Button.inline("Forward Ads", b"forward_ads")],
        [Button.inline("List Accounts", b"list_accounts"), Button.inline("Remove Account", b"remove_account")],
        [Button.inline("Server Stats", b"server_stats")],
    ]
    await event.respond(
        "Welcome! Use the buttons below to interact with the bot:",
        buttons=buttons,
    )

@bot.on(events.CallbackQuery)
async def handle_buttons(event):
    """Handle inline button interactions."""
    if event.data == b"host_account":
        await host_command(event)
    elif event.data == b"forward_ads":
        await forward_command(event)
    elif event.data == b"list_accounts":
        await accounts_command(event)
    elif event.data == b"remove_account":
        await remove_command(event)
    elif event.data == b"server_stats":
        await stats_command(event)

# /host command: Starts hosting a new account
@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    """Starts the hosting process for a new account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    user_states[user_id] = {'step': 'awaiting_credentials'}
    await event.reply("Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")

# Process user credentials for hosting
@bot.on(events.NewMessage)
async def process_hosting(event):
    user_id = event.sender_id
    if user_id not in user_states or user_states[user_id].get('step') != 'awaiting_credentials':
        return

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
            user_states[user_id].update({'step': 'awaiting_otp', 'client': client, 'phone_number': phone_number})
            await event.reply("OTP sent to your phone. Reply with the OTP.")
        else:
            accounts[phone_number] = client
            await client.disconnect()
            await event.reply(f"Account {phone_number} is already authorized and hosted!")
            del user_states[user_id]
    except Exception as e:
        await event.reply(f"Error: {e}")
        del user_states[user_id]

# /forward command: Starts forwarding process
@bot.on(events.NewMessage(pattern='/forward'))
async def forward_command(event):
    """Starts the ad forwarding process."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    if not accounts:
        await event.reply("No accounts are hosted. Use /host to add accounts.")
        return

    account_list = '\n'.join([f"{i + 1}. {phone}" for i, phone in enumerate(accounts.keys())])
    await event.reply(f"Choose an account to forward ads from:\n{account_list}\nReply with the number of the account.")
    user_states[user_id] = {'step': 'awaiting_account_choice'}

# Handle forwarding choices
@bot.on(events.NewMessage)
async def handle_forwarding(event):
    user_id = event.sender_id
    if user_id not in user_states or user_states[user_id].get('step') != 'awaiting_account_choice':
        return

    try:
        account_choice = int(event.text.strip()) - 1
        if 0 <= account_choice < len(accounts):
            selected_account = list(accounts.keys())[account_choice]
            await event.reply(f"Selected account {selected_account}. Forwarding will start shortly.")
            # Implement forwarding logic here
            del user_states[user_id]
        else:
            await event.reply("Invalid account number.")
    except ValueError:
        await event.reply("Please provide a valid number.")

# /stats command: Displays server statistics
@bot.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    """Displays server statistics."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    stats = (
        f"**Server Stats:**\n\n"
        f"**CPU Usage:** {cpu_usage}%\n"
        f"**RAM Usage:** {ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB ({ram.percent}%)\n"
        f"**Disk Usage:** {disk.used / (1024**3):.2f} GB / {disk.total / (1024**3):.2f} GB ({disk.percent}%)"
    )
    await event.reply(stats)

# Run the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
