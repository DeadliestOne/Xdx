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
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4" # Your API hash from my.telegram.org

# Store user session globally
user_client = None

# Initialize the bot client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start command for the bot
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Welcome! Use /host to log in as a user.")

# /host command to login the user
@bot.on_message(filters.command("host"))
async def host(client, message):
    global user_client
    if user_client:
        await message.reply("A user session is already active!")
        return

    await message.reply("Please enter your **phone number** (with country code):")

    # Wait for the phone number input from the user
    phone_msg = await bot.listen(message.chat.id)
    phone_number = phone_msg.text.strip()
    logger.info(f"Received phone number: {phone_number}")

    # Initialize the user session
    user_client = Client("userbot", api_id=API_ID, api_hash=API_HASH)
    await user_client.connect()

    try:
        # Send OTP to the phone number
        logger.info(f"Sending OTP to {phone_number}...")
        sent_code = await user_client.send_code(phone_number)
        await message.reply("OTP sent! Please enter the OTP:")

        # Wait for the OTP input from the user
        otp_msg = await bot.listen(message.chat.id)
        otp_code = otp_msg.text.strip()
        logger.info(f"Received OTP: {otp_code}")

        # Try signing in with OTP
        await user_client.sign_in(phone_number, otp_code, phone_code_hash=sent_code.phone_code_hash)
        await message.reply("Successfully logged in! Now you can use /join to add groups.")
    except SessionPasswordNeeded:
        await message.reply("Two-step verification is enabled. Please enter your password:")
        password_msg = await bot.listen(message.chat.id)
        password = password_msg.text.strip()
        await user_client.check_password(password)
        await message.reply("Successfully logged in after password verification!")
    except FloodWait as e:
        await message.reply(f"Flood wait triggered. Try again after {e.value} seconds.")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        await message.reply(f"Login failed: {e}")
        user_client = None

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
