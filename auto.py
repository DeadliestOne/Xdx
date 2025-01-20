from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
import yt_dlp
import os

# Start command handler
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hello! Send me a YouTube link, and I'll download the video for you.")

# Download video handler
async def download_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    try:
        # Define download options
        options = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',  # Save path
            'format': 'bestvideo+bestaudio/best',      # Download best quality
            'noplaylist': True,                        # Disable playlist downloads
        }

        # Download video using yt-dlp
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)  # Extract and download
            file_path = ydl.prepare_filename(info)       # Get downloaded file path

        # Send video file to user
        with open(file_path, 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption=f"Here is your video: {info['title']}")

        # Clean up downloaded file
        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Main function to start the bot
def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = Application.builder().token("7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4").build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))

    # Message handler for YouTube links
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
