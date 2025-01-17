import os
import json
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from colorama import init, Fore

# Initialize colorama for colored output
init(autoreset=True)

# Constants
API_ID = "29305828"  # Replace with your API ID
API_HASH = "583601896f93cf2c75a076c124f7b255"  # Replace with your API Hash
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

# Temporary storage for user inputs
user_states = {}

# Command: /host
@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    user_id = event.sender_id

    if user_id in user_states:
        await event.reply("You already have an active process. Please complete it before starting a new one.")
        return

    user_states[user_id] = {'step': 'awaiting_credentials'}
    await event.reply("Please send your API ID, API Hash, and phone number in the following format:\n`API_ID|API_HASH|PHONE_NUMBER`", parse_mode='markdown')

@bot.on(events.NewMessage)
async def process_user_input(event):
    user_id = event.sender_id

    if user_id not in user_states:
        return  # Ignore messages from users who are not in the process

    state = user_states[user_id]

    if state['step'] == 'awaiting_credentials':
        data = event.text.split('|')
        if len(data) != 3:
            await event.reply("Invalid format! Please send data as: `API_ID|API_HASH|PHONE_NUMBER`.")
            return

        api_id, api_hash, phone_number = data
        session_name = f'session_{user_id}'
        client = TelegramClient(session_name, api_id, api_hash)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                state.update({
                    'step': 'awaiting_otp',
                    'client': client,
                    'phone_number': phone_number,
                    'session_name': session_name,
                    'api_id': api_id,
                    'api_hash': api_hash,
                })
                await event.reply("OTP sent to your phone. Please reply with the OTP.")
            else:
                await client.disconnect()
                await event.reply("Account is already authorized!")
                del user_states[user_id]
        except Exception as e:
            await event.reply(f"Error during login: {e}")
            del user_states[user_id]

    elif state['step'] == 'awaiting_otp':
        otp = event.text.strip()
        client = state['client']
        phone_number = state['phone_number']
        session_name = state['session_name']

        try:
            await client.sign_in(phone_number, otp)
            save_credentials(session_name, {
                'api_id': state['api_id'],
                'api_hash': state['api_hash'],
                'phone_number': phone_number,
            })
            await event.reply("Account successfully hosted!")
            # Start forwarding ads to groups
            await forward_ads_to_groups(client)
            await client.disconnect()
        except Exception as e:
            await event.reply(f"Error during login with OTP: {e}")
        finally:
            del user_states[user_id]

async def forward_ads_to_groups(client):
    # Select the message to forward (e.g., a message in 'Saved Messages')
    saved_messages_peer = await client.get_input_entity('me')
    history = await client.get_messages(saved_messages_peer, limit=1)

    if not history:
        print("No messages found in 'Saved Messages' to forward.")
        return

    ad_message = history[0]

    # Loop through the user's groups and forward the ad
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group = dialog.entity
            try:
                # Forward the message to the group
                await client.forward_messages(group.id, ad_message)
                print(Fore.GREEN + f"Ad forwarded to {group.title}")
            except Exception as e:
                print(Fore.RED + f"Failed to forward ad to {group.title}: {str(e)}")
            await asyncio.sleep(2)  # Delay to avoid spam

# Run the bot
print("Bot is running...")
bot.run_until_disconnected()
