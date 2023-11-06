def add_sheet(sheetname):

    # Load credentials and authorize the client
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(credentials)

    # Open the Google Sheets document
    spreadsheet = client.open_by_url(doc_url)

    # Create a new sheet with a specific name
    new_sheet_name = sheetname
    new_sheet = spreadsheet.add_worksheet(title=new_sheet_name, rows="100", cols="2")

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
