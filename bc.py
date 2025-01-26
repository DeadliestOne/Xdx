import os
import asyncio
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from colorama import init
import random

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "7226701592:AAFl69s6ea_yi24FrXpVN8FmznwCM7-alao"

CREDENTIALS_FOLDER = 'sessions'

# Create sessions folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Initialize Telegram bot
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# Define the bot owner and allowed users
OWNER_ID = 6748827895  # Replace with the owner user ID
ALLOWED_USERS = set([OWNER_ID])  # Initially allow only the owner

# User states to track ongoing processes
user_states = {}
accounts = {}  # Hosted accounts

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Welcome message for users."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this bot.")
        return
    
    await event.reply("Welcome! Use the following commands:\n\n"
                      "/host - Host a new Telegram account\n"
                      "/forward - Start forwarding ads\n"
                      "/accounts - List hosted accounts\n"
                      "/remove - Remove a hosted account\n"
                      "/add {user_id} - Add a user to the allowed list (owner only)")

# /add command: Adds a user to the allowed users list (owner only)
@bot.on(events.NewMessage(pattern='/add'))
async def add_command(event):
    """Adds a user to the allowed list."""
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("You are not authorized to use this command.")
        return

    # Get the user ID from the message
    user_input = event.text.split()
    if len(user_input) != 2:
        await event.reply("Usage: /add {user_id}")
        return

    new_user_id = int(user_input[1])
    ALLOWED_USERS.add(new_user_id)
    await event.reply(f"User {new_user_id} added to the allowed list.")

# /host command: Starts the hosting process for a new account
@bot.on(events.NewMessage(pattern='/host|/addaccount'))
async def host_command(event):
    """Starts the hosting process for a new account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    if user_id in user_states:
        if user_states[user_id].get('step') in ['awaiting_credentials', 'awaiting_otp']:
            await event.reply("You already have an active process. Please complete it before starting a new one.")
        else:
            del user_states[user_id]  # Remove any old process state
            await event.reply("You can start hosting a new account now.")
    else:
        user_states[user_id] = {'step': 'awaiting_credentials'}
        await event.reply("Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")

# /forward command: Starts the ad forwarding process
@bot.on(events.NewMessage(pattern='/forward'))
async def forward_command(event):
    """Starts the ad forwarding process."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("You are not authorized to use this command.")
        return

    if user_id in user_states:
        await event.reply("You already have an active process. Please complete it before starting a new one.")
        return

    if not accounts:
        await event.reply("No accounts are hosted. Use /host or /addaccount to add accounts.")
        return

    # Display list of hosted accounts
    account_list = '\n'.join([f"{i+1}. {phone}" for i, phone in enumerate(accounts.keys())])
    await event.reply(f"Choose an account to forward ads from:\n{account_list}\nReply with the number of the account.")

    user_states[user_id] = {'step': 'awaiting_account_choice'}

@bot.on(events.NewMessage)
async def process_input(event):
    """Processes user input for account hosting or forwarding."""
    user_id = event.sender_id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    # Handling user credentials for hosting a new account
    if state['step'] == 'awaiting_credentials':
        data = event.text.split('|')
        if len(data) != 3:
            await event.reply("Invalid format. Please send data as:\n`API_ID|API_HASH|PHONE_NUMBER`")
            return

        api_id, api_hash, phone_number = data
        session_name = f"{CREDENTIALS_FOLDER}/session_{user_id}_{phone_number}"
        client = TelegramClient(session_name, api_id, api_hash)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                state.update({'step': 'awaiting_otp', 'client': client, 'phone_number': phone_number})
                await event.reply("OTP sent to your phone. Reply with the OTP.")
            else:
                accounts[phone_number] = client
                await client.disconnect()
                await event.reply(f"Account {phone_number} is already authorized and hosted!")
                del user_states[user_id]  # Clear user state after completing hosting

                # Ask for the next account info
                await event.reply("Send the next account's details in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")

        except Exception as e:
            await event.reply(f"Error: {e}")
            del user_states[user_id]  # Clear user state if error occurs

    # OTP Verification
    elif state['step'] == 'awaiting_otp':
        otp = event.text.strip()
        client = state['client']
        phone_number = state['phone_number']

        try:
            await client.sign_in(phone_number, otp)
            accounts[phone_number] = client
            await event.reply(f"Account {phone_number} successfully hosted! Use /forward to start forwarding ads.")
            del user_states[user_id]  # Clear user state after OTP verification

            # Ask for the next account info
            await event.reply("Send the next account's details in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")
        except Exception as e:
            await event.reply(f"Error: {e}")
            del user_states[user_id]  # Clear user state if error occurs

    # Handling forwarding process steps (account choice, message count, rounds, delay)
    if state['step'] == 'awaiting_account_choice':
        try:
            account_choice = int(event.text.strip()) - 1
            if 0 <= account_choice < len(accounts):
                selected_account = list(accounts.keys())[account_choice]
                state['selected_account'] = selected_account
                state['step'] = 'awaiting_message_count'
                await event.reply(f"Selected account {selected_account}. How many messages would you like to forward per group (1-5)?")
            else:
                await event.reply("Please choose a valid account number.")
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_message_count':
        try:
            message_count = int(event.text.strip())
            if 1 <= message_count <= 5:
                state['message_count'] = message_count
                state['step'] = 'awaiting_rounds'
                await event.reply("How many rounds of ads would you like to run?")
            else:
                await event.reply("Please choose a number between 1 and 5.")
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_rounds':
        try:
            rounds = int(event.text.strip())
            state['rounds'] = rounds
            state['step'] = 'awaiting_delay'
            await event.reply("Enter delay (in seconds) between rounds.")
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_delay':
        try:
            delay = int(event.text.strip())
            state['delay'] = delay
            await event.reply("Starting the ad forwarding process...")
            await forward_ads(state['message_count'], state['rounds'], state['delay'], state['selected_account'])
            del user_states[user_id]  # Clear user state after completing forwarding
        except ValueError:
            await event.reply("Please provide a valid number.")

async def forward_ads(message_count, rounds, delay, selected_account):
    """Forwards ads to all groups for the selected account."""
    client = accounts[selected_account]
    await client.connect()
    saved_messages = await client.get_messages('me', limit=message_count)
    if not saved_messages or len(saved_messages) < message_count:
        print(f"Not enough messages in 'Saved Messages' for account {selected_account}.")
        return

    for round_num in range(1, rounds + 1):
        print(f"Round {round_num} for account {selected_account}...")
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group = dialog.entity
                for message in saved_messages:
                    try:
                        await client.forward_messages(group.id, message)
                        print(f"Ad forwarded to {group.title} from account {selected_account}.")
                        # Random delay between messages
                        await asyncio.sleep(random.uniform(2, 4))
                    except FloodWaitError as e:
                        print(f"Rate limited. Waiting for {e.seconds} seconds.")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        print(f"Failed to forward to {group.title}: {e}")
        if round_num < rounds:
            print(f"Waiting {delay} seconds before the next round...")
            await asyncio.sleep(delay)

# Run the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
