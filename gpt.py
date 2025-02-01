import logging
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

# Store user session globally
user_client = None

# Initialize the bot client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# /host command: Starts the hosting process for a new account
@bot.on_message(filters.command("host"))
async def host_command(client, message: Message):
    """Starts the hosting process for a new account."""
    
    await message.reply("Please enter your **phone number** (with country code):")

    # Wait for the phone number input from the user
    phone_msg = await bot.listen(message.chat.id)
    phone_number = phone_msg.text.strip()
    logger.info(f"Received phone number: {phone_number}")

    global user_client
    user_client = Client("userbot", api_id=API_ID, api_hash=API_HASH)

    # Try to send OTP to the phone number
    try:
        await user_client.connect()
        sent_code = await user_client.send_code(phone_number)
        await message.reply("OTP sent! Please enter the OTP:")

        # Wait for the OTP input from the user
        otp_msg = await bot.listen(message.chat.id)
        otp_code = otp_msg.text.strip()
        logger.info(f"Received OTP: {otp_code}")

        # Try signing in with OTP
        await user_client.sign_in(phone_number, otp_code, phone_code_hash=sent_code.phone_code_hash)
        await message.reply("Successfully logged in!")

    except SessionPasswordNeeded:
        await message.reply("Two-step verification is enabled. Please enter your password:")
        password_msg = await bot.listen(message.chat.id)
        password = password_msg.text.strip()
        await user_client.check_password(password)
        await message.reply("Successfully logged in after password verification!")

    except Exception as e:
        logger.error(f"Login failed: {e}")
        await message.reply(f"Login failed: {e}")
        user_client = None


# Run the bot
bot.run()
