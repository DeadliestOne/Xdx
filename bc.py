import os
import json
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import LeaveChannelRequest
from colorama import init, Fore

# Initialize colorama for colored output
init(autoreset=True)

# Constants
API_ID = "YOUR_API_ID"  # Replace with your API ID
API_HASH = "YOUR_API_HASH"  # Replace with your API Hash
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token

CREDENTIALS_FOLDER = 'sessions'

# Create a session folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Helper functions
def save_credentials(session_name, credentials):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, 'w') as f:
        json.dump(credentials, f)

def load_credentials(session_name):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

# Initialize the bot client
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Store active processes to prevent multiple handlers
active_processes = {}

# Command: /host
@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    user_id = event.sender_id

    if user_id in active_processes:
        await event.reply("You already have an active process. Please complete it before starting a new one.")
        return

    active_processes[user_id] = True
    try:
        await event.reply("Please send your API ID, API Hash, and phone number in the following format:\n`API_ID|API_HASH|PHONE_NUMBER`", parse_mode='markdown')

        # Wait for user response
        response_event = await bot.wait_for(events.NewMessage(from_users=user_id), timeout=300)
        data = response_event.text.split('|')
        if len(data) != 3:
            await response_event.reply("Invalid format! Please send data as: `API_ID|API_HASH|PHONE_NUMBER`.")
            del active_processes[user_id]
            return

        api_id, api_hash, phone_number = data
        session_name = f'session_{user_id}'
        client = TelegramClient(session_name, api_id, api_hash)

        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            await response_event.reply("OTP sent to your phone. Please reply with the OTP.")

            # Wait for OTP
            otp_event = await bot.wait_for(events.NewMessage(from_users=user_id), timeout=300)
            otp = otp_event.text.strip()
            try:
                await client.sign_in(phone_number, otp)
                save_credentials(session_name, {
                    'api_id': api_id,
                    'api_hash': api_hash,
                    'phone_number': phone_number
                })
                await otp_event.reply("Account successfully hosted!")
            except Exception as e:
                await otp_event.reply(f"Error during login: {e}")
        else:
            await response_event.reply("Account is already authorized!")

        await client.disconnect()
    except asyncio.TimeoutError:
        await event.reply("You took too long to respond. Please start over.")
    except Exception as e:
        await event.reply(f"An error occurred: {e}")
    finally:
        del active_processes[user_id]

# Command: Leave groups
@bot.on(events.NewMessage(pattern='/leave'))
async def leave_groups(event):
    session_name = f'session_{event.sender_id}'
    credentials = load_credentials(session_name)

    if not credentials:
        await event.reply("No session found for your account. Please use /host first.")
        return

    client = TelegramClient(session_name, credentials['api_id'], credentials['api_hash'])
    await client.connect()

    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            try:
                await client(LeaveChannelRequest(dialog.entity))
                print(Fore.GREEN + f"Left group: {dialog.name}")
            except Exception as e:
                print(Fore.RED + f"Failed to leave group {dialog.name}: {e}")

    await client.disconnect()
    await event.reply("Left all groups where applicable.")

# Run the bot
print("Bot is running...")
bot.run_until_disconnected()
