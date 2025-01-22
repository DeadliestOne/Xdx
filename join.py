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

# Temporary storage for user data
user_data = {}


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    user_id = sender.id

    # Welcome message and request phone number
    await event.reply(
        "Welcome! To proceed, please provide your phone number in the format:\n\n"
        "`+1234567890`"
    )
    user_data[user_id] = {'status': 'awaiting_phone', 'otp': None}


@client.on(events.NewMessage)
async def handle_user_input(event):
    sender = await event.get_sender()
    user_id = sender.id

    if user_id not in user_data:
        return  # Ignore messages from users not in the flow

    # Check the user's current status
    user_status = user_data[user_id]['status']

    if user_status == 'awaiting_phone':
        phone_number = event.message.message.strip()

        # Validate phone number format
        if re.match(r"^\+\d{10,15}$", phone_number):
            user_data[user_id]['phone'] = phone_number
            user_data[user_id]['status'] = 'awaiting_otp'

            # Generate a default OTP (e.g., a random 6-digit number)
            otp = f"{random.randint(100000, 999999)}"
            user_data[user_id]['otp'] = otp

            # Simulate sending OTP
            await event.reply(
                f"Phone number received: {phone_number}\n\n"
                f"Your OTP is: `{otp}`\n\nPlease send the OTP to verify your number."
            )
        else:
            await event.reply("Invalid phone number format. Please try again in the format:\n\n`+1234567890`")

    elif user_status == 'awaiting_otp':
        otp_input = event.message.message.strip()

        # Validate OTP
        if otp_input == user_data[user_id]['otp']:
            user_data[user_id]['status'] = 'verified'
            await event.reply("✅ OTP verified! You can now send the `/join_groups` command to proceed.")
        else:
            await event.reply("❌ Invalid OTP. Please try again.")

    elif user_status == 'verified':
        # Handle additional commands or reset flow
        await event.reply("You're already verified. Use `/join_groups` to start joining groups.")


@client.on(events.NewMessage(pattern='/join_groups'))
async def join_groups(event):
    sender = await event.get_sender()
    user_id = sender.id

    # Check if the user is verified
    if user_id not in user_data or user_data[user_id]['status'] != 'verified':
        await event.reply("You must verify your phone number and OTP first. Use `/start` to begin.")
        return

    # Proceed with group joining logic (same as before)
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


# Notify the bot is running
print("Bot is running. Send /start to begin.")

# Start the bot
client.run_until_disconnected()
