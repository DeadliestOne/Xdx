import logging
import re
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, FloodWait
from pyrogram.types import Message

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Bot credentials (replace with actual)
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"
API_ID = 26416419
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"  # Your API hash from my.telegram.org

# Store user session globally
user_client = None
user_states = {}  # Track user states during the hosting process
ALLOWED_USERS = [6748827895]  # Replace with actual user IDs who are allowed to use the bot
accounts = {}  # Store hosted accounts in a dictionary, indexed by phone numbers

# Initialize the bot client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Function to prompt the user for their credentials
async def prompt_credentials(message: Message):
    await message.reply("Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")


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
        await prompt_credentials(message)


# Handle receiving credentials (API ID, API HASH, Phone Number)
@bot.on_message(filters.text & ~filters.command("start"))
async def handle_credentials(client, message: Message):
    user_id = message.from_user.id

    # Check if the user is in the credentials stage
    if user_id not in user_states or user_states[user_id].get('step') != 'awaiting_credentials':
        return

    # Process credentials input
    credentials = message.text.strip()
    parts = credentials.split('|')
    
    if len(parts) != 3:
        await message.reply("Invalid format. Please send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")
        return

    api_id, api_hash, phone_number = parts
    logger.info(f"Received credentials: API_ID={api_id}, API_HASH={api_hash}, PHONE_NUMBER={phone_number}")

    # Initialize the user session
    global user_client
    user_client = Client("userbot", api_id=int(api_id), api_hash=api_hash)

    # Try to send OTP
    try:
        await user_client.connect()
        sent_code = await user_client.send_code(phone_number)
        user_states[user_id]['step'] = 'awaiting_otp'

        await message.reply("OTP sent! Please enter the OTP:")
    except Exception as e:
        await message.reply(f"Error: {e}")
        user_states[user_id] = {'step': 'awaiting_credentials'}


# Handle receiving OTP
@bot.on_message(filters.text)
async def handle_otp(client, message: Message):
    user_id = message.from_user.id

    # Check if the user is in the OTP stage
    if user_id not in user_states or user_states[user_id].get('step') != 'awaiting_otp':
        return

    otp_code = message.text.strip()
    logger.info(f"Received OTP: {otp_code}")

    # Try signing in with OTP
    try:
        sent_code = await user_client.send_code()
        await user_client.sign_in(message.text, otp_code, phone_code_hash=sent_code.phone_code_hash)

        user_states[user_id]['step'] = 'logged_in'
        await message.reply("Successfully logged in! Now you can use /join to add groups.")
    except SessionPasswordNeeded:
        await message.reply("Two-step verification is enabled. Please enter your password:")
        user_states[user_id]['step'] = 'awaiting_password'
    except Exception as e:
        await message.reply(f"Error: {e}")
        user_states[user_id] = {'step': 'awaiting_credentials'}


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


# Run the bot
bot.run()
