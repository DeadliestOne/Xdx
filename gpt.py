import logging
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, PeerIdInvalid

# Bot credentials (replace with your own)
API_ID = 26416419
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_TOKEN = "8031831989:AAH8H2ZuKhMukDZ9cWG2Kgm18hEx835jb48"  # Replace with your bot's token

# Setup logging to suppress unwanted output
logging.basicConfig(level=logging.ERROR)  # Suppress INFO/DEBUG logs
logger = logging.getLogger("pyrogram")
logger.setLevel(logging.ERROR)  # This ensures Pyrogram's logs are suppressed

# Initialize the Pyrogram client (bot)
bot = Client("account_hoster_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Define a state to track user progress (we'll keep this simple)
user_sessions = {}

@bot.on_message(filters.command("start"))
async def start_message(client, message):
    await message.reply("Welcome to the Account Hoster Bot! Please use /setsession to provide your string session.")

@bot.on_message(filters.command("setsession"))
async def set_session(client, message):
    user_id = message.from_user.id
    session_string = message.text.replace("/setsession", "").strip()

    if not session_string:
        await message.reply("Please provide a valid string session.")
        return

    # Initialize the user client using the provided session string
    try:
        user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=session_string)
        await user_client.connect()

        # Save the user client session for future use
        user_sessions[user_id] = {"user_client": user_client, "step": "logged_in"}
        
        await message.reply("Successfully logged in with the provided string session!")

        # Ask for the group links to join
        await message.reply("Please send the group links (separated by commas or newlines) to join:")

    except Exception as e:
        await message.reply(f"Failed to log in with the provided session string: {str(e)}")

@bot.on_message(filters.text)
async def handle_input(client, message):
    user_id = message.from_user.id
    if user_id not in user_sessions:
        return

    step = user_sessions[user_id]["step"]

    # If the user is logged in, proceed to group joining
    if step == "logged_in":
        group_links = message.text.splitlines()  # Split by newlines to handle multi-line input
        group_links = [link.strip() for link in group_links if link.strip()]

        # Ensure we don't exceed 2,000 groups
        if len(group_links) > 2000:
            await message.reply("You can't join more than 2,000 groups at once.")
            return

        for link in group_links:
            # Handle both public group usernames and private invite links
            group_username = None
            try:
                # If the link is a t.me link, extract the group username or invite link
                if "t.me/" in link:
                    if "+" in link:  # Private group invite link
                        invite_link = link
                        await message.reply(f"Attempting to join private group with invite link: {invite_link}")
                        await user_sessions[user_id]["user_client"].join_chat(invite_link)
                    else:  # Public group
                        group_username = link.split("/")[-1]
                        await message.reply(f"Attempting to join public group: @{group_username}")
                        await user_sessions[user_id]["user_client"].join_chat(group_username)
                else:
                    # If it's just a username (e.g., @group)
                    group_username = link
                    await message.reply(f"Attempting to join public group: @{group_username}")
                    await user_sessions[user_id]["user_client"].join_chat(group_username)
                
                await message.reply(f"Successfully joined: {group_username if group_username else 'private group'}")
            except PeerIdInvalid:
                await message.reply(f"Failed to join {link}: Invalid group or invite link.")
            except Exception as e:
                await message.reply(f"Failed to join {link}: {str(e)}")
        
        # Optionally, you can disconnect after joining the groups
        await user_sessions[user_id]["user_client"].disconnect()
        del user_sessions[user_id]  # Clear session data for this user

# Run the bot
bot.run()
