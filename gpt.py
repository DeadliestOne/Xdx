import re
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, FloodWait

# Enable logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your credentials
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"

# API credentials from my.telegram.org
API_ID = 26416419
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"# Replace with your API Hash

# Global variable for user session
user_client = None

# Bot client (this is your bot that listens for commands)
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def wait_for_reply(client, chat_id, timeout=60):
    """
    Waits for a reply message from the user in a chat and returns it.
    """
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    async def handler(_client, message):
        if message.chat.id == chat_id:
            future.set_result(message)

    # Attach handler for message listening
    client.add_handler(filters.chat(chat_id), handler)
    
    try:
        message = await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        client.remove_handler(handler)
        raise Exception("❌ Timed out waiting for a response.")
    
    client.remove_handler(handler)
    return message


@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("👋 Welcome! Use /host to log in as a user.")


@bot.on_message(filters.command("host"))
async def host(client, message):
    global user_client
    if user_client:
        await message.reply("⚠️ A user session is already active!")
        return

    # Ask for the phone number
    await message.reply("📱 Enter your **phone number** (with country code, e.g., +123456789):")
    
    try:
        phone_msg = await wait_for_reply(bot, message.chat.id)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        return

    phone_number = phone_msg.text.strip()
    logger.info(f"Received phone number: {phone_number}")

    # Initialize the userbot session
    user_client = Client("userbot", api_id=API_ID, api_hash=API_HASH)
    await user_client.connect()

    try:
        logger.info("Connected to Telegram, sending OTP...")
        sent_code = await user_client.send_code(phone_number)
        logger.info(f"OTP Sent! Phone Code Hash: {sent_code.phone_code_hash}")

        await message.reply("🔑 OTP has been sent! Please enter the **OTP** you received:")

        try:
            otp_msg = await wait_for_reply(bot, message.chat.id)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
            return

        otp_code = otp_msg.text.strip()
        logger.info(f"Received OTP: {otp_code}")

        # Log in with the phone code
        await user_client.sign_in(phone_number, otp_code, phone_code_hash=sent_code.phone_code_hash)
        await message.reply("✅ Userbot logged in successfully!\nNow use /join to add groups.")
    except SessionPasswordNeeded:
        await message.reply("⚠️ Two-Step Verification is enabled! Send your **password**:")
        try:
            password_msg = await wait_for_reply(bot, message.chat.id)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
            return
        password = password_msg.text.strip()
        await user_client.check_password(password)
        await message.reply("✅ Userbot logged in successfully!\nNow use /join to add groups.")
    except FloodWait as e:
        await message.reply(f"🚨 Flood wait triggered! Try again after {e.value} seconds.")
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
        group_msg = await wait_for_reply(bot, message.chat.id)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        return

    # Split input into individual links
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


# Start the bot
bot.run()
