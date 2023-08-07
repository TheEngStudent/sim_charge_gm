############################## Read Me ####################################
"""
This program reads the gid power data from the different scenarios and
performs various plotting functions on it. The program does the followinf 
tasks:
    First:
        - Find the minimum power for the hour of each day
        - Find the maximum power for the hour for each day
        - Find the average power for the hour over all the days
        - Plot this on one graph and fill the gap as an area
        - This is combined grid power
    Second:
        - Find the maximum power in each day
        - Plot according to number of chargers
    Third:
        - Split the power graphs according to depot charging and home charging
        - Plot on the same graph with different colours
        - The same is done as in first
"""

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import re
import matplotlib.dates as mdates
import numpy as np

source_folder = 'D:/Masters/Simulations/Simulation_2/Outputs/' 

### Important to note that this is purely done for no Home Charging

####################################################################################################
################################ First: Minimum and Maximum ########################################
###################################################################################################

### Prepare for plotting
integer_list = list(range(0, 86400))
timedelta_index = pd.to_timedelta(integer_list, unit='s')
base_date = pd.to_datetime('04:00:00')
timedelta_index = base_date + timedelta_index
# List to store the corresponding SCE folder names
sce_folder_names = []
# List to keep track of whether we have added the legend entry for each SCE folder
legend_added = []
# Create a list of markers to cycle through for different SCE folders
colour_list = [ '#d9ff00',
                '#00ffd5',
                '#00ff15',
                '#f2ff00',
                '#0019ff',
                '#ffea00',
                '#ff2f00'
             ]

plt.rcParams['figure.dpi'] = 600

sce_folders = glob.glob(os.path.join(source_folder, 'SCE*False'))

for sce_folder in sce_folders:

    day_subfolders = glob.glob(os.path.join(sce_folder, 'Day*'))
    sce_folder_name = os.path.basename(sce_folder)

    avg_values_per_hour_dict = {}
    hourly_values_dict = {}
    avg_values_per_hour_dict_vehicle = {}
    hourly_values_dict_vehicle = {}

    max_hourly_data = []
    min_hourly_data = []

    for day_subfolder in day_subfolders:
        # Read the 'grid_power' file from each Day subfolder
        grid_power_file = os.path.join(day_subfolder, 'grid_power.csv')

        # Perform your file-reading operations on grid_power_file here
        grid_power = pd.read_csv(grid_power_file)

        grid_sums = grid_power.sum(axis=1)
        grid_sums = grid_sums / 1000
        grid_vehicle = grid_sums / len(grid_power.columns)

        for i in range(24):
            
            if i not in avg_values_per_hour_dict:
                avg_values_per_hour_dict[i] = []
                hourly_values_dict[i] = []
                avg_values_per_hour_dict_vehicle[i] = []
                hourly_values_dict_vehicle[i] = []

            hourly_data = grid_sums[i*3600 : (i+1)*3600]
            hourly_data_vehicle = grid_vehicle[i*3600 : (i+1)*3600]

            avg_value = sum(hourly_data) / len(hourly_data)
            avg_value_vehicle = sum(hourly_data_vehicle) / len(hourly_data_vehicle)

            avg_values_per_hour_dict[i].append(avg_value)
            hourly_values_dict[i].append(hourly_data)
            avg_values_per_hour_dict_vehicle[i].append(avg_value_vehicle)
            hourly_values_dict_vehicle[i].append(hourly_data_vehicle)


    # Find where the minimum and maximum locations are
    for key, value_list in avg_values_per_hour_dict.items():
        # Use the index() method to find the location (index) of the minimum value in the list
        min_location = value_list.index(min(value_list))

        min_hourly_data.extend(hourly_values_dict[key][min_location])

        max_location = value_list.index(max(value_list))

        max_hourly_data.extend(hourly_values_dict[key][max_location])


    # Plot information
    plt.figure()
    plt.plot(timedelta_index, min_hourly_data, label = 'Minimum Power')
    plt.plot(timedelta_index, max_hourly_data, label = 'Maximum Power')

    plt.xticks(rotation=45)

    plt.fill_between(timedelta_index, min_hourly_data, max_hourly_data, alpha=0.3)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.ylim(0, 170)
    plt.xlabel('Time of Day')
    plt.ylabel('Grid Power [kW]')
    plt.title('Maximum and Minimum Grid Power')
    plt.legend()

    plt.subplots_adjust(bottom = 0.2)

    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power.svg'
    plt.savefig(save_path, format = 'svg')

    plt.close()

    max_hourly_data = []
    min_hourly_data = []

    # Find where the minimum and maximum locations are
    for key, value_list in avg_values_per_hour_dict_vehicle.items():
        # Use the index() method to find the location (index) of the minimum value in the list
        min_location = value_list.index(min(value_list))

        min_hourly_data.extend(hourly_values_dict_vehicle[key][min_location])

        max_location = value_list.index(max(value_list))

        max_hourly_data.extend(hourly_values_dict_vehicle[key][max_location])


    # Plot information
    plt.figure()
    plt.plot(timedelta_index, min_hourly_data, label = 'Minimum Power per Vehicle')
    plt.plot(timedelta_index, max_hourly_data, label = 'Maximum Power per Vehicle')

    plt.xticks(rotation=45)

    plt.fill_between(timedelta_index, min_hourly_data, max_hourly_data, alpha=0.3)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.ylim(0, 20)
    plt.xlabel('Time of Day')
    plt.ylabel('Grid Power [kW]')
    plt.title('Maximum and Minimum Grid Power per Vehicle')
    plt.legend()

    plt.subplots_adjust(bottom = 0.2)

    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Vehicle.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Vehicle.svg'
    plt.savefig(save_path, format = 'svg')

    plt.close()
        






    




