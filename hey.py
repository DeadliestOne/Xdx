import string
import itertools
from telethon import TelegramClient, events
import asyncio

# Replace these with your own values
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
phone_number = 'YOUR_PHONE_NUMBER'

async def check_username(client, username):
    try:
        result = await client(functions.account.CheckUsernameRequest(username=username))
        return result
    except Exception as e:
        print(f"Error checking username {username}: {str(e)}")
        return False

async def find_usernames():
    client = TelegramClient('session', api_id, api_hash)
    await client.start(phone=phone_number)

    characters = string.ascii_lowercase + string.digits
    count = 0

    for username in itertools.product(characters, repeat=5):
        username = ''.join(username)
        is_available = await check_username(client, username)
        
        if is_available:
            print(f"Available username: {username}")
            count += 1
            if count >= 5:
                break

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(find_usernames())
