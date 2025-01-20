from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pytube import YouTube
import os

# Start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hello! Send me a YouTube link, and I'll download the video for you.")

# Handle YouTube links
def download_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    try:
        # Ensure it's a valid YouTube URL
        yt = YouTube(url)
        video = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
        title = yt.title
        file_path = video.download(output_path="downloads")
        
        # Send the video file
        with open(file_path, 'rb') as video_file:
            update.message.reply_video(video=video_file, caption=f"Here is your video: {title}")
        
        # Clean up
        os.remove(file_path)
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

# Main function
def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    updater = Updater("7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4")

    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    
    # Message handler for YouTube links
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
