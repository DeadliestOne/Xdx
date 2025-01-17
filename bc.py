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
BOT_TOKEN = "7226701592:AAEqPN7bjyECFSucMld7JMtaQ5hC_nCY_JQ"  # Replace with your bot token

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
            # Ask the user what they want to do
            await event.reply("What would you like to do next?\n1. Run ads in groups\n2. Leave groups\nPlease reply with 1 or 2.")
            state.update({'step': 'choose_action'})
        except Exception as e:
            await event.reply(f"Error during login with OTP: {e}")
        finally:
            del user_states[user_id]

    elif state['step'] == 'choose_action':
        choice = event.text.strip()
        if choice == '1':
            state['action'] = 'run_ads'
            await event.reply("How many rounds of ads would you like to run? Please provide a number.")
            state['step'] = 'awaiting_rounds'
        elif choice == '2':
            state['action'] = 'leave_groups'
            await event.reply("I will now proceed to leave groups.")
            await leave_unwanted_groups(state['client'])
            del user_states[user_id]
        else:
            await event.reply("Invalid choice! Please reply with 1 to run ads or 2 to leave groups.")

    elif state['step'] == 'awaiting_rounds':
        try:
            rounds = int(event.text.strip())
            state['rounds'] = rounds
            await event.reply("How many times would you like to forward the ad to each group per round? Please provide a number.")
            state['step'] = 'awaiting_forward_count'
        except ValueError:
            await event.reply("Please enter a valid number for rounds.")

    elif state['step'] == 'awaiting_forward_count':
        try:
            forward_count = int(event.text.strip())
            state['forward_count'] = forward_count
            await event.reply("What delay (in seconds) would you like between each round of ads?")
            state['step'] = 'awaiting_delay'
        except ValueError:
            await event.reply("Please enter a valid number for forward count.")

    elif state['step'] == 'awaiting_delay':
        try:
            delay = int(event.text.strip())
            state['delay'] = delay
            await event.reply(f"Starting to run ads in {state['rounds']} rounds, forwarding {state['forward_count']} times per group, with {state['delay']} seconds delay between each round.")
            await run_ads_in_groups(state['client'], state['rounds'], state['forward_count'], state['delay'])
            del user_states[user_id]
        except ValueError:
            await event.reply("Please enter a valid number for delay.")

async def run_ads_in_groups(client, rounds, forward_count, delay):
    # Select the message to forward (e.g., a message in 'Saved Messages')
    saved_messages_peer = await client.get_input_entity('me')
    history = await client.get_messages(saved_messages_peer, limit=1)

    if not history:
        print("No messages found in 'Saved Messages' to forward.")
        return

    ad_message = history[0]

    for round_num in range(1, rounds + 1):
        print(f"Starting round {round_num}...")
        # Loop through the user's groups and forward the ad multiple times
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group = dialog.entity
                for _ in range(forward_count):
                    try:
                        # Forward the message to the group
                        await client.forward_messages(group.id, ad_message)
                        print(Fore.GREEN + f"Ad forwarded to {group.title}")
                    except Exception as e:
                        print(Fore.RED + f"Failed to forward ad to {group.title}: {str(e)}")
                    await asyncio.sleep(1)  # Delay between forwards to avoid spam
        if round_num < rounds:
            print(f"Delaying for {delay} seconds before the next round.")
            await asyncio.sleep(delay)

async def leave_unwanted_groups(client):
    # Loop through the user's groups and leave groups
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group = dialog.entity
            try:
                await client.send_message(group.id, "Leaving this group.")
                await client(LeaveChannelRequest(group))
                print(Fore.YELLOW + f"Left group {group.title}")
            except Exception as e:
                print(Fore.RED + f"Failed to leave group {group.title}: {str(e)}")
            await asyncio.sleep(2)  # Delay to avoid rapid actions

# Run the bot
print("Bot is running...")
bot.run_until_disconnected()
