from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from time import sleep

# Bot Configuration
API_ID = '26416419'  # Replace with your Telegram API ID
API_HASH = 'c109c77f5823c847b1aeb7fbd4990cc4'  # Replace with your Telegram API Hash
BOT_TOKEN = '7881162036:AAFqwmF2ny9TEMhNdbIohy7oh507PkWk5Wg'  # Replace with your Bot Token

# Channels to Join
REQUIRED_CHANNELS = ["@BeAkatsuki", "@penguin_logs"]  # Replace with your channel usernames

# Anime Video Links
ANIME_VIDEO_LINKS = [
    "https://files.catbox.moe/6boq1r.mp4",
    "https://files.catbox.moe/u0z2un.mp4",
    "https://files.catbox.moe/yz9nzb.mp4",
    "https://files.catbox.moe/3fgazt.mp4",
    "https://files.catbox.moe/y5j0dl.mp4",
    "https://files.catbox.moe/m36po8.mp4",
    "https://files.catbox.moe/ixfxl2.mp4",
    "https://files.catbox.moe/c7wkqf.mp4",
    "https://files.catbox.moe/cuw8qy.mp4",
    "https://files.catbox.moe/hrj9hc.mp4",
    "https://files.catbox.moe/8ell4z.mp4",
    "https://files.catbox.moe/cl59ro.mp4",
    "https://files.catbox.moe/kelo65.mp4",
    "https://files.catbox.moe/brh8k2.mp4",
    "https://files.catbox.moe/l29mj8.mp4",
    "https://files.catbox.moe/463a7s.mp4",
    "https://files.catbox.moe/tz4af8.mp4",
    "https://files.catbox.moe/oc9wi0.mp4",
    "https://files.catbox.moe/1wmvrc.mp4",
]

# Initialize the Bot
app = Client("anime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def check_user_in_channels(user_id):
    """Check if the user has joined all required channels."""
    for channel in REQUIRED_CHANNELS:
        try:
            # Check the user's membership status in the channel
            member = app.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                print(f"User is not a member of {channel}")
                return False
        except Exception as e:
            print(f"Error checking membership for {channel}: {e}")
            return False
    return True

@app.on_message(filters.command("start"))
def start(bot, message):
    user_id = message.from_user.id
    if not check_user_in_channels(user_id):
        # Prompt to join channels
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Join {channel}", url=f"https://t.me/{channel[1:]}")] for channel in REQUIRED_CHANNELS
        ] + [[InlineKeyboardButton("I Joined All", callback_data="check_join")]])
        bot.send_message(
            chat_id=user_id,
            text="📢 Please join the following channels to access the anime videos:",
            reply_markup=keyboard
        )
    else:
        # Send Anime Videos
        bot.send_message(chat_id=user_id, text="🎉 Thanks for joining! Here are your anime videos:")
        for video in ANIME_VIDEO_LINKS[:100]:
            bot.send_video(chat_id=user_id, video=video)
            sleep(1)  # Avoid flooding

@app.on_callback_query(filters.regex("check_join"))
def check_join(bot, callback_query):
    user_id = callback_query.from_user.id
    if check_user_in_channels(user_id):
        bot.answer_callback_query(callback_query.id, "✅ You have joined all channels!")
        bot.send_message(chat_id=user_id, text="🎉 Thanks for joining! Here are your anime videos:")
        for video in ANIME_VIDEO_LINKS[:100]:
            bot.send_video(chat_id=user_id, video=video)
            sleep(1)  # Avoid flooding
    else:
        bot.answer_callback_query(callback_query.id, "❌ You haven't joined all channels yet. Please join first.")

# Run the Bot
print("Bot is running...")
app.run()
