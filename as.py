import os
import asyncio
from telethon import TelegramClient, events
from pymongo import MongoClient
from telethon.errors import FloodWaitError
import random

# MongoDB configuration
MONGO_URI = "mongodb+srv://jc07cv9k3k:bEWsTrbPgMpSQe2z@cluster0.nfbxb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB URI
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['telegram_bot']
users_collection = db['users']
accounts_collection = db['accounts']

# Bot credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "7226701592:AAE7AGWAU0BXgw-PmLfhgarpCT4-2wrBdwE"

# Owner ID
OWNER_ID = 6748827895  # Replace with your Telegram User ID

# Folder for session files
CREDENTIALS_FOLDER = 'sessions'
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Initialize the bot
bot = TelegramClient('bot_session', USER_API_ID, USER_API_HASH)

# Check if a user is authorized
def is_authorized(user_id):
    if user_id == OWNER_ID:  # Allow owner by default
        return True
    user = users_collection.find_one({"user_id": user_id})
    return user is not None

# Start command
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if not is_authorized(user_id):
        await event.reply("You are not authorized to use this bot.")
        return
    await event.reply("Welcome to the bot! Available commands:\n"
                      "/host - Host a new Telegram account\n"
                      "/accounts - List hosted accounts\n"
                      "/stats - Get bot statistics\n"
                      "/remove - Remove a hosted account\n"
                      "/adduser - Add a user (owner only)\n"
                      "/removeuser - Remove a user (owner only)")

# /host command
@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    user_id = event.sender_id
    if not is_authorized(user_id):
        await event.reply("You are not authorized to use this command.")
        return
    await event.reply("Send your API ID, API Hash, and phone number in the format:\n`API_ID|API_HASH|PHONE_NUMBER`")

@bot.on(events.NewMessage(pattern='/forward'))
async def forward_command(event):
    """Starts the ad forwarding process."""
    user_id = event.sender_id
    if not is_authorized(user_id):
        await event.reply("You are not authorized to use this command.")
        return

    accounts = accounts_collection.find()
    if accounts.count() == 0:
        await event.reply("No accounts are hosted. Use /host to add accounts.")
        return

    await event.reply("How many messages would you like to forward per group (1-5)?")

    @bot.on(events.NewMessage)
    async def process_forward(event):
        try:
            message_count = int(event.text.strip())
            if not 1 <= message_count <= 5:
                await event.reply("Please provide a number between 1 and 5.")
                return

            await event.reply("How many rounds of ads would you like to run?")

            @bot.on(events.NewMessage)
            async def process_rounds(event):
                try:
                    rounds = int(event.text.strip())

                    await event.reply("Enter delay (in seconds) between rounds.")

                    @bot.on(events.NewMessage)
                    async def process_delay(event):
                        try:
                            delay = int(event.text.strip())
                            await event.reply("Starting the ad forwarding process...")

                            for account in accounts:
                                phone_number = account['phone_number']
                                session_name = f"{CREDENTIALS_FOLDER}/session_{phone_number}"
                                client = TelegramClient(session_name, USER_API_ID, USER_API_HASH)

                                try:
                                    await client.connect()
                                    saved_messages = await client.get_messages('me', limit=message_count)

                                    if not saved_messages or len(saved_messages) < message_count:
                                        await event.reply(f"Not enough messages in 'Saved Messages' for account {phone_number}.")
                                        continue

                                    for round_num in range(1, rounds + 1):
                                        await event.reply(f"Starting round {round_num} for account {phone_number}...")
                                        async for dialog in client.iter_dialogs():
                                            if dialog.is_group:
                                                group = dialog.entity
                                                for message in saved_messages:
                                                    try:
                                                        await client.forward_messages(group.id, message)
                                                        await asyncio.sleep(random.uniform(2, 4))
                                                    except FloodWaitError as e:
                                                        await asyncio.sleep(e.seconds)
                                                    except Exception as e:
                                                        print(f"Failed to forward to {group.title}: {e}")
                                        if round_num < rounds:
                                            await asyncio.sleep(delay)

                                    await client.disconnect()

                                except Exception as e:
                                    print(f"Error with account {phone_number}: {e}")

                        except ValueError:
                            await event.reply("Invalid delay value. Please enter a valid number.")
                        except Exception as e:
                            await event.reply(f"An error occurred: {e}")
                except ValueError:
                    await event.reply("Invalid rounds value. Please enter a valid number.")
                except Exception as e:
                    await event.reply(f"An error occurred: {e}")
        except ValueError:
            await event.reply("Invalid message count. Please enter a valid number.")
        except Exception as e:
            await event.reply(f"An error occurred: {e}")
        
    
    @bot.on(events.NewMessage)
    async def process_host(event):
        data = event.text.split('|')
        if len(data) != 3:
            await event.reply("Invalid format. Use: `API_ID|API_HASH|PHONE_NUMBER`")
            return
        api_id, api_hash, phone_number = data
        session_name = f"{CREDENTIALS_FOLDER}/session_{phone_number}"
        client = TelegramClient(session_name, api_id, api_hash)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                await event.reply("OTP sent to your phone. Reply with the OTP.")
                @bot.on(events.NewMessage)
                async def otp_handler(event):
                    otp = event.text.strip()
                    try:
                        await client.sign_in(phone_number, otp)
                        accounts_collection.insert_one({"phone_number": phone_number})
                        await event.reply(f"Account {phone_number} successfully hosted.")
                    except Exception as e:
                        await event.reply(f"Error during OTP verification: {e}")
            else:
                accounts_collection.insert_one({"phone_number": phone_number})
                await event.reply(f"Account {phone_number} is already authorized.")
        except Exception as e:
            await event.reply(f"Error hosting account: {e}")

