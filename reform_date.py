def reform_date(date_string):

    import datetime

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

