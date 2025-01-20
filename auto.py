import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
import yt_dlp

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
            'cookies': '# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1737266159	GPS	1
.youtube.com	TRUE	/	TRUE	0	YSC	ifft8tWhRxo
.youtube.com	TRUE	/	TRUE	1752816418	VISITOR_INFO1_LIVE	jFAEj2seQK0
.youtube.com	TRUE	/	TRUE	1752816418	VISITOR_PRIVACY_METADATA	CgJJThIEGgAgaA%3D%3D
.youtube.com	TRUE	/	TRUE	1752816359	__Secure-ROLLOUT_TOKEN	CO3ZxO2KqMLvTRDMutiIhoGLAxjMutiIhoGLAw%3D%3D
.youtube.com	TRUE	/	TRUE	1771824433	PREF	f6=40000000&tz=Asia.Kolkata&f7=100
.youtube.com	TRUE	/	TRUE	1768800414	__Secure-1PSIDTS	sidts-CjEBmiPuTYJa-2J-kRRX4CROFPQfBDvbU6MCUidTaIamYevAPeDAnT1e5a-NQrkzQLoZEAA
.youtube.com	TRUE	/	TRUE	1768800414	__Secure-3PSIDTS	sidts-CjEBmiPuTYJa-2J-kRRX4CROFPQfBDvbU6MCUidTaIamYevAPeDAnT1e5a-NQrkzQLoZEAA
.youtube.com	TRUE	/	FALSE	1771824418	HSID	A-tH2AWtVnk-vzE36
.youtube.com	TRUE	/	TRUE	1771824418	SSID	AkpU6Woj3HZHxfnmN
.youtube.com	TRUE	/	FALSE	1771824418	APISID	0umRik8NLDADvvQw/AkiXjZ_k3ng3AT5z8
.youtube.com	TRUE	/	TRUE	1771824418	SAPISID	TneezPy25Pm0gQUe/A76JuVHV4ORLJxAJY
.youtube.com	TRUE	/	TRUE	1771824418	__Secure-1PAPISID	TneezPy25Pm0gQUe/A76JuVHV4ORLJxAJY
.youtube.com	TRUE	/	TRUE	1771824418	__Secure-3PAPISID	TneezPy25Pm0gQUe/A76JuVHV4ORLJxAJY
.youtube.com	TRUE	/	FALSE	1771824418	SID	g.a000sgjIoXFBVtXzAoD9_49PEFDLw7F1-MhC_sG_rXLK1iuvBQ5rBeZHmpO6e5N68inVrUws6QACgYKAZYSARISFQHGX2MiXC7igJWsIBperP1lhdY-wRoVAUF8yKrfSReM3tsScVozOLnDbx3W0076
.youtube.com	TRUE	/	TRUE	1771824418	__Secure-1PSID	g.a000sgjIoXFBVtXzAoD9_49PEFDLw7F1-MhC_sG_rXLK1iuvBQ5rj8I6931IXCch5OlkREKFnwACgYKASkSARISFQHGX2MipUSTBgLs7GYBv3NXKKELUBoVAUF8yKrbB5FOhQ4aZbCEVgw-3lOF0076
.youtube.com	TRUE	/	TRUE	1771824418	__Secure-3PSID	g.a000sgjIoXFBVtXzAoD9_49PEFDLw7F1-MhC_sG_rXLK1iuvBQ5rjMmOfik50VSwuATHpbPyaAACgYKATESARISFQHGX2MihBpmZgtllHVcSNZCuFlKQBoVAUF8yKo_e0A9bccTi1X4dkzZ6syl0076
.youtube.com	TRUE	/	FALSE	1768800511	SIDCC	AKEyXzX8UFEsrmTFKw-PbbAp-IDfB0TtBB7IIipzNKLoHBUUhemq_znu_aA7WjBj1s898fIEfA
.youtube.com	TRUE	/	TRUE	1768800511	__Secure-1PSIDCC	AKEyXzWNkFXNVppKXXJc5N83eAgEBkxV7QTcNEhEItHH9dwycOloxBCoDnXcVLwCviFw75nGjw
.youtube.com	TRUE	/	TRUE	1768800511	__Secure-3PSIDCC	AKEyXzWyd1HhAfoo8zoDL1SzuM6plPvTfHluFdhcnxTZNYn26CuULVJ8ko75Gdz40fgv6vUBlw
.youtube.com	TRUE	/	TRUE	1737264537	YTSESSION-rvkia	ANPz9Ki+W/Hd8YBXlFxYcaSer1eGY0oy5Wmd2XRNye/hVvOy1YLEsvijc27dil17X6sNzJVAHohbJmmatBVoPETqfNjyWrxXtbrqjRGodrcVFdtnDEZEulDJXmT7xyW+PDIL7n2ivHtndXu5/ZspBrs22UjYCF0UvKxmSvT6c6sH3A==
.youtube.com	TRUE	/	TRUE	1771824418	LOGIN_INFO	AFmmF2swRgIhAJ3FBi4kYoV1wRpj5_jdrCDCr7XUlNOnAfkTduB-GlYzAiEA5V2Fg7jXR2LvVqbaW4aTyGJqjoMAhqu-7Ef2Arg1U1w:QUQ3MjNmeHNxckgxVnA1UDZIME0wZ1BzeUNzN3FhMGZvUWJ0TmpXcV9JLXU3eDc2Zk5sN3NUUVRUdFIyb3ZFQWJkVGJvRnEydUtJbm1BcVQxYVpmbXdEVlQybVVneTNHUnpJdU92VUE5WnowQ2ZyVFpSUjBaRXBybmZBUFFKbDdZQ1RRMldUSVpSZHFPWEZVcTBQX1NCTWx1bGtWTTdlODZB
.youtube.com	TRUE	/	FALSE	1737264439	ST-12zd86k	csn=LIHnNCuVRVMM777q&itct=CJsBEPxaGAAiEwjzu-CphoGLAxXWSJ0JHTK1CecyBnNlYXJjaFIYdHUgYmFhdCBrYXJleWEgbmEgbXVqaHNlmgEDEPQk',                  # Use cookies for authentication
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
