import asyncio
from telethon import TelegramClient, events
import re
import random

# Replace with your credentials
api_id = "26416419"
api_hash = "c109c77f5823c847b1aeb7fbd4990cc4"
bot_token = "7528897246:AAG6cSNdbi38HQA4QGAW5Ko5c3mng6WJdnc"  # Create a bot at @BotFather and get the token

# Create the client (acting as a bot)
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

# Temporary storage for OTP-related data
user_otps = {}

# Command to trigger joining groups
@client.on(events.NewMessage(pattern='/join_groups'))
async def join_groups(event):
    sender = await event.get_sender()
    user_id = sender.id

    # Check if user has already provided an OTP
    if user_id not in user_otps:
        await event.reply("Please provide your OTP to proceed. Send it as a reply to this message.")
        return

    otp = user_otps[user_id]
    # Confirm OTP (this can be enhanced based on actual OTP validation logic)
    if otp != "123456":  # Replace "123456" with your validation logic
        await event.reply("Invalid OTP. Please try again.")
        return

    # Initial message
    status_message = await event.reply("Fetching group links from Saved Messages...")

    try:
        # Fetch messages from Saved Messages
        saved_messages = await client.get_messages("me", limit=2000)  # Adjust limit to 2000
        group_links = []
        for message in saved_messages:
            if message.message:  # Check if the message contains text
                links = re.findall(r"(https://t.me/joinchat/\S+|https://t.me/\S+)", message.message)
                group_links.extend(links)

        # Prepare for joining groups
        joined_count = 0
        failed_count = 0
        joined_groups = []
        failed_groups = []

        await status_message.edit(
            f"Found {len(group_links)} group links.\nStarting to join groups...\n\n"
            f"**Joined:** {joined_count}\n**Failed:** {failed_count}"
        )

        # Join groups with updates
        for link in group_links:
            try:
                await client.join_chat(link)
                joined_groups.append(link)
                joined_count += 1
            except Exception as e:
                failed_groups.append(f"{link} (Error: {e})")
                failed_count += 1

            # Update the status message after each attempt
            await status_message.edit(
                f"**Joining Groups:**\n\n"
                f"**Joined:** {joined_count}\n{', '.join(joined_groups[-5:])}\n\n"
                f"**Failed:** {failed_count}\n{', '.join(failed_groups[-5:])}\n\n"
                f"**Progress:** {joined_count + failed_count}/{len(group_links)}"
            )

            # Add random delay between actions
            await asyncio.sleep(random.randint(10, 30))

        # Final update
        await status_message.edit(
            f"✅ **Completed!**\n\n"
            f"**Total Groups Found:** {len(group_links)}\n"
            f"**Successfully Joined:** {joined_count}\n"
            f"**Failed to Join:** {failed_count}\n"
        )

    except Exception as e:
        await status_message.edit(f"An error occurred: {str(e)}")


# OTP handler
@client.on(events.NewMessage)
async def handle_otp(event):
    sender = await event.get_sender()
    user_id = sender.id

    # Check if it's a reply for OTP
    if "Please provide your OTP" in (await event.get_reply_message()).message:
        otp = event.message.message.strip()
        user_otps[user_id] = otp
        await event.reply("OTP received! You can now send the /join_groups command to proceed.")


# Notify the bot is running
print("Bot is running. Send /join_groups to start.")

# Start the bot
client.run_until_disconnected()
