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
        [Button.text("Host New Account", resize=True), Button.text("Forward Ads", resize=True)],
        [Button.text("List Accounts", resize=True), Button.text("Remove Account", resize=True)],
    ]
    await event.respond(
        "Welcome! Use the buttons below to interact with the bot:",
        buttons=buttons,
    )

@bot.on(events.CallbackQuery)
async def handle_buttons(event):
    """Handle inline button interactions."""
    if event.data == b"Host New Account":
        await host_command(event)
    elif event.data == b"Forward Ads":
        await forward_command(event)
    elif event.data == b"List Accounts":
        await accounts_command(event)
    elif event.data == b"Remove Account":
        await remove_command(event)

# /add command: Adds a user to the allowed users list (owner only)
@bot.on(events.NewMessage(pattern='/add'))
async def add_command(event):
    """Adds a user to the allowed list."""
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("You are not authorized to use this command.")
        return

    # Get the user ID from the message
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

# /accounts command: Lists all hosted accounts
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

    account_list = '\n'.join([f"{i + 1}. {phone}" for i, phone in enumerate(accounts.keys())])
    await event.reply(f"Hosted accounts:\n{account_list}")

# /remove command: Removes a hosted account
@bot.on(events.NewMessage(pattern='/remove'))
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

# Other parts of the code remain unchanged.

# Run the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
