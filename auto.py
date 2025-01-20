from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
import instaloader
import os
import re

# Instagram credentials
INSTAGRAM_USERNAME = "WeAkatsuki"  # Replace with your Instagram username
INSTAGRAM_PASSWORD = "Hello@345"  # Replace with your Instagram password

# Owner Telegram user ID
OWNER_ID = 6748827895  # Replace with your Telegram user ID

# Start command handler
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Hello! Send me a public or private Instagram post link, and I'll download the video for you."
    )

# Notify the owner when the bot starts
async def notify_owner(application: Application) -> None:
    try:
        await application.bot.send_message(
            chat_id=OWNER_ID,
            text="Bot has started and is now running!"
        )
    except Exception as e:
        print(f"Failed to send start notification to owner: {e}")

# Instagram video downloader handler
async def download_instagram_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()

    # Validate the Instagram URL
    if not re.match(r'https?://(www\.)?instagram\.com/(p|reel|tv)/[a-zA-Z0-9-_]+', url):
        await update.message.reply_text("Please send a valid Instagram post, reel, or TV link.")
        return

    try:
        # Initialize Instaloader
        loader = instaloader.Instaloader(save_metadata=False, download_videos=True, post_metadata_txt_pattern="")

        # Log in to Instagram
        loader.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        # Extract shortcode from URL
        shortcode = url.split("/")[-2]

        # Define download directory
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)

        # Download post
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=download_dir)

        # Find downloaded video file
        for file in os.listdir(download_dir):
            if file.endswith(".mp4"):
                video_path = os.path.join(download_dir, file)
                
                # Send video to the user
                with open(video_path, 'rb') as video_file:
                    await update.message.reply_video(video=video_file, caption=f"Here is your video from Instagram!")
                
                # Clean up
                os.remove(video_path)
                break

        # Remove leftover files
        for file in os.listdir(download_dir):
            os.remove(os.path.join(download_dir, file))

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

# Main function to start the bot
def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = Application.builder().token("7208430789:AAEhpDdFXugHH9-PTKrZzcQnwFkkuUlCfI4").build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram_video))

    # Notify owner when the bot starts
    application.post_init(notify_owner)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
