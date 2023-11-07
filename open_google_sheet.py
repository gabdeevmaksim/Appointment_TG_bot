def open_google_sheet(json_keyfile, doc_url, sheet_name):
#json_keyfile - path to json_file
#doc_url - URL of GoogleDoc
#sheet - name of sheet


    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)

    client = gspread.authorize(credentials)

    sheet = client.open_by_url(doc_url).worksheet(sheet_name)

    data_fr_sheet = sheet.get_all_records()

    return data_fr_sheet
