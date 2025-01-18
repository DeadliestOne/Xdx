import os
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession

# Replace with your own API credentials
API_ID = '26416419'  # Get it from my.telegram.org
API_HASH = 'c109c77f5823c847b1aeb7fbd4990cc4'  # Get it from my.telegram.org
BOT_API_TOKEN = '7982088140:AAFOZ5B9BwMWibArOEGoEBg50V2PZdKe_hg'  # Replace with your bot's API token

# Folder to save session files
SESSION_FOLDER = 'sessions'

# Make the folder to store the session files
if not os.path.exists(SESSION_FOLDER):
    os.mkdir(SESSION_FOLDER)

# Initialize the Telegram bot
bot = TelegramClient('bot', API_ID, API_HASH)

# This will hold the clients for each account
clients = {}

# Function to log in and save session
async def login(account_name, phone_number):
    # Create a unique session file for each account
    session_name = f"{SESSION_FOLDER}/{account_name}_session"
    
    # Check if the session already exists
    if os.path.exists(session_name):
        return f"Account {account_name} already logged in!"
    
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        # Wait for the user to send the OTP
        return f"OTP sent to {phone_number}. Please send the OTP to complete login."

    clients[account_name] = client
    return f"Account {account_name} logged in successfully!"

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Welcomes the user and provides instructions."""
    await event.reply("Welcome! Use the following commands:\n"
                      "/login {account_name} {phone_number} - To login with a new account.\n"
                      "/accounts - List logged-in accounts.\n"
                      "/logout {account_name} - Log out from an account.\n"
                      "/help - Show this message.")

@bot.on(events.NewMessage(pattern='/login'))
async def login_command(event):
    """Logs in a new account."""
    user_input = event.text.split()
    if len(user_input) != 3:
        await event.reply("Usage: /login {account_name} {phone_number}")
        return

    account_name, phone_number = user_input[1], user_input[2]
    message = await login(account_name, phone_number)
    await event.reply(message)

@bot.on(events.NewMessage(pattern='/accounts'))
async def accounts_command(event):
    """Lists all logged-in accounts."""
    if not clients:
        await event.reply("No accounts are logged in.")
    else:
        accounts_list = "\n".join(clients.keys())
        await event.reply(f"Logged-in accounts:\n{accounts_list}")

@bot.on(events.NewMessage(pattern='/logout'))
async def logout_command(event):
    """Logs out from an account."""
    user_input = event.text.split()
    if len(user_input) != 2:
        await event.reply("Usage: /logout {account_name}")
        return

    account_name = user_input[1]
    if account_name in clients:
        client = clients[account_name]
        await client.disconnect()
        del clients[account_name]
        await event.reply(f"Account {account_name} logged out successfully.")
    else:
        await event.reply(f"Account {account_name} is not logged in.")

@bot.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    """Displays help."""
    await event.reply("Use the following commands:\n"
                      "/login {account_name} {phone_number} - Log in with a new account.\n"
                      "/accounts - List logged-in accounts.\n"
                      "/logout {account_name} - Log out from an account.\n"
                      "/help - Show this message.")

# Start the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
