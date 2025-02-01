import logging
from pyrogram import Client, filters

# Bot credentials
API_ID = "26416419"
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"

# Setup logging for debugging
logging.basicConfig(level=logging.INFO)

# Initialize the bot client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# /start command for the bot
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Welcome! Please send your string session to login.")

# /setsession command to set the string session and log in
@bot.on_message(filters.command("setsession"))
async def set_session(client, message):
    string_session = message.text.replace("/setsession", "").strip()

    if not string_session:
        await message.reply("Please provide a valid string session.")
        return

    # Try logging in with the provided string session
    user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=string_session)

    try:
        await user_client.connect()
        await message.reply("Successfully logged in with the provided string session!")

        # After successful login, ask for group links
        await message.reply("Now, please send the group links (separated by commas) to join:")

        # Wait for group links input
        group_msg = await bot.listen(message.chat.id)
        group_links = [link.strip() for link in group_msg.text.split(",")]

        for link in group_links:
            group_username = link.split("/")[-1] if "t.me" in link else link.strip("@")
            try:
                # Try joining the group using the string session
                await user_client.join_chat(group_username)
                await message.reply(f"Successfully joined: {group_username}")
            except Exception as e:
                await message.reply(f"Failed to join {group_username}: {e}")

        # Disconnect the user client after finishing
        await user_client.disconnect()

    except Exception as e:
        await message.reply(f"Login failed: {e}")
        return

# Run the bot
bot.run()
