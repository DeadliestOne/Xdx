import os
import psutil
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from colorama import init

# Initialize colorama for colored output
init(autoreset=True)

# Replace with your API credentials
USER_API_ID = "26416419"
USER_API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"
BOT_API_TOKEN = "7571130552:AAFarufThZfioBIb5xzkHn41LZJqHyx3Gx8"

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
async def start_command(event):
    """Welcome message with interactive buttons."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("❌ You are not authorized to use this bot.")
        return

    await event.respond(
        "👋 **Welcome to the Hosting Bot!**\n\n"
        "Here are the available commands:\n"
        "🔹 **Host a New Account**\n"
        "🔹 **View Server Stats**\n"
        "🔹 **List Hosted Accounts**\n"
        "🔹 **Manage Users**\n\n"
        "👉 Use the buttons below to navigate.",
        buttons=[
            [  # Main Menu Buttons
                ("➕ Host Account", "host"),
                ("📊 Server Stats", "stats"),
            ],
            [
                ("📋 List Accounts", "accounts"),
                ("👥 Manage Users", "manage_users"),
            ],
        ]
    )


@bot.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    """Displays server stats."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("❌ You are not authorized to use this bot.")
        return

    # Fetch system stats
    ram_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)
    total_accounts = len(accounts)
    hosting_capacity = max(0, 50 - total_accounts)  # Assuming a limit of 50 accounts

    await event.respond(
        "📊 **Server Stats:**\n\n"
        f"💻 **RAM Usage:** {ram_usage}%\n"
        f"⚙️ **CPU Usage:** {cpu_usage}%\n"
        f"📂 **Hosted Accounts:** {total_accounts}\n"
        f"🔹 **Remaining Capacity:** {hosting_capacity} accounts",
        buttons=[("🔙 Back to Menu", "menu")],
    )


@bot.on(events.NewMessage(pattern='/host'))
async def host_command(event):
    """Starts the hosting process for a new account."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("❌ You are not authorized to use this bot.")
        return

    user_states[user_id] = {'step': 'awaiting_credentials'}
    await event.respond(
        "📩 **To host a new account:**\n\n"
        "Please send your details in the following format:\n\n"
        "`API_ID|API_HASH|PHONE_NUMBER`\n\n"
        "Example: `123456|abc123xyz|+1234567890`",
        buttons=[("🔙 Back to Menu", "menu")],
    )


@bot.on(events.NewMessage(pattern='/accounts'))
async def accounts_command(event):
    """Lists all hosted accounts."""
    user_id = event.sender_id
    if user_id not in ALLOWED_USERS:
        await event.reply("❌ You are not authorized to use this bot.")
        return

    if not accounts:
        await event.respond("📂 **No accounts are currently hosted.**", buttons=[("🔙 Back to Menu", "menu")])
        return

    account_list = '\n'.join([f"{i+1}. {phone}" for i, phone in enumerate(accounts.keys())])
    await event.respond(
        f"📋 **Hosted Accounts:**\n\n{account_list}",
        buttons=[("🔙 Back to Menu", "menu")],
    )


@bot.on(events.NewMessage(pattern='/add'))
async def add_command(event):
    """Adds a user to the allowed list."""
    user_id = event.sender_id
    if user_id != OWNER_ID:
        await event.reply("❌ You are not authorized to use this command.")
        return

    user_input = event.text.split()
    if len(user_input) != 2:
        await event.reply("Usage: /add {user_id}")
        return

    try:
        new_user_id = int(user_input[1])
        ALLOWED_USERS.add(new_user_id)
        await event.respond(f"✅ User `{new_user_id}` has been added to the allowed list.", buttons=[("🔙 Back to Menu", "menu")])
    except ValueError:
        await event.reply("❌ Invalid user ID.")


@bot.on(events.CallbackQuery)
async def callback_handler(event):
    """Handles all button actions."""
    action = event.data.decode('utf-8')

    if action == "menu":
        await start_command(event)
    elif action == "stats":
        await stats_command(event)
    elif action == "host":
        await host_command(event)
    elif action == "accounts":
        await accounts_command(event)
    elif action == "manage_users":
        await event.respond(
            "👥 **Manage Users:**\n\n"
            "Use the following commands:\n"
            "/add {user_id} - Add a new user\n"
            "/remove {user_id} - Remove a user\n",
            buttons=[("🔙 Back to Menu", "menu")],
        )


# Run the bot
print("🤖 Bot is running...")
bot.start(bot_token=BOT_API_TOKEN)
bot.run_until_disconnected()
    
