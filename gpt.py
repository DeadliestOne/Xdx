import re
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, FloodWait

# Logging Setup (for Debugging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Credentials (Replace with your actual values)
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"

# API credentials from my.telegram.org
API_ID = 26416419
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4" Replace with your actual API HASH

# Global variable to store the user session
user_client = None

# Initialize the bot
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("👋 Welcome! Use /host to log in as a user.")

@bot.on_message(filters.command("host"))
async def host(client, message):
    global user_client
    if user_client:
        await message.reply("⚠️ A user session is already active!")
        return

    await message.reply("📱 Enter your **phone number** (with country code, e.g., +123456789):")

    try:
        phone_msg = await bot.listen(message.chat.id)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        return

    phone_number = phone_msg.text.strip()
    logger.info(f"Received phone number: {phone_number}")

    # Initialize the user session
    user_client = Client("userbot", api_id=API_ID, api_hash=API_HASH)
    await user_client.connect()

    try:
        logger.info("Sending OTP...")
        sent_code = await user_client.send_code(phone_number)
        await message.reply("🔑 OTP sent! Please enter the **OTP**:")

        try:
            otp_msg = await bot.listen(message.chat.id)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
            return

        otp_code = otp_msg.text.strip()
        logger.info(f"Received OTP: {otp_code}")

        # Sign in with OTP
        await user_client.sign_in(phone_number, otp_code, phone_code_hash=sent_code.phone_code_hash)
        await message.reply("✅ Userbot logged in successfully! Now use /join to add groups.")
    except SessionPasswordNeeded:
        await message.reply("⚠️ Two-Step Verification detected! Enter your **password**:")
        try:
            password_msg = await bot.listen(message.chat.id)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
            return

        password = password_msg.text.strip()
        await user_client.check_password(password)
        await message.reply("✅ Userbot logged in successfully!")
    except FloodWait as e:
        await message.reply(f"🚨 Too many login attempts! Wait {e.value} seconds before retrying.")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        await message.reply(f"❌ Login Failed: {e}")
        user_client = None

@bot.on_message(filters.command("join"))
async def join_groups(client, message):
    global user_client
    if not user_client:
        await message.reply("⚠️ No active user session. Use /host first!")
        return

    await message.reply("🔗 Send the **group links** separated by commas:")
    try:
        group_msg = await bot.listen(message.chat.id)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        return

    # Extract links
    group_links = [link.strip() for link in group_msg.text.split(",")]

    for link in group_links:
        match = re.search(r"(?:https?://)?t\.me/([\w_]+)", link)
        if match:
            group_username = match.group(1)
        elif link.startswith("@"):
            group_username = link[1:]
        else:
            group_username = None

        if group_username:
            try:
                await user_client.join_chat(group_username)
                await message.reply(f"✅ Joined: {group_username}")
            except Exception as e:
                await message.reply(f"❌ Failed to join {group_username}: {e}")
        else:
            await message.reply(f"❌ Invalid link format: {link}")

bot.run()
