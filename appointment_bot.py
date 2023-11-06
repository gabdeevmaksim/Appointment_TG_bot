import logging
import datetime
import calendar
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stages
START_ROUTES, END_ROUTES = range(2)
# Callback data
DATE, TIME, CONTACT, IGNORE, END = range(5)

def create_callback_data(action,year,month,day):
    """ Create the callback data associated to each button"""
    return ";".join([action,str(year),str(month),str(day)])

def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")

def create_calendar(year=None,month=None):
    """
    Create an inline keyboard with the provided year and month
    :param int year: Year to use in the calendar, if None the current year is used.
    :param int month: Month to use in the calendar, if None the current month is used.
    :return: Returns the InlineKeyboardMarkup object with the calendar.
    """
    now = datetime.datetime.now()
    if year == None: year = now.year
    if month == None: month = now.month
    data_ignore = create_callback_data("IGNORE", year, month, 0)
    keyboard = []
    #First row - Month and Year
    row=[]
    row.append(InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data=data_ignore))
    keyboard.append(row)
    #Second row - Week Days
    row=[]
    for day in ["Mo","Tu","We","Th","Fr","Sa","Su"]:
        row.append(InlineKeyboardButton(day,callback_data=data_ignore))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row=[]
        for day in week:
            if(day==0):
                row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
            else:
                row.append(InlineKeyboardButton(str(day),callback_data=create_callback_data("DAY",year,month,day)))
        keyboard.append(row)
    #Last row - Buttons
    row=[]
    row.append(InlineKeyboardButton("<",callback_data=create_callback_data("PREV-MONTH",year,month,day)))
    row.append(InlineKeyboardButton("EXIT",callback_data=data_ignore))
    row.append(InlineKeyboardButton(">",callback_data=create_callback_data("NEXT-MONTH",year,month,day)))
    keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

def reform_callback_date_to_sheetname(date_callback):

    # Split the string by semicolon (;)
    date_parts = date_callback.split(';')

    # Extract the year, month, and day from the split parts
    year = date_parts[1]
    month = date_parts[2].zfill(2)  # Zero-padding the month if necessary
    day = date_parts[3].zfill(2)  # Zero-padding the day if necessary

    # Create the desired formatted string
    formatted_date = 'D' + year + month + day

    return formatted_date  # Output: D20230620

def reform_date(date_string):

    # Split the string by semicolon (;)
    date_parts = date_string.split(';')

    # Extract the year, month, and day from the split parts
    year = int(date_parts[1])
    month = int(date_parts[2])
    day = int(date_parts[3])

    # Create a datetime object using the extracted parts
    date = datetime.datetime(year, month, day)

    # Format the date in a desired format
    formatted_date = date.strftime('%Y-%m-%d')

    return formatted_date  # Output: 2023-06-20

def list_of_sheets_in_GD(json_keyfile, doc_url):
# json_keyfile - path to json_file
# doc_url - URL of GoogleDoc


    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)

    client = gspread.authorize(credentials)

    worksheet_list = client.open_by_url(doc_url).worksheets()

    sheet_names = [worksheet.title for worksheet in worksheet_list]

    return sheet_names

def open_google_sheet(json_keyfile, doc_url, sheet_name):
#json_keyfile - path to json_file
#doc_url - URL of GoogleDoc
#sheet - name of sheet

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)

    client = gspread.authorize(credentials)

    sheet = client.open_by_url(doc_url).worksheet(sheet_name)

    data_from_sheet = sheet.get_all_records()

    return data_from_sheet

def get_free_times(data):
    time_index = []
    time_value = []

    for item in data:
        if item['Availability'] == 'free':
            time_index.append(data.index(item))
            time_value.append(item['Time'])

    return time_index, time_value

def create_available_time_keyboard(callback_date):

    available_dates = list_of_sheets_in_GD(json_keyfile, doc_url)
    chosen_date = reform_callback_date_to_sheetname(callback_date)
    if chosen_date not in available_dates:
        add_sheet(chosen_date)

    data_from_sheet = open_google_sheet(json_keyfile,doc_url,chosen_date)
    time_index, options = get_free_times(data_from_sheet)

    if len(options) == 0:
        keyboard = []
        row = []
        row = [InlineKeyboardButton("Choose other date",callback_data='START_OVER')]
        keyboard.append(row)
    else:
        keyboard = []
        option_index = 0
        for i in range(len(options) // 4):
            row = []
            for _ in range(len(options) // (len(options) // 4)):
                row.append(InlineKeyboardButton(options[option_index],
                                                callback_data=str(chosen_date + options[option_index])))
                option_index += 1
            keyboard.append(row)

        # Add any remaining options to the last row if the number of options is not evenly divisible by NOL
        remaining_options = len(options) % (len(options) // 4)
        if remaining_options > 0:
            row = []
            for _ in range(remaining_options):
                row.append(InlineKeyboardButton(options[option_index],
                                                callback_data=str(chosen_date + options[option_index])))
                option_index += 1
            keyboard[-1].extend(row)

        row = []
        row = [InlineKeyboardButton("Choose other date",callback_data='START_OVER')]
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

def add_sheet(sheetname):
    # Load credentials and authorize the client
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(credentials)

    # Open the Google Sheets document
    spreadsheet = client.open_by_url(doc_url)

    # Create a new sheet with a specific name
    new_sheet_name = sheetname
    new_sheet = spreadsheet.add_worksheet(title=new_sheet_name, rows="100", cols="5")

    # Write the column headers
    header_row = ['Time', 'Availability']
    new_sheet.insert_row(header_row, index=1)

    # Write the time and availability data
    time_data = []
    availability_data = []

    for hour in range(10, 20):
        time_data.append(f'{hour:02}:00')
        availability_data.append('free')
        time_data.append(f'{hour:02}:30')
        availability_data.append('free')

    data_rows = list(zip(time_data[:-1], availability_data[:-1]))
    for row in data_rows:
        new_sheet.append_row(row)

    return "New sheet created and data written successfully!"

def confirm_datetime(datetime):

    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=datetime)],
        [InlineKeyboardButton("Choose another date", callback_data='START_OVER')],
        [InlineKeyboardButton("Choose another time", callback_data='CHANGE_TIME')],
        [InlineKeyboardButton("Cancel", callback_data='CANCEL')]
    ]

    return InlineKeyboardMarkup(keyboard)

