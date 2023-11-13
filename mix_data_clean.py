import pandas as pd
import os


source_folder = 'D:/Masters/Chris Data Model/MXT Data/Original Data/'
save_folder = 'D:/Masters/Chris Data Model/MXT Data/Cleaned Data/'


csv_files = [file for file in os.listdir(source_folder) if file.endswith('.csv')]

selected_columns = ['Time', 'Latitude', 'Longitude', 'Velocity', 'Altitude', 'Heading']

vehicle_num = 18


for file in csv_files:
    # Construct the full file path
    file_path = os.path.join(source_folder, file)

    # Read the CSV file into a pandas DataFrame
    vehicle_data = pd.read_csv(file_path)

    # Convert the date-time column to datetime format
    vehicle_data['Time'] = pd.to_datetime(vehicle_data['Time'])

    # Extract month and year into separate columns
    vehicle_data['month'] = vehicle_data['Time'].dt.month
    vehicle_data['year'] = vehicle_data['Time'].dt.year

    # Filter the data for the 11th month (November)
    november_data = vehicle_data[vehicle_data['month'] == 11]

    # Iterate through unique years and save November data for each year
    for year in november_data['year'].unique():

        print(f'Saving Vehicle {vehicle_num}')

        year_data = november_data[november_data['year'] == year]

        selected_november_data = year_data[selected_columns]

        # Save the data to a separate CSV file for each year
        output_file_name = f'Vehicle_{vehicle_num}.csv'

        output_file_path = os.path.join(save_folder, output_file_name)
        selected_november_data.to_csv(output_file_path, index=False)

        vehicle_num = vehicle_num + 1
