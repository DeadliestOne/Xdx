import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.channels import LeaveChannelRequest
from colorama import init

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
accounts = {}  # Dictionary to store clients for multiple accounts


@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    """Starts the hosting process for a new account."""
    user_id = event.sender_id
    if user_id in user_states:
        await event.reply("You already have an active process. Please complete it before starting a new one.")
        return

    user_states[user_id] = {'step': 'awaiting_credentials'}
    await event.reply("Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")


@bot.on(events.NewMessage(pattern='/accounts'))
async def list_accounts(event):
    """Lists all hosted accounts."""
    if not accounts:
        await event.reply("No accounts are currently hosted.")
        return

    response = "Hosted Accounts:\n"
    for i, acc in enumerate(accounts.keys(), 1):
        response += f"{i}. {acc}\n"
    await event.reply(response)


@bot.on(events.NewMessage(pattern='/remove'))
async def remove_account(event):
    """Removes an account."""
    user_id = event.sender_id
    account_list = list(accounts.keys())

    if not account_list:
        await event.reply("No accounts to remove.")
        return

    await event.reply("Reply with the number of the account to remove (use /accounts to view them).")
    user_states[user_id] = {'step': 'awaiting_remove_account'}


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
        session_name = f'{CREDENTIALS_FOLDER}/session_{user_id}_{phone_number}'
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
                accounts[phone_number] = client
                await client.disconnect()
                await event.reply(f"Account {phone_number} is already authorized and hosted!")
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
            accounts[phone_number] = client
            await event.reply(f"Account {phone_number} successfully hosted! What would you like to do next?")
            del user_states[user_id]
        except Exception as e:
            await event.reply(f"Error: {e}")
            del user_states[user_id]

    elif state['step'] == 'awaiting_remove_account':
        try:
            index = int(event.text.strip()) - 1
            account_list = list(accounts.keys())
            if 0 <= index < len(account_list):
                removed_account = account_list[index]
                await accounts[removed_account].disconnect()
                del accounts[removed_account]
                await event.reply(f"Account {removed_account} removed successfully.")
                del user_states[user_id]
            else:
                await event.reply("Invalid account number.")
        except ValueError:
            await event.reply("Please provide a valid number.")


@bot.on(events.NewMessage(pattern='/forward'))
async def forward_command(event):
    """Starts the ad forwarding process."""
    if not accounts:
        await event.reply("No accounts are hosted. Use /host to add accounts.")
        return

    await event.reply("How many messages would you like to forward per group (1-5)?")
    user_states[event.sender_id] = {'step': 'awaiting_message_count'}


@bot.on(events.NewMessage)
async def forward_ads_input(event):
    """Processes input for forwarding ads."""
    user_id = event.sender_id

    if user_id not in user_states:
        return

    state = user_states[user_id]

    if state['step'] == 'awaiting_message_count':
        try:
            message_count = int(event.text.strip())
            if message_count < 1 or message_count > 5:
                await event.reply("Please choose a number between 1 and 5.")
                return
            state['message_count'] = message_count
            await event.reply("How many rounds of ads would you like to run?")
            state['step'] = 'awaiting_rounds'
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_rounds':
        try:
            rounds = int(event.text.strip())
            state['rounds'] = rounds
            await event.reply("Enter delay (in seconds) between rounds.")
            state['step'] = 'awaiting_delay'
        except ValueError:
            await event.reply("Please provide a valid number.")

    elif state['step'] == 'awaiting_delay':
        try:
            delay = int(event.text.strip())
            state['delay'] = delay
            await event.reply("Starting ad forwarding process...")
            await forward_ads(state['message_count'], state['rounds'], state['delay'])
            del user_states[user_id]
        except ValueError:
            await event.reply("Please provide a valid number.")


async def forward_ads(message_count, rounds, delay):
    """Forwards ads to all groups for all hosted accounts."""
    for phone_number, client in accounts.items():
        await client.connect()
        saved_messages = await client.get_messages('me', limit=message_count)
        if not saved_messages or len(saved_messages) < message_count:
            print(f"Not enough messages in 'Saved Messages' for account {phone_number}.")
            continue

        for round_num in range(1, rounds + 1):
            print(f"Round {round_num} for account {phone_number}...")
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    group = dialog.entity
                    for message in saved_messages:
                        try:
                            await client.forward_messages(group.id, message)
                            print(f"Ad forwarded to {group.title} from account {phone_number}.")
                        except Exception as e:
                            print(f"Failed to forward to {group.title}: {e}")
                        await asyncio.sleep(1)
            if round_num < rounds:
                await asyncio.sleep(delay)


print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
