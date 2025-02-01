import logging
import os
import json
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import Message

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Bot credentials (replace with actual)
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"
API_ID = 26416419
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"  # Your API hash from my.telegram.org

CREDENTIALS_FOLDER = 'sessions'

# Create a session folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

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

# Initialize the bot client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# /host command: Starts the hosting process for a new account
@bot.on_message(filters.command("host"))
async def host_command(client, message: Message):
    """Starts the hosting process for a new account."""

    # Ask for phone number
    await message.reply("Please enter your **phone number** (with country code):")

    # Wait for the phone number input from the user
    phone_msg = await bot.listen(message.chat.id)
    phone_number = phone_msg.text.strip()

    # Load saved credentials or ask for new credentials
    session_name = f"session_{phone_number}"
    credentials = load_credentials(session_name)

    if credentials:
        await message.reply(f"Using saved credentials for {phone_number}.")
        api_id = credentials['api_id']
        api_hash = credentials['api_hash']
        phone_number = credentials['phone_number']
    else:
        await message.reply("Enter API ID and API Hash for your account.")
        api_id = int(await bot.listen(message.chat.id))
        api_hash = await bot.listen(message.chat.id)
        
        credentials = {
            'api_id': api_id,
            'api_hash': api_hash,
            'phone_number': phone_number
        }
        save_credentials(session_name, credentials)

    # Create client instance
    user_client = Client(session_name, api_id=api_id, api_hash=api_hash)

    try:
        await user_client.connect()
        # Check if user is authorized
        if not await user_client.is_user_authorized():
            await user_client.send_code_request(phone_number)
            await user_client.sign_in(phone_number)

        # Handle two-factor authentication
        if user_client.is_authorized() is False:
            await message.reply("Two-factor authentication is enabled. Please enter your password:")
            password_msg = await bot.listen(message.chat.id)
            password = password_msg.text.strip()
            await user_client.sign_in(password=password)

        await message.reply("Successfully logged in!")

    except Exception as e:
        logger.error(f"Login failed: {e}")
        await message.reply(f"Login failed: {e}")

    finally:
        await user_client.disconnect()

# Run the bot
bot.run()
