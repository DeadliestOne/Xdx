import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Store bot data (In a real-world case, store this in a database or file)
bot_data = {}

# Define states for the conversation
BOT_NAME, BOT_USERNAME = range(2)

# Command for starting the bot
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hello! I'm a bot management bot. Type /createbot to create a new bot.")

# Start creating the bot
async def create_bot(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id

    if user_id in bot_data:
        await update.message.reply_text("You already have a bot created! Type /viewbot to see its details.")
        return ConversationHandler.END
    
    # Ask user for the bot name
    await update.message.reply_text("Please provide a bot name (e.g., MyBot).")
    return BOT_NAME

# Process the bot name
async def process_bot_name(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    bot_name = update.message.text

    bot_data[user_id] = {"bot_name": bot_name}

    await update.message.reply_text(f"Got it! Now, please provide the bot username (e.g., my_bot).")
    return BOT_USERNAME

# Process the bot username and finalize bot creation
async def process_bot_username(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    bot_username = update.message.text

    if user_id in bot_data:
        bot_data[user_id]["bot_username"] = bot_username
        await update.message.reply_text(f"Great! Your bot '{bot_data[user_id]['bot_name']}' with username @{bot_username} is created.")
        await update.message.reply_text("Now you can manage bot commands. Type /addcommand to add a command.")
    
    return ConversationHandler.END

# Add command functionality
async def add_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in bot_data:
        await update.message.reply_text("Please provide the command you'd like to add (e.g., /start).")
    else:
        await update.message.reply_text("You need to create a bot first. Type /createbot.")

# Process added command
async def process_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    command = update.message.text.strip()

    if user_id in bot_data:
        bot_data[user_id]["command"] = command
        await update.message.reply_text(f"Command '{command}' has been added to your bot!")
    else:
        await update.message.reply_text("You need to create a bot first. Type /createbot.")

# View bot information
async def view_bot(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in bot_data:
        bot_info = bot_data[user_id]
        bot_name = bot_info.get("bot_name", "Not set")
        bot_username = bot_info.get("bot_username", "Not set")
        bot_command = bot_info.get("command", "No commands added")

        await update.message.reply_text(f"Your Bot Info:\nName: {bot_name}\nUsername: @{bot_username}\nCommands: {bot_command}")
    else:
        await update.message.reply_text("You haven't created a bot yet. Type /createbot.")

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    # Replace with your bot's token
    token = '7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4'

    # Create Application instance
    application = Application.builder().token(token).build()

    # Define conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('createbot', create_bot)],  # Start of the conversation
        states={
            BOT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bot_name)],  # Handle bot name
            BOT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bot_username)],  # Handle bot username
        },
        fallbacks=[],
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcommand", add_command))
    application.add_handler(CommandHandler("viewbot", view_bot))

    # Register conversation handler
    application.add_handler(conversation_handler)

    # Log all errors
    application.add_error_handler(error)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
