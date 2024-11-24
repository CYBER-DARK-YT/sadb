from telegram import Update
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes
from datetime import datetime

# Track users to monitor for bans
monitored_users = {}

async def banwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts monitoring bans for a specific user."""
    if len(context.args) == 0:
        await update.message.reply_text("Please specify a username to monitor (e.g., /banwatch <username>).")
        return

    username = context.args[0].lstrip('@')  # Remove @ if included
    chat_id = update.effective_chat.id

    if chat_id not in monitored_users:
        monitored_users[chat_id] = []

    # Check if already monitoring the user
    if username in monitored_users[chat_id]:
        await update.message.reply_text(f"Already monitoring @{username}.")
        return

    monitored_users[chat_id].append(username)
    await update.message.reply_text(f"Started monitoring @{username} for bans.")

async def ban_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles ban events for monitored users."""
    chat_id = update.effective_chat.id
    if chat_id not in monitored_users:
        return  # No monitoring in this chat

    status_change = update.chat_member
    old_status = status_change.old_chat_member
    new_status = status_change.new_chat_member

    # Only monitor changes for users being tracked
    username = new_status.user.username
    if username not in monitored_users[chat_id]:
        return

    if old_status.status not in ["kicked", "restricted"] and new_status.status in ["kicked", "restricted"]:
        # A ban or restriction occurred
        user = new_status.user
        until_date = new_status.until_date
        ban_time = "Indefinite"

        if until_date:
            ban_duration = until_date - datetime.now()
            hours, remainder = divmod(ban_duration.total_seconds(), 3600)
            minutes = remainder // 60
            ban_time = f"{int(hours)} Hours and {int(minutes)} Minutes"

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Banned @{username}.\nTook {ban_time}."
        )

def main():
    # Your bot token here
    TOKEN = "8073847069:AAH8vAiqWQAXMwKZoclT0FuSloqEeSNtbyo"

    # Create Application
    application = Application.builder().token(TOKEN).build()

    # Add Command and ChatMember handlers
    application.add_handler(CommandHandler("banwatch", banwatch))
    application.add_handler(ChatMemberHandler(ban_monitor, ChatMemberHandler.CHAT_MEMBER))

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
