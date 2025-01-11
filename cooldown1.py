from telethon import TelegramClient, events, functions
from datetime import datetime, timedelta
import sqlite3

# Replace these with your API credentials
API_ID = '23688071'
API_HASH = '6a5721916b1642a04466af2219083499'
BOT_TOKEN = '7348396799:AAEnPw1-VG7wP79_9MIeUsk4QvMyxQNGB6w'
CHANNEL_USERNAME = 'takeyourbrokeasshome'  # Replace with your channel's username

# Initialize the bot
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Connect to SQLite database to track joins
conn = sqlite3.connect('join_log.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS join_log (
        user_id INTEGER,
        username TEXT,
        join_time TEXT,
        PRIMARY KEY (user_id)
    )
''')
conn.commit()

# Variable to manage cooldown
cooldown_end_time = None

# Track join times
@bot.on(events.ChatAction)
async def handler(event):
    global cooldown_end_time

    # Check if user joined
    if event.user_added:
        current_time = datetime.now()
        user_id = event.user_id
        username = event.user.username if event.user.username else "unknown"

        # Log the join time
        cursor.execute('INSERT OR REPLACE INTO join_log (user_id, username, join_time) VALUES (?, ?, ?)',
                       (user_id, username, current_time.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

        # Check if multiple users joined at the same time
        cursor.execute('SELECT COUNT(*) FROM join_log WHERE join_time > ?',
                       ((current_time - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),))
        recent_joins = cursor.fetchone()[0]

        if recent_joins >= 2:
            # Activate cooldown if multiple users joined at the same time
            cooldown_end_time = current_time + timedelta(minutes=10)
            await event.reply("Too many users joined at the same time. No new members can join for the next 10 minutes.")

            # Ban or restrict the users who joined
            for added_user in event.action.users:
                try:
                    await bot.kick_participant(event.chat_id, added_user)
                    await bot.send_message(event.chat_id, f"User {added_user.username} has been banned due to suspicious activity.")
                except Exception as e:
                    print(f"Error banning user: {e}")
            
        # If we are in cooldown, prevent new joins
        if cooldown_end_time and current_time < cooldown_end_time:
            await event.reply(f"Too many users joined at the same time. Please wait for {((cooldown_end_time - current_time).seconds // 60)} minutes before joining.")

print("Bot is running...")
bot.run_until_disconnected()
