import re
import logging
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, FloodWait

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Bot credentials (replace with actual)
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"

# API credentials from my.telegram.org
API_ID = 26416419
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"  # Your API hash from my.telegram.org

# Store user session globally
user_client = None
user_states = {}  # Track user states during the hosting process
ALLOWED_USERS = [6748827895]  # Replace with actual user IDs who are allowed to use the bot
accounts = {}  # Store hosted accounts in a dictionary, indexed by phone numbers

# Initialize the bot client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# /start command for the bot
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Welcome! Use /host to log in as a user.")

# /host command (modified)
@bot.on_message(filters.command('host') | filters.command('addaccount'))
async def host_command(client, message):
    """Starts the hosting process for a new account."""
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS:
        await message.reply("You are not authorized to use this command.")
        return

    if user_id in user_states:
        if user_states[user_id].get('step') in ['awaiting_credentials', 'awaiting_otp']:
            await message.reply("You already have an active process. Please complete it before starting a new one.")
        else:
            del user_states[user_id]  # Remove any old process state
            await message.reply("You can start hosting a new account now.")
    else:
        user_states[user_id] = {'step': 'awaiting_credentials'}
        await message.reply("Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")

# /join command to join groups
@bot.on_message(filters.command("join"))
async def join_groups(client, message):
    global user_client
    if not user_client:
        await message.reply("No active user session. Please use /host to log in first!")
        return

    await message.reply("Please send the group links (separated by commas):")

    # Wait for group links input
    group_msg = await bot.listen(message.chat.id)
    group_links = [link.strip() for link in group_msg.text.split(",")]

    for link in group_links:
        match = re.search(r"(?:https?://)?t\.me/([\w_]+)", link)
        group_username = match.group(1) if match else (link[1:] if link.startswith("@") else None)

        if group_username:
            try:
                await user_client.join_chat(group_username)
                await message.reply(f"Successfully joined: {group_username}")
            except Exception as e:
                await message.reply(f"Failed to join {group_username}: {e}")
        else:
            await message.reply(f"Invalid link format: {link}")

# /forward command: Starts the ad forwarding process
@bot.on_message(filters.command('forward'))
async def forward_command(client, message):
    """Starts the ad forwarding process."""
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS:
        await message.reply("You are not authorized to use this command.")
        return

    if user_id in user_states:
        await message.reply("You already have an active process. Please complete it before starting a new one.")
        return

    if not accounts:
        await message.reply("No accounts are hosted. Use /host or /addaccount to add accounts.")
        return

    # Display list of hosted accounts
    account_list = '\n'.join([f"{i+1}. {phone}" for i, phone in enumerate(accounts.keys())])
    await message.reply(f"Choose an account to forward ads from:\n{account_list}\nReply with the number of the account.")

    user_states[user_id] = {'step': 'awaiting_account_choice'}

# Run the bot
bot.run()
