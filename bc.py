from telethon import TelegramClient, events
from telethon.tl.types import InputPeerUser, InputPeerChannel
import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.getenv('API_ID' ,'26416419')
API_HASH = os.getenv('API_HASH' ,'c109c77f5823c847b1aeb7fbd4990cc4')
BOT_TOKEN = os.getenv('BOT_TOKEN' ,'7271656197:AAEakRafQypDQ6nYms0MCZSC3iNFntfNw3k')

# Initialize the client
client = TelegramClient('auto_broadcast_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Store user and group IDs
users = set()
groups = set()

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    users.add(event.sender_id)
    await event.reply("Welcome! You'll now receive broadcast messages.")

@client.on(events.ChatAction)
async def chat_handler(event):
    if event.user_added and event.user.id == client.get_me().id:
        groups.add(event.chat_id)
        await event.reply("Thanks for adding me! I'll send broadcast messages here.")

async def broadcast_message(message):
    for user_id in users:
        try:
            await client.send_message(user_id, message)
            logger.info(f"Message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {str(e)}")
        await asyncio.sleep(1)  # Delay to avoid flooding

    for group_id in groups:
        try:
            await client.send_message(group_id, message)
            logger.info(f"Message sent to group {group_id}")
        except Exception as e:
            logger.error(f"Failed to send message to group {group_id}: {str(e)}")
        await asyncio.sleep(1)  # Delay to avoid flooding

@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
    if event.sender_id != int(os.getenv('ADMIN_ID')):
        await event.reply("You are not authorized to use this command.")
        return

    message = event.text.split('/broadcast ', 1)[1]
    await event.reply("Broadcasting message...")
    await broadcast_message(message)
    await event.reply("Broadcast completed.")

async def main():
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