####################################################################################################
####################### Second: Maximum Power vs Number of Chargers ################################
####################################################################################################


sce_folders = glob.glob(os.path.join(source_folder, 'SCE*False'))

# Create a dictionary to store the maximum values for each day, using day as keys
max_values_per_day_dict = {}
# List to store the corresponding SCE folder names
sce_folder_names = []
# List to keep track of whether we have added the legend entry for each SCE folder
legend_added = []
# Create a list of markers to cycle through for different SCE folders
markers = ['o', 's', '^', 'd', '*', 'x', '+']
colour_list = [ '#d9ff00',
                '#00ffd5',
                '#00ff15',
                '#f2ff00',
                '#0019ff',
                '#ffea00',
                '#ff2f00'
             ]

for sce_folder in sce_folders:

    day_subfolders = glob.glob(os.path.join(sce_folder, 'Day*'))

    for day_subfolder in day_subfolders:
        # Read the 'grid_power' file from each Day subfolder
        grid_power_file = os.path.join(day_subfolder, 'grid_power.csv')

        # Perform your file-reading operations on grid_power_file here
        grid_power = pd.read_csv(grid_power_file)

        grid_sums = grid_power.sum(axis=1)
        grid_sums = grid_sums / 1000

        # Find the maximum value for each day
        max_value = grid_sums.max()

        # Get the day from the subfolder name
        day = os.path.basename(day_subfolder)[4:]  # Assuming the day information starts from the fourth character

        # Add the maximum value to the dictionary using day as the key
        if day not in max_values_per_day_dict:
            max_values_per_day_dict[day] = []
        max_values_per_day_dict[day].append(max_value)

    # Get the SCE folder name using regex (extract 'N*' part)
    sce_folder_name = re.search(r'N(\d+)', os.path.basename(sce_folder)).group(0)
    # Append the SCE folder name to the list
    sce_folder_names.append(sce_folder_name)

    

# Plotting all the maximum values on one graph with different markers for each SCE folder
plt.figure(figsize=(10, 6))  # Adjust the figure size if needed

for i, (day, max_values) in enumerate(max_values_per_day_dict.items()):
    # Plot the maximum values for each day with a different marker
    k = 0
    for max_value in max_values:
        plt.scatter(day, max_value, marker=markers[k], c=colour_list[k])
        k = k + 1

plt.xlabel('Day')
plt.ylabel('Maximum Grid Power [kW]')
plt.title('Maximum Grid Power for Different Number of Chargers')
plt.ylim(0, 170)
plt.legend(sce_folder_names)

save_path = source_folder + 'Maximum_Power_Chargers.png'
plt.savefig(save_path)
# Save the plot to a specific location as a svg
save_path = source_folder + 'Maximum_Power_Chargers.svg'
plt.savefig(save_path, format = 'svg')
plt.close()