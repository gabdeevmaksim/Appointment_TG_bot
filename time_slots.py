def create_time_slots_file(filename):
    import csv
    import random

    CSV_FILE = filename + '.csv'

    start_hour = 10
    end_hour = 19

    time_slots = []

    # Iterate through the range of hours
    for hour in range(start_hour, end_hour+1):
        # Add the hour and minute to the list in HH:MM format
        time_slots.append(f'{hour:02}:00')
        time_slots.append(f'{hour:02}:30')

        # Generate random availability for each time slot
    availability_values = ['free' for _ in range(len(time_slots)-1)]

    # Create a list of dictionaries for each row
    rows = [{'time': time, 'Availability': str(availability)} for time, availability in
            zip(time_slots[:-1], availability_values)]

    # Write the data to the CSV file
    with open(CSV_FILE, 'w', newline='') as csvfile:
        fieldnames = ['time', 'Availability']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV file '{CSV_FILE}' has been created with the time slots and availability.")

    return


create_time_slots_file('D20230616')
