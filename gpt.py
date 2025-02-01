import logging
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded

# Bot credentials (replace with your own)
API_ID = 26416419
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"  # Replace with your bot's token

# Setup logging to suppress unwanted output
logging.basicConfig(level=logging.ERROR)  # Suppress INFO/DEBUG logs

# Initialize the Pyrogram client (bot)
bot = Client("account_hoster_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Define a state to track user progress (we'll keep this simple)
user_sessions = {}

@bot.on_message(filters.command("start"))
async def start_message(client, message):
    await message.reply("Welcome to the Account Hoster Bot! Please use /host to begin the login process.")

@bot.on_message(filters.command("host"))
async def host_account(client, message):
    user_id = message.from_user.id
    if user_id in user_sessions:
        await message.reply("You already have an active session!")
        return

    # Start the hosting process
    user_sessions[user_id] = {"step": "waiting_for_phone"}
    await message.reply("Please send your phone number (with country code):")

@bot.on_message(filters.text)
async def handle_input(client, message):
    user_id = message.from_user.id
    if user_id not in user_sessions:
        return

    step = user_sessions[user_id]["step"]

    # Step 1: Get phone number
    if step == "waiting_for_phone":
        user_sessions[user_id]["phone"] = message.text.strip()
        user_sessions[user_id]["step"] = "waiting_for_api_id"
        await message.reply("Please send your API ID:")

    # Step 2: Get API ID
    elif step == "waiting_for_api_id":
        try:
            user_sessions[user_id]["api_id"] = int(message.text.strip())
            user_sessions[user_id]["step"] = "waiting_for_api_hash"
            await message.reply("Please send your API Hash:")
        except ValueError:
            await message.reply("Invalid API ID! Please send a valid API ID:")

    # Step 3: Get API Hash
    elif step == "waiting_for_api_hash":
        user_sessions[user_id]["api_hash"] = message.text.strip()
        user_sessions[user_id]["step"] = "waiting_for_otp"
        await message.reply("Thank you! Now, I will send an OTP to your phone number. Please wait...")

        # Initialize the user client for login
        phone = user_sessions[user_id]["phone"]
        api_id = user_sessions[user_id]["api_id"]
        api_hash = user_sessions[user_id]["api_hash"]

        user_client = Client("user_session", api_id=api_id, api_hash=api_hash)
        await user_client.connect()

        try:
            # Send OTP request
            await user_client.send_code_request(phone)
            user_sessions[user_id]["user_client"] = user_client
            user_sessions[user_id]["step"] = "waiting_for_otp"
            await message.reply("OTP sent! Please enter the OTP you received:")

        except Exception as e:
            await message.reply(f"Error sending OTP: {str(e)}")
            del user_sessions[user_id]
            await user_client.disconnect()

    # Step 4: Get OTP and log in
    elif step == "waiting_for_otp":
        otp = message.text.strip()
        user_client = user_sessions[user_id].get("user_client")

        try:
            # Log in using OTP
            await user_client.sign_in(phone, otp)
            await message.reply("Successfully logged in!")
            del user_sessions[user_id]
            await user_client.disconnect()

        except SessionPasswordNeeded:
            await message.reply("Two-step verification enabled. Please enter your password:")
            user_sessions[user_id]["step"] = "waiting_for_password"
        except Exception as e:
            await message.reply(f"Login failed: {str(e)}")
            del user_sessions[user_id]
            await user_client.disconnect()

    # Step 5: Handle password if 2FA is enabled
    elif step == "waiting_for_password":
        password = message.text.strip()
        user_client = user_sessions[user_id].get("user_client")

        try:
            await user_client.sign_in(password=password)
            await message.reply("Successfully logged in after password verification!")
            del user_sessions[user_id]
            await user_client.disconnect()
        except Exception as e:
            await message.reply(f"Password verification failed: {str(e)}")
            del user_sessions[user_id]
            await user_client.disconnect()

# Run the bot
bot.run()
