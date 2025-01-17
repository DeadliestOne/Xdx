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
API_ID = "26416419"  # Replace with your API ID
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"  # Replace with your API Hash
BOT_TOKEN = "7880833796:AAF6YV4ABd84IrOKk_E3N-oL4Yh5RsN2X00"  # Replace with your bot token

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

# Command: /host
@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    user_id = event.sender_id
    await event.reply("Please send your API ID, API Hash, and phone number in the following format:\n`API_ID|API_HASH|PHONE_NUMBER`", parse_mode='markdown')

    # Wait for user response
    @bot.on(events.NewMessage(from_users=user_id))
    async def process_credentials(response_event):
        try:
            data = response_event.text.split('|')
            if len(data) != 3:
                await response_event.reply("Invalid format! Please send data as: `API_ID|API_HASH|PHONE_NUMBER`.")
                return

            api_id, api_hash, phone_number = data
            session_name = f'session_{user_id}'
            client = TelegramClient(session_name, api_id, api_hash)

            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                await response_event.reply("OTP sent to your phone. Please reply with the OTP.")

                # Wait for OTP
                @bot.on(events.NewMessage(from_users=user_id))
                async def process_otp(otp_event):
                    try:
                        otp = otp_event.text.strip()
                        await client.sign_in(phone_number, otp)
                        save_credentials(session_name, {
                            'api_id': api_id,
                            'api_hash': api_hash,
                            'phone_number': phone_number
                        })
                        await otp_event.reply("Account successfully hosted!")
                        await client.disconnect()
                    except Exception as e:
                        await otp_event.reply(f"Error during login: {e}")
                        await client.disconnect()

            else:
                await response_event.reply("Account is already authorized!")
                await client.disconnect()

        except Exception as e:
            await response_event.reply(f"Error: {e}")

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
