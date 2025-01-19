import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to scrape lyrics from Genius
def get_lyrics(song_name: str) -> str:
    try:
        search_url = f"https://genius.com/search?q={song_name.replace(' ', '%20')}"
        search_page = requests.get(search_url)
        
        # Check if the request was successful
        if search_page.status_code != 200:
            return "Error: Unable to fetch search results. Please try again later."
        
        soup = BeautifulSoup(search_page.text, 'html.parser')

        # Look for the first result link
        song_link = soup.find('a', {'class': 'mini_card'})
        
        if not song_link:
            return "Sorry, no results found for this song."

        song_url = song_link['href']
        song_page = requests.get(song_url)

        # Check if the song page is available
        if song_page.status_code != 200:
            return "Error: Unable to fetch the song page. Please try again later."

        song_soup = BeautifulSoup(song_page.text, 'html.parser')

        # Find the lyrics section
        lyrics = song_soup.find('div', {'class': 'lyrics'})
        
        if lyrics:
            return lyrics.get_text().strip()
        else:
            return "Sorry, I couldn't find the lyrics for this song."

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return f"An error occurred while fetching the lyrics: {e}"

# Command handler for '/lyric' command
async def lyric(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    song_name = ' '.join(context.args)
    if not song_name:
        await update.message.reply_text("Please provide a song name. Usage: /lyric <song name>")
        return

    lyrics = get_lyrics(song_name)
    await update.message.reply_text(lyrics)

# Main function to set up the bot
def main():
    # Replace with your bot's token
    token = 'YOUR_TELEGRAM_BOT_API_TOKEN'

    # Create the Application and Dispatcher
    application = Application.builder().token(token).build()

    # Register the /lyric command handler
    application.add_handler(CommandHandler("lyric", lyric))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
