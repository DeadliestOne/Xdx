import asyncio
import re
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded

# Your bot token from BotFather
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"

# API credentials from my.telegram.org
API_ID = 26416419
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"

# Store user session globally
user_client = None

# Bot Client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply("Welcome! Use /host to log in as a user.")

@bot.on_message(filters.command("host"))
async def host(bot, message):
    global user_client
    if user_client:
        await message.reply("A user session is already active!")
        return

    await message.reply("Please send your **phone number** (including country code) in this format: `+123456789`")
    
    # Wait for the user's phone number
    phone_msg = await bot.listen(message.chat.id)
    phone_number = phone_msg.text.strip()

    # Initialize Userbot Session
    user_client = Client("userbot", api_id=API_ID, api_hash=API_HASH)
    
    await user_client.connect()
    try:
        sent_code = await user_client.send_code(phone_number)
        await message.reply("OTP has been sent. Please enter the **OTP** you received:")
        
        # Wait for OTP
        otp_msg = await bot.listen(message.chat.id)
        otp_code = otp_msg.text.strip()
        
        await user_client.sign_in(phone_number, otp_code)
        await message.reply("✅ Userbot Logged in Successfully!\nNow use /join to add groups.")
    except SessionPasswordNeeded:
        await message.reply("⚠️ Two-Step Verification is enabled! Send your **password**:")
        password_msg = await bot.listen(message.chat.id)
        password = password_msg.text.strip()
        await user_client.check_password(password)
        await message.reply("✅ Userbot Logged in Successfully!\nNow use /join to add groups.")
    except Exception as e:
        await message.reply(f"❌ Login Failed: {e}")
        user_client = None

@bot.on_message(filters.command("join"))
async def join_groups(bot, message):
    global user_client
    if not user_client:
        await message.reply("⚠️ No active user session. Use /host first!")
        return

    await message.reply("Send the **group links** separated by a comma:")

    # Wait for group links
    group_msg = await bot.listen(message.chat.id)
    group_links = [link.strip() for link in group_msg.text.split(",")]

    for link in group_links:
        match = re.search(r"(?:https?://)?t\.me/([\w_]+)", link)
        if match:
            group_username = match.group(1)
        elif link.startswith("@"):
            group_username = link[1:]
        else:
            await message.reply(f"❌ Invalid link format: {link}")
            continue

        try:
            await user_client.join_chat(group_username)
            await message.reply(f"✅ Joined: {group_username}")
        except Exception as e:
            await message.reply(f"❌ Failed to join {group_username}: {e}")

# Run the bot
bot.run()
