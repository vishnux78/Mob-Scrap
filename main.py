# Copyright (C) @TheSmartBisnu
# Channel: https://t.me/itsSmartDev

import re
import os
import asyncio
import time
from urllib.parse import urlparse
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserNotParticipant, ChannelPrivate

# --- Configuration ---
# It's recommended to use environment variables for security.
# However, you can hardcode them here if needed.
API_ID = int(os.environ.get("API_ID", "36678014"))
API_HASH = os.environ.get("API_HASH", "2f674efd2652a5cb857af17ae0056699")
SESSION_STRING = os.environ.get("SESSION_STRING", "BQIvqX4ABBEsl11Av_t7NO-ed_IUd_AfhcbN-5BKJcMJgs8m3S3l0IPdC3JxsLrnjStXlCi_XpQUfGUkrbUwVuiEa1GI44SzuhzfJ07cYZ9bkmGbuwlf8ceFhCJ2XNozVPUq4Lj8cNyIu-ruh5DlGyR759sZHtngTYth3HEGRO1Vs0iJ1aNFATbJKhV4KojMCqmpEHN2Z33PdgGlHnhqQm8uHtaqp9YBNLxH10jdM8M-LmRxbiCfkvePg_WstUPl9jZy5lBbdvP9iPQ5s8VwYXJv_R3xf3xd0S5CDDT2Hff-xNv3I-xYukdpz-g1GPTGLTPzbTsm0zV7-9Vg-HHI7YSHvh8OyAAAAAHu1oLwAA")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8542163039:AAEAxU_6yeh9I5H05VMY8iZo3vA78L--6j4")

# Admin and Limit settings
ADMIN_IDS = [8302002928,]
DEFAULT_LIMIT = 10000
ADMIN_LIMIT = 50000
# --- End of Configuration ---

# --- Bot Setup ---
bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=100,
    parse_mode=ParseMode.HTML
)

user = Client(
    "user_session",
    session_string=SESSION_STRING,
    workers=100
)
# --- End of Bot Setup ---

# --- In-memory storage ---
user_stats = {}
active_tasks = {}
bot_start_time = time.time()
# --- End of storage ---


# --- Helper Functions ---
def remove_duplicates(messages):
    """Removes duplicate cards from a list."""
    unique_messages = list(set(messages))
    duplicates_removed = len(messages) - len(unique_messages)
    return unique_messages, duplicates_removed

def format_time(seconds):
    """Formats seconds into a human-readable string (h m s)."""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    return f"{int(minutes)}m {int(seconds)}s"

def get_uptime():
    """Returns the bot's uptime."""
    return format_time(time.time() - bot_start_time)

def get_progress_bar(progress):
    """Creates a textual progress bar."""
    bar = "▰" * int(progress / 10)
    bar += "▱" * (10 - int(progress / 10))
    return bar
# --- End of Helper Functions ---


# --- Core Scraping Logic ---
async def scrape_messages(client, channel_id, limit, bin_filter=None, progress_callback=None):
    """The main function to scrape and format credit cards from messages."""
    messages = []
    count = 0
    pattern = r'\d{16}\D*\d{2}\D*\d{2,4}\D*\d{3,4}' # <<< --- THIS IS YOUR EXACT CORE LOGIC
    last_update_time = 0

    async for message in user.search_messages(channel_id):
        if len(messages) >= limit: # Check total found so far
            break
        text = message.text or message.caption
        if not text:
            continue

        matched_cards = re.findall(pattern, text)
        if not matched_cards:
            continue

        for card in matched_cards:
            values = re.findall(r'\d+', card)
            if len(values) == 4:
                card_number, month, year, cvv = values
                year = year[-2:] # <<< --- THIS IS YOUR EXACT CORE LOGIC
                formatted_card = f"{card_number}|{month}|{year}|{cvv}"
                
                if bin_filter and not formatted_card.startswith(bin_filter):
                    continue
                
                messages.append(formatted_card)

                # Stop if we have reached the limit
                if len(messages) >= limit:
                    break
        
        # Update progress bar every 3 seconds to avoid API spam
        current_count = len(messages)
        if progress_callback and (time.time() - last_update_time > 3 or current_count == limit):
            await progress_callback(min(current_count, limit), limit)
            last_update_time = time.time()
                
    return messages[:limit]
