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

# Proxy configuration (Replace with your proxy details)
PROXY = {
    'proxy_type': 'socks5',  # Proxy type: socks5, http
    'addr': '203.142.77.226',  # Replace with your proxy IP address
    'port': 8080,  # Replace with your proxy port
    'username': None,  # Proxy username if needed
    'password': None   # Proxy password if needed
}

# Initialize the Telegram bot
bot = TelegramClient('bot', API_ID, API_HASH, proxy=(PROXY['proxy_type'], PROXY['addr'], PROXY['port'], PROXY['username'], PROXY['password']))

# This will hold the clients for each account
clients = {}

# Store the OTP requests
otp_requests = {}

# Store user input for OTP
otp_inputs = {}

# Function to log in and save session
async def login(account_name, phone_number):
    # Create a unique session file for each account
    session_name = f"{SESSION_FOLDER}/{account_name}_session"
    
    # Check if the session already exists
    if os.path.exists(session_name):
        return f"Account {account_name} already logged in!"
    
    client = TelegramClient(session_name, API_ID, API_HASH, proxy=(PROXY['proxy_type'], PROXY['addr'], PROXY['port'], PROXY['username'], PROXY['password']))
    
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        otp_requests[account_name] = phone_number  # Store the phone number for OTP request
        return f"OTP sent to {phone_number}. Please send the OTP to complete login."

    clients[account_name] = client
    return f"Account {account_name} logged in successfully!"

async def verify_otp(account_name, otp):
    """Verifies the OTP entered by the user"""
    if account_name not in otp_requests:
        return f"No OTP request found for {account_name}. Please log in first."

    phone_number = otp_requests[account_name]
    client = TelegramClient(f"{SESSION_FOLDER}/{account_name}_session", API_ID, API_HASH, proxy=(PROXY['proxy_type'], PROXY['addr'], PROXY['port'], PROXY['username'], PROXY['password']))
    
    try:
        # Try to sign in using the OTP
        await client.sign_in(phone_number, otp)
        clients[account_name] = client  # Store the client after successful login
        del otp_requests[account_name]  # Remove OTP request once verified
        return f"Account {account_name} successfully logged in!"
    except Exception as e:
        return f"Failed to verify OTP for {account_name}: {str(e)}"

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Welcomes the user and provides instructions."""
    await event.reply("Welcome! Use the following commands:\n"
                      "/login {account_name} {phone_number} - To login with a new account.\n"
                      "/accounts - List logged-in accounts.\n"
                      "/logout {account_name} - Log out from an account.\n"
                      "/otp {account_name} {otp} - Provide OTP to complete login.\n"
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

@bot.on(events.NewMessage(pattern='/otp'))
async def otp_command(event):
    """Gets the OTP for the account login."""
    user_input = event.text.split()
    if len(user_input) != 3:
        await event.reply("Usage: /otp {account_name} {otp}")
        return
    
    account_name, otp = user_input[1], user_input[2]

    # Call the function to verify OTP
    message = await verify_otp(account_name, otp)
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
                      "/otp {account_name} {otp} - Provide OTP to complete login.\n"
                      "/help - Show this message.")

# Start the bot
print("Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
