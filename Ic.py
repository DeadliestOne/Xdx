import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to scrape lyrics from Genius
def get_lyrics(song_name: str) -> str:
    try:
        search_url = f"https://genius.com/search?q={song_name.replace(' ', '%20')}"
        search_page = requests.get(search_url)
        soup = BeautifulSoup(search_page.text, 'html.parser')

        # Find the first search result link
        song_url = soup.find('a', {'class': 'mini_card'})['href']
        song_page = requests.get(song_url)
        song_soup = BeautifulSoup(song_page.text, 'html.parser')

        # Find the lyrics section on the page
        lyrics = song_soup.find('div', {'class': 'lyrics'})
        if lyrics:
            return lyrics.get_text().strip()
        else:
            return "Sorry, I couldn't find the lyrics for this song."
    except Exception as e:
        logger.error(f"Error retrieving lyrics: {e}")
        return "An error occurred while fetching the lyrics."

# Command handler for '/lyric' command
def lyric(update: Update, context: CallbackContext) -> None:
    song_name = ' '.join(context.args)
    if not song_name:
        update.message.reply_text("Please provide a song name. Usage: /lyric <song name>")
        return

    lyrics = get_lyrics(song_name)
    update.message.reply_text(lyrics)

# Main function to set up the bot
def main():
    # Replace with your bot's token
    token = '7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4'

    # Set up the Updater and Dispatcher
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    # Register the /lyric command handler
    dp.add_handler(CommandHandler("lyric", lyric))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