# --- End of Core Scraping Logic ---


# --- Command Handlers ---
@bot.on_message(filters.command(["start"]))
async def start_cmd(client, message):
    user_name = message.from_user.first_name
    is_admin = message.from_user.id in ADMIN_IDS
    limit = ADMIN_LIMIT if is_admin else DEFAULT_LIMIT
    
    start_text = f"""
<b>Welcome, {user_name}!</b> 👋

I am an advanced CC Scraper Bot designed to help you extract credit card information efficiently.

<b><u>Key Features:</u></b>
-  Scraping from public & private channels
- BIN filtering to find specific cards
- Fast, reliable, and removes duplicates

Use the <b>/help</b> command to see how to use me.

<b>Your Status:</b> {'Admin' if is_admin else 'User'}
<b>Scrape Limit:</b> <code>{limit}</code> cards per request
"""
    await message.reply_text(start_text, disable_web_page_preview=True)

@bot.on_message(filters.command(["help"]))
async def help_cmd(client, message):
    help_text = """
<b>📖 How to Use the Scraper Bot</b>

Here are the available commands and how to use them:

<b>1. Basic Scraping:</b>
   <code>/scr [channel_username] [amount]</code>
   <i>Example:</i> <code>/scr @SomeChannel 1000</code>
   This will scrape the latest 1000 credit cards from the specified channel.

<b>2. Scraping with a BIN Filter:</b>
   <code>/scr [channel_username] [amount] [BIN]</code>
   <i>Example:</i> <code>/scr @SomeChannel 500 405060</code>
   This will scrape 500 cards that start with the BIN `405060`.

<b><u>Other Commands:</u></b>
- /start - Shows the welcome message.
- /stats - Displays your personal scraping statistics.

<b>NOTE:</b> To scrape from a private channel, the user account connected via `SESSION_STRING` must be a member of that channel.
"""
    await message.reply_text(help_text, disable_web_page_preview=True)

@bot.on_message(filters.command(["stats"]))
async def stats_cmd(client, message):
    user_id = message.from_user.id
    stats = user_stats.get(user_id, {"scrapes": 0, "cards": 0})
    is_admin = user_id in ADMIN_IDS
    
    stats_text = f"""
<b>📊 Your Scraping Statistics</b>

<b>User:</b> {message.from_user.mention}
<b>Status:</b> {'Admin' if is_admin else 'User'}
- - - - - - - - - - - - - - -
<b>Total Scrapes:</b> <code>{stats['scrapes']}</code>
<b>Total Cards Found:</b> <code>{stats['cards']}</code>
- - - - - - - - - - - - - - -
<b>Bot Uptime:</b> <code>{get_uptime()}</code>
"""
    await message.reply_text(stats_text)

