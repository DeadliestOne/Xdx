import os
import json
import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.channels import LeaveChannelRequest
from colorama import init, Fore
import time

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your own API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "7226701592:AAHSQb_ceVqps81-DhXfyakVg4D0Jpp_3Og"

CREDENTIALS_FOLDER = 'sessions'

# Create sessions folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Initialize Telegram bot
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# User states to track ongoing processes
user_states = {}

@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    """Handles the hosting process."""
    user_id = event.sender_id
    if user_id in user_states:
        await event.reply("You already have an active process. Please complete it before starting a new one.")
        return

    user_states[user_id] = {'step': 'awaiting_credentials'}
    await event.reply("Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")

@bot.on(events.NewMessage)
async def process_input(event):
    """Processes user input and steps."""
    user_id = event.sender_id

    if user_id not in user_states:
        return

    state = user_states[user_id]

    if state['step'] == 'awaiting_credentials':
        data = event.text.split('|')
        if len(data) != 3:
            await event.reply("Invalid format. Please send data as:\n`API_ID|API_HASH|PHONE_NUMBER`")
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
                })
                await event.reply("OTP sent to your phone. Reply with the OTP.")
            else:
                await client.disconnect()
                await event.reply("Account is already authorized!")
                del user_states[user_id]
        except Exception as e:
            await event.reply(f"Error: {e}")
            del user_states[user_id]

    elif state['step'] == 'awaiting_otp':
        otp = event.text.strip()
        client = state['client']
        phone_number = state['phone_number']

        try:
            await client.sign_in(phone_number, otp)
            await event.reply("Account successfully hosted! What would you like to do next?\n1. Forward ads to groups\n2. Leave groups\nReply with 1 or 2.")
            state['step'] = 'choose_action'
        except Exception as e:
            await event.reply(f"Error: {e}")
            del user_states[user_id]

    elif state['step'] == 'choose_action':
        choice = event.text.strip()
        if choice == '1':
            await event.reply("Do you want to forward 1 or 2 messages? Reply with 1 or 2.")
            state['step'] = 'awaiting_message_count'
        elif choice == '2':
            try:
                await leave_groups(state['client'])
                await event.reply("Left all groups.")
                del user_states[user_id]
            except Exception as e:
                await event.reply(f"Error: {e}")
        else:
            await event.reply("Invalid choice. Reply with 1 or 2.")

    elif state['step'] == 'awaiting_message_count':
        message_count = event.text.strip()
        if message_count not in ['1', '2']:
            await event.reply("Invalid input. Please reply with 1 or 2.")
            return
        state['message_count'] = int(message_count)
        await event.reply("How many rounds of ads would you like to run?")
        state['step'] = 'awaiting_rounds'

    elif state['step'] == 'awaiting_rounds':
        try:
            rounds = int(event.text.strip())
            state['rounds'] = rounds
            await event.reply("How many messages to forward per group per round?")
            state['step'] = 'awaiting_forward_count'
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_forward_count':
        try:
            forward_count = int(event.text.strip())
            state['forward_count'] = forward_count
            await event.reply("Enter delay (in seconds) between rounds.")
            state['step'] = 'awaiting_delay'
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_delay':
        try:
            delay = int(event.text.strip())
            state['delay'] = delay
            await event.reply("Starting ad forwarding process... One More Thing This Is A Script Which Was Maded By @UncountableAura For 10$ Only")
            await forward_ads(state['client'], state['message_count'], state['rounds'], state['forward_count'], state['delay'])
            del user_states[user_id]
        except ValueError:
            await event.reply("Please provide a valid number.")

async def forward_ads(client, message_count, rounds, forward_count, delay):
    """Forwards ads to all groups."""
    await client.connect()
    saved_messages = await client.get_messages('me', limit=message_count)
    if not saved_messages or len(saved_messages) < message_count:
        print("Not enough messages in 'Saved Messages'.")
        return

    for round_num in range(1, rounds + 1):
        print(f"Round {round_num}...")
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group = dialog.entity
                for message in saved_messages:
                    for _ in range(forward_count):
                        try:
                            await client.forward_messages(group.id, message)
                            print(f"Ad forwarded to {group.title}")
                        except Exception as e:
                            print(f"Failed to forward to {group.title}: {e}")
                        await asyncio.sleep(1)
        if round_num < rounds:
            await asyncio.sleep(delay)

async def leave_groups(client):
    """Leaves all groups."""
    await client.connect()
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            try:
                await client(LeaveChannelRequest(dialog.entity))
                print(f"Left group {dialog.name}")
            except Exception as e:
                print(f"Failed to leave {dialog.name}: {e}")

print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
