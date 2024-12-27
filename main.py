import time
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TimedOut

API_TOKEN = '8073847069:AAH8vAiqWQAXMwKZoclT0FuSloqEeSNtbyo'  # Replace with your bot API token
MONITORING_USERNAMES = {}  # Dictionary to track usernames being monitored

# Function to check if the username exists or is banned
def check_username(username: str) -> bool:
    url = f'https://fragment.com/username/{username}'  # Use Fragment URL for validation
    try:
        response = requests.get(url)
        if response.status_code == 200 and "Unavailable" not in response.text:
            return True  # Username exists and is available
        return False  # Username is unavailable (banned or not for sale)
    except Exception as e:
        print(f"Error while checking username: {e}")
        return False

# Retry function for sending messages
async def send_message_with_retry(update, message):
    for _ in range(3):  # Retry up to 3 times
        try:
            await update.message.reply_text(message)
            return  # If successful, exit the function
        except TimedOut:
            print("Timeout occurred, retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying

    # After 3 retries, log the failure
    print(f"Failed to send message: {message}")

# Command to start monitoring a username
async def banwatch(update: Update, context: CallbackContext):
    """Start monitoring a username."""
    if len(context.args) != 1:
        await send_message_with_retry(update, "Please provide exactly one username to monitor (e.g., /banwatch target@).")
        return
    
    username = context.args[0].lstrip('@')  # Remove @ if present
    fragment_url = f"https://fragment.com/username/{username}"  # Construct the Fragment URL
    start_time = time.time()
    
    # Check if the username exists or is banned
    username_exists = check_username(username)
    if not username_exists:
        await send_message_with_retry(update, f"The username @{username} is banned")
        return  # Stop execution if the username is unavailable
    
    # Store the username and start time for tracking
    MONITORING_USERNAMES[username] = start_time
    await send_message_with_retry(
        update, f"Started monitoring @{username} for bans..."
    )

    # Monitor the username's status
    await monitor_username(update, context, username, start_time)

# Monitor the username's status
async def monitor_username(update: Update, context: CallbackContext, username: str, start_time: float):
    """Monitor the username and track time taken for account ban or deletion."""
    fragment_url = f"https://fragment.com/username/{username}"  # Construct the Fragment URL
    
    while True:
        # Check if the username is still valid on Fragment
        username_exists = check_username(username)
        
        # Calculate elapsed time in hours and minutes
        elapsed_time = time.time() - start_time
        hours, remainder = divmod(int(elapsed_time), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if not username_exists:
            # If the username is banned or deleted
            await send_message_with_retry(
                update, f"The username @{username} is now banned. Monitoring stopped.\nTime monitored: {hours} hours and {minutes} minutes."
            )
            break  # Stop monitoring after finding banned account
        
        # Check the username every 60 seconds
        await asyncio.sleep(60)

# Command to start the bot and send the /start message
async def start(update: Update, context: CallbackContext):
    """Send a welcome message when the bot starts."""
    welcome_message = (
        "Welcome! I'm here to monitor if a Telegram username gets banned. "
        "Use the command /banwatch followed by a username to start monitoring."
    )
    await send_message_with_retry(update, welcome_message)

# Start the bot
def main():
    """Start the Telegram bot."""
    application = Application.builder().token(API_TOKEN).build()

    # Handlers for commands
    application.add_handler(CommandHandler("start", start))  # /start command
    application.add_handler(CommandHandler("banwatch", banwatch))  # /banwatch command

    # Start polling
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
