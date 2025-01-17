import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors import FloodWaitError
from colorama import init

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "7226701592:AAE7AGWAU0BXgw-PmLfhgarpCT4-2wrBdwE"

CREDENTIALS_FOLDER = 'sessions'

# Create sessions folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Initialize Telegram bot
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# User states to track ongoing processes
user_states = {}
accounts = {}


@bot.on(events.NewMessage(pattern='/forward'))
async def forward_command(event):
    """Starts the ad forwarding process."""
    if not accounts:
        await event.reply("No accounts are hosted. Use /host to add accounts.")
        return

    user_id = event.sender_id
    user_states[user_id] = {'step': 'awaiting_message_count'}
    await event.reply("How many messages would you like to forward per group (1-5)?")


@bot.on(events.NewMessage)
async def process_forward_steps(event):
    """Handles forwarding process steps (message count, rounds, delay)."""
    user_id = event.sender_id

    if user_id not in user_states:
        return

    state = user_states[user_id]

    # Step 1: Message count
    if state['step'] == 'awaiting_message_count':
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

    # Step 2: Rounds
    elif state['step'] == 'awaiting_rounds':
        try:
            rounds = int(event.text.strip())
            state['rounds'] = rounds
            state['step'] = 'awaiting_delay'
            await event.reply("Enter delay (in seconds) between rounds.")
        except ValueError:
            await event.reply("Please provide a valid number.")

    # Step 3: Delay
    elif state['step'] == 'awaiting_delay':
        try:
            delay = int(event.text.strip())
            state['delay'] = delay
            await event.reply("Starting the ad forwarding process...")
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
                            # Add a small random delay between messages
                            await asyncio.sleep(random.uniform(2, 5))
                        except FloodWaitError as e:
                            print(f"Rate limited. Waiting for {e.seconds} seconds.")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            print(f"Failed to forward to {group.title}: {e}")
            if round_num < rounds:
                print(f"Waiting {delay} seconds before the next round...")
                await asyncio.sleep(delay)


print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
