import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Store bot data (In a real-world case, store this in a database or file)
bot_data = {}

# Command for creating a new bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hello! I'm a bot management bot. Type /createbot to create a new bot.")

def create_bot(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id in bot_data:
        update.message.reply_text("You already have a bot created! Type /viewbot to see its details.")
        return
    
    # Ask user for the bot name and username
    update.message.reply_text("Please provide a bot name (e.g., MyBot).")
    return

def process_bot_name(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    bot_name = update.message.text

    bot_data[user_id] = {"bot_name": bot_name}

    update.message.reply_text(f"Got it! Now, please provide the bot username (e.g., my_bot).")
    return

def process_bot_username(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    bot_username = update.message.text

    if user_id in bot_data:
        bot_data[user_id]["bot_username"] = bot_username
        update.message.reply_text(f"Great! Your bot '{bot_data[user_id]['bot_name']}' with username @{bot_username} is created.")

        # Allow users to manage commands after bot creation
        update.message.reply_text("Now you can manage bot commands. Type /addcommand to add a command.")
    else:
        update.message.reply_text("You haven't created a bot yet. Type /createbot to create one.")

def add_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in bot_data:
        update.message.reply_text("Please provide the command you'd like to add (e.g., /start).")
    else:
        update.message.reply_text("You need to create a bot first. Type /createbot.")

def process_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    command = update.message.text.strip()

    if user_id in bot_data:
        bot_data[user_id]["command"] = command
        update.message.reply_text(f"Command '{command}' has been added to your bot!")
    else:
        update.message.reply_text("You need to create a bot first. Type /createbot.")

def view_bot(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in bot_data:
        bot_info = bot_data[user_id]
        bot_name = bot_info.get("bot_name", "Not set")
        bot_username = bot_info.get("bot_username", "Not set")
        bot_command = bot_info.get("command", "No commands added")

        update.message.reply_text(f"Your Bot Info:\nName: {bot_name}\nUsername: @{bot_username}\nCommands: {bot_command}")
    else:
        update.message.reply_text("You haven't created a bot yet. Type /createbot.")

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    # Replace with your bot's token
    token = '7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4'

    # Updater and Dispatcher
    updater = Updater(token)
    dp = updater.dispatcher

    # Define command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("createbot", create_bot))
    dp.add_handler(CommandHandler("addcommand", add_command))
    dp.add_handler(CommandHandler("viewbot", view_bot))

    # Add message handlers
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, process_bot_name))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, process_bot_username))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, process_command))

    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a stop signal (Ctrl+C)
    updater.idle()

if __name__ == '__main__':
    main()
