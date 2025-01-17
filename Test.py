import asyncio
import os
import json
from telethon import TelegramClient, errors
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerUser
from colorama import init, Fore
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ParseMode

# Initialize colorama for colored output
init(autoreset=True)

# Bot token from BotFather
BOT_TOKEN = "7880833796:AAF6YV4ABd84IrOKk_E3N-oL4Yh5RsN2X00"

# Telegram API details
CREDENTIALS_FOLDER = 'sessions'
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

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

async def login_and_forward(api_id, api_hash, phone_number, session_name):
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start(phone=phone_number)

    try:
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            await client.sign_in(phone_number)
    except SessionPasswordNeededError:
        password = input("Two-factor authentication enabled. Enter your password: ")
        await client.sign_in(password=password)

    saved_messages_peer = await client.get_input_entity('me')
    history = await client(GetHistoryRequest(
        peer=saved_messages_peer,
        limit=1,
        offset_id=0,
        offset_date=None,
        add_offset=0,
        max_id=0,
        min_id=0,
        hash=0
    ))

    if not history.messages:
        print("No messages found in 'Saved Messages'")
        return

    last_message = history.messages[0]
    for dialog in await client.get_dialogs():
        if dialog.is_group:
            group = dialog.entity
            try:
                await client.forward_messages(group, last_message)
                print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
            except Exception as e:
                print(Fore.RED + f"Failed to forward message to {group.title}: {str(e)}")
            await asyncio.sleep(3)

    await client.disconnect()

@dp.message_handler(commands=['host'])
async def handle_host(message: types.Message):
    await message.reply("Please provide the API ID, API hash, and phone number for the account.\nFormat:\n<code>API_ID|API_HASH|PHONE</code>")

@dp.message_handler(lambda message: "|" in message.text)
async def process_hosting(message: types.Message):
    try:
        credentials = message.text.split("|")
        api_id = int(credentials[0])
        api_hash = credentials[1]
        phone_number = credentials[2]
        session_name = f"session_{phone_number}"

        save_credentials(session_name, {
            'api_id': api_id,
            'api_hash': api_hash,
            'phone_number': phone_number
        })

        await message.reply("Hosting started! The account will now forward ads.")
        asyncio.create_task(login_and_forward(api_id, api_hash, phone_number, session_name))
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

if __name__ == "__main__":
    print(Fore.GREEN + "Bot is running...")
    executor.start_polling(dp, skip_updates=True)