def convert_date_string(date_str):
    # Extract the date and time parts from the string
    date_part = date_str[1:9]
    time_part = date_str[9:]

    # Convert the date part to a datetime object
    date = datetime.datetime.strptime(date_part, '%Y%m%d').date()

    # Format the date and time parts as desired
    formatted_date = date.strftime('%d %B %Y')

    # Combine the formatted date and time
    result = time_part + ' ' + formatted_date

    return result

def correct_availability(sheet_name, chosen_time, user):
    # Load credentials and authorize the client
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(credentials)

    # Open the Google Sheets document
    spreadsheet = client.open_by_url(doc_url)

    # Select the desired sheet
    sheet = spreadsheet.worksheet(sheet_name)

    # Find the row index of the chosen time in the 'Time' column
    time_values = sheet.col_values(1)
    chosen_time_index = time_values.index(chosen_time)+1

    # Correct the availability for the chosen time and the two following times
    sheet.update_cell(chosen_time_index, 2, 'entry')
    sheet.update_cell(chosen_time_index + 1, 2, 'busy')
    sheet.update_cell(chosen_time_index + 2, 2, 'busy')

    sheet.update_cell(chosen_time_index, 3, user)
    if chosen_time_index <= 3:
        index_to_change = range(1,chosen_time_index)
        [sheet.update_cell(i, 2, 'overlap') for i in index_to_change]
    else:
        sheet.update_cell(chosen_time_index - 1, 2, 'overlap')
        sheet.update_cell(chosen_time_index - 2, 2, 'overlap')

    print("Availability corrected successfully!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a message with three inline buttons attached."""
    await update.message.reply_text("Please select a date: ",reply_markup=create_calendar())
    return START_ROUTES

async def process_calendar_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process the callback_query. This method generates a new calendar if forward or
    backward is pressed. This method should be called inside a CallbackQueryHandler.
    """
    ret_data = (False,None)
    query = update.callback_query
    await query.answer()
    (action,year,month,day) = separate_callback_data(query.data)
    curr = datetime.datetime(int(year), int(month), 1)
    if action == "IGNORE":
        #await query.edit_message_text(text='You did not choose the date starting over')
        return IGNORE
        #bot.answer_callback_query(callback_query_id= query.id)
    elif action == "DAY":
        await query.edit_message_text(text=f'You selected: {reform_date(query.data)}.'+' Now choose the time.'
                                      , reply_markup=create_available_time_keyboard(query.data))
        return TIME
    elif action == "PREV-MONTH":
        pre = curr - datetime.timedelta(days=1)
        await query.edit_message_text(text=query.message.text,
                                      reply_markup=create_calendar(int(pre.year),int(pre.month)))
    elif action == "NEXT-MONTH":
        ne = curr + datetime.timedelta(days=31)
        await query.edit_message_text(text=query.message.text,
                                      reply_markup=create_calendar(int(ne.year), int(ne.month)))
    else:
        update.message.reply_text("Something went wrong. Please try to select a date again: ",
                                  reply_markup=create_calendar())
        #bot.answer_callback_query(callback_query_id= query.id,text="Something went wrong!")
        # UNKNOWN

async def process_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'START_OVER':
        await query.edit_message_text(text="Please select another date: ",
                                      reply_markup=create_calendar())
        return DATE
    else:
        await query.edit_message_text(text=f'You selected: {convert_date_string(query.data)}',
                                      reply_markup=confirm_datetime(query.data))
        return CONTACT

async def process_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'START_OVER':
        await query.edit_message_text(text="Please select another date: ",
                                      reply_markup=create_calendar())
        return DATE
    elif query.data == 'CHANGE_TIME':
        await query.edit_message_text(text="Please select another time: ",
                                      reply_markup=create_available_time_keyboard())
        return TIME
    elif query.data == 'CANCEL':
        return IGNORE
    else:
        datetime = query.data
        user = update.effective_user
        correct_availability(datetime[:9],datetime[9:],user.mention_html())
        await query.edit_message_text(f"Thank you, {user.name}! Your booking is finished!")
        return END

async def booking_finished(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="You didn't choose the date. See you next time!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("5939122345:AAE_6pHG2-XW6QSgxzilI-JEm0xr6AWbfbg").build()
    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DATE: [CallbackQueryHandler(process_calendar_selection)],
            TIME: [CallbackQueryHandler(process_time_selection)],
            CONTACT: [CallbackQueryHandler(process_confirmation)],
            #    MessageHandler(filters.LOCATION, location),
            #    CommandHandler("skip", skip_location),
            #],
            IGNORE: [CallbackQueryHandler(end)],
            END: [CallbackQueryHandler(booking_finished)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    json_keyfile = 'C:/Users/gamak/AppData/Roaming/gcloud/fortelegrambot-389309-501cf7aa60ed.json'
    doc_url = 'https://docs.google.com/spreadsheets/d/1DIi0JsdVUXa2UvRw6yoY_oCfzvOL57aSuSd3fZ63kQ0/edit?usp=sharing'
    main()