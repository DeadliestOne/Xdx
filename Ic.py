import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to fetch lyrics from Lyrics.ovh API
def get_lyrics(song_name: str, artist_name: str) -> str:
    try:
        # Construct the API URL
        api_url = f"https://api.lyrics.ovh/v1/{artist_name}/{song_name}"
        response = requests.get(api_url)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return data.get("lyrics", "Sorry, no lyrics found for this song.")
        else:
            return "Sorry, I couldn't find the lyrics for this song. Please try again later."

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return "An error occurred while fetching the lyrics."

# Command handler for '/lyric' command
async def lyric(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Please provide both the song name and the artist name. Usage: /lyric <song name> <artist name>")
        return

    song_name = context.args[0]
    artist_name = context.args[1]

    lyrics = get_lyrics(song_name, artist_name)
    await update.message.reply_text(lyrics)

# Main function to set up the bot
def main():
    # Replace with your bot's token
    token = '7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4'

    # Create the Application and Dispatcher
    application = Application.builder().token(token).build()

    # Register the /lyric command handler
    application.add_handler(CommandHandler("lyric", lyric))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
