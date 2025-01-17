import os
import json
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import LeaveChannelRequest
from colorama import init, Fore
import time

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your own API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "7226701592:AAEqPN7bjyECFSucMld7JMtaQ5hC_nCY_JQ"

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
            await event.reply("How many rounds of ads would you like to run?")
            state['step'] = 'awaiting_rounds'
        elif choice == '2':
            await leave_groups(state['client'])
            await event.reply("Left all groups.")
            del user_states[user_id]
        else:
            await event.reply("Invalid choice. Reply with 1 or 2.")

    elif state['step'] == 'awaiting_rounds':
        try:
            rounds = int(event.text.strip())
            state['rounds'] = rounds
        
