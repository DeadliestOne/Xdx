import os
import asyncio
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
    ]
    await event.respond(
        "Welcome! Use the buttons below to interact with the bot:",
        buttons=buttons,
    )

@bot.on(events.CallbackQuery)
async def handle_buttons(event):
    """Handle inline button interactions."""
    if event.data == b"host_account":
        await event.edit("You selected to host a new account. Use /host to start.")
    elif event.data == b"forward_ads":
        await event.edit("You selected to forward ads. Use /forward to start.")
    elif event.data == b"list_accounts":
        await accounts_command(event)
    elif event.data == b"remove_account":
        await remove_command(event)

# /accounts command: Lists all hosted accounts
async def accounts_command(event):
    """Lists all hosted accounts."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    if not accounts:
        await event.reply("No accounts are hosted.")
        return

    account_list = '\n'.join([f"{i + 1}. {phone}" for i, phone in enumerate(accounts.keys())])
    await event.reply(f"Hosted accounts:\n{account_list}")

# /remove command: Removes a hosted account
async def remove_command(event):
    """Removes a hosted account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    if not accounts:
        await event.reply("No accounts are hosted.")
        return

    account_list = '\n'.join([f"{i + 1}. {phone}" for i, phone in enumerate(accounts.keys())])
    await event.reply(f"Choose an account to remove:\n{account_list}\nReply with the number of the account.")
    user_states[user_id] = {'step': 'awaiting_remove_choice'}

# Run the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
