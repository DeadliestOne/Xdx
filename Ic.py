import logging
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types import Update
import yt_dlp as youtube_dl

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Pyrogram Client
app = Client("music_bot", api_id="26416419", api_hash="c109c77f5823c847b1aeb7fbd4990cc4", bot_token="7869333256:AAEAB080RyfVdjcG1lz9_7iUb7qjixV28Rs)

# Initialize PyTgCalls
pytgcalls = PyTgCalls(app)

# The voice chat's group ID (you'll need to have a group to call in)
GROUP_ID = -1002342618765  # Replace with your group's chat ID

# Function to download audio from YouTube
async def download_audio(url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'outtmpl': 'downloads/%(id)s.%(ext)s',  # Save the file in a downloads folder
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return f"downloads/{info['id']}.webm"  # Path of the downloaded file

# Command to play a song
@app.on_message(filters.command("play"))
async def play_song(client, message):
    song_name = message.text.split(" ", 1)[1]  # Get the song name from the command
    await message.reply("Searching for the song...")

    # Use youtube-dl to find the song's URL
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
        url = info['entries'][0]['url']

    # Download the audio
    audio_path = await download_audio(url)
    await message.reply(f"Found the song! Now playing {song_name} in the voice chat.")

    # Join the voice chat and stream the audio
    await pytgcalls.join_group_call(
        GROUP_ID,
        audio_path,
        stream_type=StreamType().local_stream,
    )

# Command to stop the music
@app.on_message(filters.command("stop"))
async def stop_music(client, message):
    await pytgcalls.leave_group_call(GROUP_ID)
    await message.reply("Music stopped and left the voice chat!")

# Command to start the bot
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Hi! I'm your music bot. Use /play <song name> to play a song.")

# Run the bot
if __name__ == "__main__":
    app.run()