@bot.on_message(filters.command(["scr"]))
async def scr_cmd(client, message):
    user_id = message.from_user.id

    if user_id in active_tasks:
        await message.reply_text("<b>⚠️ You already have a scraping task in progress. Please wait for it to complete before starting a new one.</b>")
        return

    args = message.text.split()
    if not (3 <= len(args) <= 4):
        await message.reply_text("<b>Invalid format!</b>\nUse /help to see the correct usage.")
        return

    try:
        channel_identifier = args[1]
        limit = int(args[2])
        bin_filter = args[3] if len(args) == 4 else None
    except ValueError:
        await message.reply_text("<b>❌ Invalid Amount.</b> Please provide a number for the amount.")
        return

    if limit <= 0:
        await message.reply_text("<b>❌ Amount must be greater than 0.</b>")
        return

    max_limit = ADMIN_LIMIT if user_id in ADMIN_IDS else DEFAULT_LIMIT
    if limit > max_limit:
        await message.reply_text(f"<b>❌ Limit Exceeded.</b> Your maximum scrape limit is <code>{max_limit}</code> cards.")
        return

    try:
        if "t.me/" in channel_identifier:
            parsed_url = urlparse(channel_identifier)
            channel_username = parsed_url.path.lstrip('/')
        else:
            channel_username = channel_identifier.lstrip('@')
            
        chat = await user.get_chat(channel_username)
        channel_name = chat.title
    except UserNotParticipant:
        await message.reply_text("<b>❌ Access Denied.</b> The user account is not a member of this channel. Please join it first.")
        return
    except ChannelPrivate:
        await message.reply_text("<b>❌ Channel is Private.</b> The user account does not have access to this channel.")
        return
    except Exception as e:
        await message.reply_text(f"<b>❌ Error:</b> Could not access the channel. Please check the username/link.\n<i>({e})</i>")
        return

    active_tasks[user_id] = True
    start_time = time.time()
    
    status_msg = await message.reply_text(f"<b>Initializing scrape...</b>\nFrom: <code>{channel_name}</code>")

    async def update_progress(found, total):
        try:
            percentage = (found / total) * 100
            elapsed_time = format_time(time.time() - start_time)
            progress = get_progress_bar(percentage)
            
            await status_msg.edit_text(f"""
<b>Scraping in Progress...</b>

<b>Source:</b> <code>{channel_name}</code>
<b>Found:</b> <code>{found} / {total}</code>
<b>Progress:</b> <code>{progress}</code> [{int(percentage)}%]

<b>Elapsed Time:</b> <code>{elapsed_time}</code>
""")
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass

    try:
        scraped_cards = await scrape_messages(user, chat.id, limit, bin_filter, update_progress)
        unique_cards, duplicates = remove_duplicates(scraped_cards)
        elapsed_time = format_time(time.time() - start_time)

        if user_id not in user_stats:
            user_stats[user_id] = {"scrapes": 0, "cards": 0}
        user_stats[user_id]["scrapes"] += 1
        user_stats[user_id]["cards"] += len(unique_cards)

        if not unique_cards:
            await status_msg.edit_text(f"""
<b>Scraping Complete - No Cards Found</b>

<b>Source:</b> <code>{channel_name}</code>
{f'<b>BIN Filter:</b> <code>{bin_filter}</code>' if bin_filter else ''}
<b>Time Taken:</b> <code>{elapsed_time}</code>

No cards matching your criteria were found.
""")
            return

        file_name = f"scraped_{len(unique_cards)}_{channel_name.replace(' ', '_')}.txt"
        with open(file_name, 'w') as f:
            f.write("\n".join(unique_cards))

        caption = f"""
<b>✅ Scraping Complete!</b>

<b>Source:</b> <code>{channel_name}</code>
<b>Cards Found:</b> <code>{len(unique_cards)}</code>
<b>Duplicates Removed:</b> <code>{duplicates}</code>
{f'<b>BIN Filter:</b> <code>{bin_filter}</code>' if bin_filter else ''}
- - - - - - - - - - - - - - -
<b>Time Taken:</b> <code>{elapsed_time}</code>
<b>Scraped By:</b> {message.from_user.mention}
"""
        await client.send_document(
            message.chat.id,
            document=file_name,
            caption=caption,
            reply_to_message_id=message.id
        )
        await status_msg.delete()
        os.remove(file_name)

    except Exception as e:
        await status_msg.edit_text(f"<b>❌ An error occurred during scraping:</b>\n<code>{e}</code>")
    finally:
        if user_id in active_tasks:
            del active_tasks[user_id]
# --- End of Command Handlers ---


# --- Bot Startup ---
async def main():
    await bot.start()
    await user.start()
    me = await bot.get_me()
    print(f"Bot @{me.username} started successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
# --- End of Bot Startup ---
