import time
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
import instaloader

# Global dictionary to store monitoring information
monitoring_accounts = {}

# Function to check if an Instagram account is accessible
def is_account_active(username):
    loader = instaloader.Instaloader()
    try:
        instaloader.Profile.from_username(loader.context, username)
        return True
    except Exception:
        return False

# Command to start monitoring an Instagram account
def banwatch(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usage: /banwatch <username>")
        return

    username = context.args[0]
    user_id = update.message.chat_id

    if username in monitoring_accounts:
        update.message.reply_text(f"Already monitoring @{username}.")
        return

    # Add the username to the monitoring list
    monitoring_accounts[username] = {
        "start_time": datetime.now(),
        "user_id": user_id,
    }

    update.message.reply_text(f"Started monitoring @{username} for bans.")

# Background job to check account status
def check_ban_status(context: CallbackContext):
    to_remove = []

    for username, info in monitoring_accounts.items():
        if not is_account_active(username):
            start_time = info["start_time"]
            elapsed_time = datetime.now() - start_time
            hours, remainder = divmod(elapsed_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            context.bot.send_message(
                chat_id=info["user_id"],
                text=f"Banned @{username}. Took {hours} Hours and {minutes} Minutes."
            )
            to_remove.append(username)

    # Remove banned accounts from monitoring list
    for username in to_remove:
        del monitoring_accounts[username]

# Main function to start the bot
def main():
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("banwatch", banwatch))

    # Set up job queue for periodic checks
    job_queue = updater.job_queue
    job_queue.run_repeating(check_ban_status, interval=60)  # Check every 1 minute

     # Print a message indicating the bot has started
    print("Bot is starting and now running...")

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
