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

    # Step 1: Ask for the phone number
    phone_number = await bot.ask(message.chat.id, "📱 Enter your **phone number** (with country code, e.g., +123456789):")
    
    # Initialize Userbot Session
    user_client = Client("userbot", api_id=API_ID, api_hash=API_HASH)
    
    await user_client.connect()
    try:
        sent_code = await user_client.send_code(phone_number.text.strip())
        otp_code = await bot.ask(message.chat.id, "🔑 OTP has been sent! Please enter the **OTP** you received:")

        await user_client.sign_in(phone_number.text.strip(), otp_code.text.strip())
        await message.reply("✅ Userbot Logged in Successfully!\nNow use /join to add groups.")
    except SessionPasswordNeeded:
        password_msg = await bot.ask(message.chat.id, "⚠️ Two-Step Verification is enabled! Send your **password**:")
        await user_client.check_password(password_msg.text.strip())
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

    # Ask for group links
    group_msg = await bot.ask(message.chat.id, "🔗 Send the **group links** separated by commas:")

    # Process each link
    group_links = [link.strip() for link in group_msg.text.split(",")]

    for link in group_links:
        match = re.search(r"(?:https?://)?t\.me/([\w_]+)", link)
        group_username = match.group(1) if match else (link[1:] if link.startswith("@") else None)

        if group_username:
            try:
                await user_client.join_chat(group_username)
                await message.reply(f"✅ Joined: {group_username}")
            except Exception as e:
                await message.reply(f"❌ Failed to join {group_username}: {e}")
        else:
            await message.reply(f"❌ Invalid link format: {link}")

# Run the bot
bot.run()
