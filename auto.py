from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from pytube import YouTube
import os

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hello! Send me a YouTube link, and I'll download the video for you.")

# Handle YouTube links
async def download_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    try:
        # Ensure it's a valid YouTube URL
        yt = YouTube(url)
        video = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
        title = yt.title
        file_path = video.download(output_path="downloads")
        
        # Send the video file
        with open(file_path, 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption=f"Here is your video: {title}")
        
        # Clean up
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Main function
def main():
    # Replace '7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4' with your actual bot token
    application = Application.builder().token("7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4").build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    
    # Message handler for YouTube links
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
