import os
import json
import psutil
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerUser
from colorama import init, Fore
import pyfiglet

# Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN"
API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
SESSIONS_FOLDER = "sessions"

# Initialize colorama for colored output
init(autoreset=True)

# Ensure sessions folder exists
if not os.path.exists(SESSIONS_FOLDER):
    os.mkdir(SESSIONS_FOLDER)

# Initialize the bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# In-memory storage for hosted accounts
hosted_accounts = {}

# Save account credentials
def save_account(session_name, api_id, api_hash, phone_number):
    data = {
        "api_id": api_id,
        "api_hash": api_hash,
        "phone_number": phone_number
    }
    with open(f"{SESSIONS_FOLDER}/{session_name}.json", "w") as f:
        json.dump(data, f)

# Load account credentials
def load_account(session_name):
    try:
        with open(f"{SESSIONS_FOLDER}/{session_name}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# Get server stats
def get_server_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    return f"CPU Usage: {cpu_usage}%\nMemory Usage: {memory_usage}%"

# Function to display banner
def display_banner():
    print(Fore.RED + pyfiglet.figlet_format("LEGITDEALS9"))
    print(Fore.GREEN + "Made by @Legitdeals9\n")

# Command: /host
@bot.on(events.NewMessage(pattern="/host"))
async def host_account(event):
    args = event.raw_text.split()
    if len(args) != 4:
        await event.reply("Usage: /host <session_name> <api_id> <api_hash> <phone_number>")
        return

    session_name, api_id, api_hash, phone_number = args[1], args[2], args[3], args[4]

    if session_name in hosted_accounts:
        await event.reply(f"Session {session_name} is already hosted.")
        return

    client = TelegramClient(f"{SESSIONS_FOLDER}/{session_name}", int(api_id), api_hash)
    try:
        await client.start(phone=phone_number)
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            await event.reply("Enter the code sent to the account:")

            @bot.on(events.NewMessage(from_user=event.sender_id))
            async def handle_code_response(code_event):
                try:
                    await client.sign_in(phone_number, code_event.raw_text)
                    hosted_accounts[session_name] = client
                    save_account(session_name, api_id, api_hash, phone_number)
                    await code_event.reply(f"Account {session_name} hosted successfully!")
                except Exception as e:
                    await code_event.reply(f"Failed to authenticate: {str(e)}")
                finally:
                    bot.remove_event_handler(handle_code_response)

        else:
            hosted_accounts[session_name] = client
            save_account(session_name, api_id, api_hash, phone_number)
            await event.reply(f"Account {session_name} hosted successfully!")
    except Exception as e:
        await event.reply(f"Failed to host account: {str(e)}")

# Command: /remove
@bot.on(events.NewMessage(pattern="/remove"))
async def remove_account(event):
    args = event.raw_text.split()
    if len(args) != 2:
        await event.reply("Usage: /remove <session_name>")
        return

    session_name = args[1]
    if session_name not in hosted_accounts:
        await event.reply(f"Session {session_name} is not hosted.")
        return

    client = hosted_accounts.pop(session_name)
    await client.disconnect()
    os.remove(f"{SESSIONS_FOLDER}/{session_name}.json")
    await event.reply(f"Account {session_name} removed successfully.")

# Command: /accounts
@bot.on(events.NewMessage(pattern="/accounts"))
async def list_accounts(event):
    if not hosted_accounts:
        await event.reply("No accounts are currently hosted.")
    else:
        accounts = "\n".join(hosted_accounts.keys())
        await event.reply(f"Hosted accounts:\n{accounts}")

# Command: /stats
@bot.on(events.NewMessage(pattern="/stats"))
async def server_stats(event):
    stats = get_server_stats()
    await event.reply(f"Server Stats:\n{stats}")

# Command: /forward
@bot.on(events.NewMessage(pattern="/forward"))
async def forward_ads(event):
    args = event.raw_text.split()
    if len(args) != 1:
        await event.reply("Usage: /forward")
        return

    session_name = event.sender_id
    if session_name not in hosted_accounts:
        await event.reply("No hosted session found. Use /host to host a session.")
        return

    client = hosted_accounts[session_name]

    saved_messages_peer = await client.get_input_entity("me")
    history = await client(GetHistoryRequest(
        peer=saved_messages_peer,
        limit=5,  # Fetch up to 5 messages
        offset_id=0,
        offset_date=None,
        add_offset=0,
        max_id=0,
        min_id=0,
        hash=0
    ))

    if not history.messages:
        await event.reply("No messages found in 'Saved Messages'.")
        return

    ads = history.messages[:5]

    repeat_count = int(await event.reply("How many rounds do you want to forward messages?").raw_text)
    delay_between_rounds = int(await event.reply("Enter delay (seconds) between rounds:").raw_text)

    for round_num in range(repeat_count):
        for message in ads:
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    try:
                        await client.forward_messages(dialog.entity, message)
                        await asyncio.sleep(2)  # Small delay between groups
                    except Exception as e:
                        await event.reply(f"Failed to forward message to {dialog.entity.title}: {e}")
        await asyncio.sleep(delay_between_rounds)

    await event.reply("Forwarding completed.")

# Run the bot
print("Bot is running...")
bot.run_until_disconnected()