# /accounts command
@bot.on(events.NewMessage(pattern='/accounts'))
async def accounts_command(event):
    user_id = event.sender_id
    if not is_authorized(user_id):
        await event.reply("You are not authorized to use this command.")
        return
    accounts = accounts_collection.find()
    if accounts.count() == 0:
        await event.reply("No accounts are hosted.")
    else:
        account_list = "\n".join([acc["phone_number"] for acc in accounts])
        await event.reply(f"Hosted accounts:\n{account_list}")

# /stats command
@bot.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    user_id = event.sender_id
    if not is_authorized(user_id):
        await event.reply("You are not authorized to use this command.")
        return
    user_count = users_collection.count_documents({})
    account_count = accounts_collection.count_documents({})
    await event.reply(f"Bot Statistics:\n- Authorized users: {user_count}\n- Hosted accounts: {account_count}")

# /remove command
@bot.on(events.NewMessage(pattern='/remove'))
async def remove_command(event):
    user_id = event.sender_id
    if not is_authorized(user_id):
        await event.reply("You are not authorized to use this command.")
        return
    await event.reply("Send the phone number of the account you want to remove.")
    @bot.on(events.NewMessage)
    async def process_remove(event):
        phone_number = event.text.strip()
        result = accounts_collection.delete_one({"phone_number": phone_number})
        if result.deleted_count > 0:
            os.remove(f"{CREDENTIALS_FOLDER}/session_{phone_number}.session")
            await event.reply(f"Account {phone_number} removed successfully.")
        else:
            await event.reply("Account not found.")

# /adduser command
@bot.on(events.NewMessage(pattern='/adduser'))
async def add_user_command(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("You are not authorized to use this command.")
        return
    try:
        new_user_id = int(event.text.split()[1])
        if users_collection.find_one({"user_id": new_user_id}):
            await event.reply("User is already authorized.")
        else:
            users_collection.insert_one({"user_id": new_user_id})
            await event.reply(f"User {new_user_id} added successfully.")
    except Exception as e:
        await event.reply(f"Error: {e}")

# /removeuser command
@bot.on(events.NewMessage(pattern='/removeuser'))
async def remove_user_command(event):
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("You are not authorized to use this command.")
        return
    try:
        target_user_id = int(event.text.split()[1])
        result = users_collection.delete_one({"user_id": target_user_id})
        if result.deleted_count > 0:
            await event.reply(f"User {target_user_id} removed successfully.")
        else:
            await event.reply("User not found.")
    except Exception as e:
        await event.reply(f"Error: {e}")

# Start the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
