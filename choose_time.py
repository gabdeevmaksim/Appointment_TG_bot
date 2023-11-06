import logging
import csv
import os
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, Application, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Set up the bot token
TOKEN = '5939122345:AAE_6pHG2-XW6QSgxzilI-JEm0xr6AWbfbg'
CSV_FILE = 'data.csv'

# Define a function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

# Define a function to handle incoming messages
async def echo(update: Update, context):
    with open(CSV_FILE, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Availability'].lower() == 'true':
                context.bot.send_message(chat_id=update.effective_chat.id, text=row['time'])

# Define a function to handle the time selection
async def handle_time(update: Update, context):
    selected_time = update.message.text.strip()

    # Read the CSV file and update the 'Availability' column
    data = []
    with open(CSV_FILE, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['time'] == selected_time:
                row['Availability'] = 'False'
            data.append(row)

    # Rewrite the CSV file with the updated values
    with open(CSV_FILE, 'w', newline='') as csvfile:
        fieldnames = ['time', 'Availability']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    context.bot.send_message(chat_id=update.effective_chat.id, text=f"You selected the time: {selected_time}. The availability has been updated.")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time))
    application.add_handler(MessageHandler(filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()