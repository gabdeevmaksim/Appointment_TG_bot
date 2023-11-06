def list_of_sheets_in_GD(json_keyfile, doc_url):
# json_keyfile - path to json_file
# doc_url - URL of GoogleDoc
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)

    client = gspread.authorize(credentials)

    worksheet_list = client.open_by_url(doc_url).worksheets()

    sheet_names = [worksheet.title for worksheet in worksheet_list]

    return sheet_names

