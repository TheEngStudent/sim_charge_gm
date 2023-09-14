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
        - Create box plots
        - Plot percentage completion for each N chargers with box plots
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
import natsort

source_folder = 'D:/Masters/Simulations/Simulation_2/Outputs/' 
plt.rcParams['figure.dpi'] = 600

### Prepare for plotting
integer_list = list(range(0, 1440))
timedelta_index = pd.to_timedelta(integer_list, unit='m')
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

# TODO change for other scenarios
total_vehicle_days = 222
positive_vehicle_days = [54, 93, 112, 120, 121, 122, 122]
positive_vehicle_days_true = [157, 170, 175, 175, 175, 175, 175]



####################################################################################################
################################## Home Charging = False ###########################################
################################ First: Minimum and Maximum ########################################
####################################################################################################

print('No Home Charging Scenarios')

sce_folders = glob.glob(os.path.join(source_folder, 'SCE*False'))

all_day_vehicle_min = []
all_day_sums_min = []

for sce_folder in sce_folders:

    day_subfolders = glob.glob(os.path.join(sce_folder, 'Day*'))
    sce_folder_name = os.path.basename(sce_folder)

    print(sce_folder_name)

    all_grid_vehicle_min = []
    all_grid_sums_min = []

    for day_subfolder in day_subfolders:

        # Find the last iteration subfolder
        iteration_subfolders = natsort.natsorted(glob.glob(os.path.join(day_subfolder, 'Iteration*')))
        last_iteration_folder = iteration_subfolders[-1]

        # Read the 'grid_power' file from each Day subfolder
        grid_power_file = os.path.join(last_iteration_folder, 'grid_power.csv')
        soc_file = os.path.join(last_iteration_folder, 'soc.csv')

        # Perform your file-reading operations on grid_power_file here
        grid_power = pd.read_csv(grid_power_file)
        soc_data = pd.read_csv(soc_file)

        total_active_vehicles = (soc_data.iloc[-1] != 0).sum()

        grid_sums = grid_power.sum(axis=1)
        grid_sums = grid_sums / 1000

        grid_vehicle = grid_sums / total_active_vehicles
        
        all_grid_vehicle_min.append(grid_vehicle)
        all_grid_sums_min.append(grid_sums)

    ### Matrix of 1440x17 created
    # Per vehicle
    result_matrix_vehicle = pd.concat(all_grid_vehicle_min, axis=1)
    na_column_indices = result_matrix_vehicle.columns[result_matrix_vehicle.isna().any()]

    result_matrix_vehicle = result_matrix_vehicle.dropna(axis=1)
 
    max_values_array_vehicle = result_matrix_vehicle.max(axis=1).values
    min_values_array_vehicle = result_matrix_vehicle.min(axis=1).values
    avg_values_array_vehicle = result_matrix_vehicle.mean(axis=1).values

    max_day_array_vehicles = result_matrix_vehicle.max().values

    # Per day
    result_matrix_sums = pd.concat(all_grid_sums_min, axis=1)
    result_matrix_sums = result_matrix_sums.drop(na_column_indices, axis=1)
 
    max_values_array_sums = result_matrix_sums.max(axis=1).values
    min_values_array_sums = result_matrix_sums.min(axis=1).values
    avg_values_array_sums = result_matrix_sums.mean(axis=1).values

    max_day_array_sums = result_matrix_sums.max().values



    all_day_vehicle_min.append(max_day_array_vehicles)
    all_day_sums_min.append(max_day_array_sums)

    print('Saving Graphs')

    ### Plot information for per vehicle data
    plt.figure()

    plt.plot(timedelta_index, avg_values_array_vehicle, label = 'Average Power per Vehicle', color='#2D71E6')

    plt.xticks(rotation=45)

    plt.fill_between(timedelta_index, min_values_array_vehicle, max_values_array_vehicle, alpha=0.3, color='#ADD8E6', edgecolor='none')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.ylim(0, 30)
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

    ### Plot information for overall
    plt.figure()

    plt.plot(timedelta_index, avg_values_array_sums, label = 'Average Power', color='#2D71E6')

    plt.xticks(rotation=45)

    plt.fill_between(timedelta_index, min_values_array_sums, max_values_array_sums, alpha=0.3, color='#ADD8E6', edgecolor='none')

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

print('Creating Box Plots')

all_day_vehicle_min = pd.DataFrame(all_day_vehicle_min)
all_day_sums_min = pd.DataFrame(all_day_sums_min)

result_box_plot_vehicle = all_day_vehicle_min.T
result_box_plot_sums = all_day_sums_min.T

plt.figure()

fig, ax1 = plt.subplots()

box = plt.boxplot(result_box_plot_sums, patch_artist=True, showfliers=False)
for patch in box['boxes']:
    patch.set_facecolor('#FFE6B9')

# Add labels and title
ax1.set_xlabel('Number of Chargers')
ax1.set_ylabel('Grid Power [kW]')
ax1.set_title('Maximum Grid Power per Scenario (HC = False)')

ax1.set_ylim(0, 170)

# Calculate percentage completion
percentages = [day / total_vehicle_days * 100 for day in positive_vehicle_days]

# Create a twin y-axis for percentages
ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Completion')

ax2.set_ylim(0, 100)

# Plot percentages behind the box plots
ax2.plot(range(1, len(percentages) + 1), percentages, linestyle='-', label='Percentage Completion', color='#2D71E6')
ax2.fill_between(range(1, len(percentages) + 1), percentages, 0, alpha=0.2, color='#ADD8E6', edgecolor='none')

# Show the plot
plt.tight_layout()
save_path = source_folder + '/Grid_Power_Box_Plot_HC_False.png'
plt.savefig(save_path)
save_path = source_folder + '/Grid_Power_Box_Plot_HC_False.svg'
plt.savefig(save_path, format='svg')

plt.close()


plt.figure()

fig, ax1 = plt.subplots()

box = plt.boxplot(result_box_plot_vehicle, patch_artist=True, showfliers=False)
for patch in box['boxes']:
    patch.set_facecolor('#FFE6B9')

# Add labels and title
ax1.set_xlabel('Number of Chargers')
ax1.set_ylabel('Grid Power [kW]')
ax1.set_title('Maximum Grid Power per Vehicle per Scenario (HC = False)')

ax1.set_ylim(0, 25)

# Calculate percentage completion
percentages = [day / total_vehicle_days * 100 for day in positive_vehicle_days]

# Create a twin y-axis for percentages
ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Completion')

ax2.set_ylim(0, 100)

# Plot percentages behind the box plots
ax2.plot(range(1, len(percentages) + 1), percentages, linestyle='-', label='Percentage Completion', color='#2D71E6')
ax2.fill_between(range(1, len(percentages) + 1), percentages, 0, alpha=0.2, color='#ADD8E6', edgecolor='none')

# Show the plot
plt.tight_layout()
save_path = source_folder + '/Grid_Power_Vehicle_Box_Plot_HC_False.png'
plt.savefig(save_path)
save_path = source_folder + '/Grid_Power_Vehicle_Box_Plot_HC_False.svg'
plt.savefig(save_path, format='svg')

plt.close()

        


####################################################################################################
################################## Home Charging = True ############################################
################################ First: Minimum and Maximum ########################################
####################################################################################################

print('Home Charging Scenarios')

sce_folders = glob.glob(os.path.join(source_folder, 'SCE*True'))

all_day_vehicle_min = []
all_day_sums_min = []

all_day_vehicle_min_d = []
all_day_sums_min_d = []

all_day_vehicle_min_hc = []
all_day_sums_min_hc = []

for sce_folder in sce_folders:

    day_subfolders = glob.glob(os.path.join(sce_folder, 'Day*'))
    sce_folder_name = os.path.basename(sce_folder)

    print(sce_folder_name)

    all_grid_vehicle_min = []
    all_grid_sums_min = []

    all_grid_vehicle_min_d = []
    all_grid_sums_min_d = []

    all_grid_vehicle_min_hc = []
    all_grid_sums_min_hc = []

    for day_subfolder in day_subfolders:

        # Find the last iteration subfolder
        iteration_subfolders = natsort.natsorted(glob.glob(os.path.join(day_subfolder, 'Iteration*')))
        last_iteration_folder = iteration_subfolders[-1]

        # Read the 'grid_power' file from each Day subfolder
        grid_power_file = os.path.join(last_iteration_folder, 'grid_power.csv')
        soc_file = os.path.join(last_iteration_folder, 'soc.csv')
        cf_file = os.path.join(last_iteration_folder, 'charging_variable.csv')

        # Perform your file-reading operations on grid_power_file here
        grid_power = pd.read_csv(grid_power_file)
        soc_data = pd.read_csv(soc_file)
        cf_data = pd.read_csv(cf_file)

        total_active_vehicles = (soc_data.iloc[-1] != 0).sum()
        

        ### Overall grid power
        grid_sums = grid_power.sum(axis=1)
        grid_sums = grid_sums / 1000
        
        grid_vehicle = grid_sums / total_active_vehicles

        all_grid_vehicle_min.append(grid_vehicle)
        all_grid_sums_min.append(grid_sums)

        ### Just Depot grid power
        d_mask = cf_data.eq(1).astype(int)

        grid_power_d = d_mask * grid_power

        grid_sums_d = grid_power_d.sum(axis=1)
        grid_sums_d = grid_sums_d / 1000
        
        grid_vehicle_d = grid_sums_d / total_active_vehicles

        all_grid_vehicle_min_d.append(grid_vehicle_d)
        all_grid_sums_min_d.append(grid_sums_d)


        ### Just Home Charging grid power
        hc_mask = cf_data.eq(-1).astype(int)

        grid_power_hc = hc_mask * grid_power

        grid_sums_hc = grid_power_hc.sum(axis=1)
        grid_sums_hc = grid_sums_hc / 1000
        
        grid_vehicle_hc = grid_sums_hc / total_active_vehicles

        all_grid_vehicle_min_hc.append(grid_vehicle_hc)
        all_grid_sums_min_hc.append(grid_sums_hc)



    #################################### Overall grid power ######################################
    ### Matrix of 1440x17 created
    # Per vehicle
    result_matrix_vehicle = pd.concat(all_grid_vehicle_min, axis=1)
    na_column_indices = result_matrix_vehicle.columns[result_matrix_vehicle.isna().any()]

    result_matrix_vehicle = result_matrix_vehicle.dropna(axis=1)
 
    max_values_array_vehicle = result_matrix_vehicle.max(axis=1).values
    min_values_array_vehicle = result_matrix_vehicle.min(axis=1).values
    avg_values_array_vehicle = result_matrix_vehicle.mean(axis=1).values

    max_day_array_vehicles = result_matrix_vehicle.max().values

    # Per day
    result_matrix_sums = pd.concat(all_grid_sums_min, axis=1)
    result_matrix_sums = result_matrix_sums.drop(na_column_indices, axis=1)
 
    max_values_array_sums = result_matrix_sums.max(axis=1).values
    min_values_array_sums = result_matrix_sums.min(axis=1).values
    avg_values_array_sums = result_matrix_sums.mean(axis=1).values

    max_day_array_sums = result_matrix_sums.max().values

    all_day_vehicle_min.append(max_day_array_vehicles)
    all_day_sums_min.append(max_day_array_sums)

    print('Saving Graphs')

    ### Plot information for per vehicle data
    plt.figure()

    plt.plot(timedelta_index, avg_values_array_vehicle, label = 'Overall Average Power per Vehicle', color='#2D71E6')

    plt.xticks(rotation=45)

    plt.fill_between(timedelta_index, min_values_array_vehicle, max_values_array_vehicle, alpha=0.3, color='#ADD8E6', edgecolor='none')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.ylim(0, 30)
    plt.xlabel('Time of Day')
    plt.ylabel('Grid Power [kW]')
    plt.title('Maximum and Minimum Grid Power per Vehicle')
    plt.legend()

    plt.subplots_adjust(bottom = 0.2)

    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Vehicle_Overall.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Vehicle_Overall.svg'
    plt.savefig(save_path, format = 'svg')

    plt.close()

    ### Plot information for overall
    plt.figure()

    plt.plot(timedelta_index, avg_values_array_sums, label = 'Overall Average Power', color='#2D71E6')

    plt.xticks(rotation=45)

    plt.fill_between(timedelta_index, min_values_array_sums, max_values_array_sums, alpha=0.3, color='#ADD8E6', edgecolor='none')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.ylim(0, 170)
    plt.xlabel('Time of Day')
    plt.ylabel('Grid Power [kW]')
    plt.title('Maximum and Minimum Grid Power')
    plt.legend()

    plt.subplots_adjust(bottom = 0.2)

    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Overall.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Overall.svg'
    plt.savefig(save_path, format = 'svg')

    plt.close()



    ############################## Depot vs Home Charging grid power ###############################
    ### Matrix of 1440x17 created
    # Per vehicle
    result_matrix_vehicle_d = pd.concat(all_grid_vehicle_min_d, axis=1)
    result_matrix_vehicle_hc = pd.concat(all_grid_vehicle_min_hc, axis=1)

    result_matrix_vehicle_d = result_matrix_vehicle_d.dropna(axis=1)
    result_matrix_vehicle_hc = result_matrix_vehicle_hc.dropna(axis=1)
 
    max_values_array_vehicle_d = result_matrix_vehicle_d.max(axis=1).values
    min_values_array_vehicle_d = result_matrix_vehicle_d.min(axis=1).values
    avg_values_array_vehicle_d = result_matrix_vehicle_d.mean(axis=1).values

    max_values_array_vehicle_hc = result_matrix_vehicle_hc.max(axis=1).values
    min_values_array_vehicle_hc = result_matrix_vehicle_hc.min(axis=1).values
    avg_values_array_vehicle_hc = result_matrix_vehicle_hc.mean(axis=1).values

    max_day_array_vehicles_d = result_matrix_vehicle_d.max().values
    max_day_array_vehicles_hc = result_matrix_vehicle_hc.max().values

    # Per day
    result_matrix_sums_d = pd.concat(all_grid_sums_min_d, axis=1)
    result_matrix_sums_hc = pd.concat(all_grid_sums_min_hc, axis=1)

    result_matrix_sums_d = result_matrix_sums_d.drop(na_column_indices, axis=1)
    result_matrix_sums_hc = result_matrix_sums_hc.drop(na_column_indices, axis=1)
 
    max_values_array_sums_d = result_matrix_sums_d.max(axis=1).values
    min_values_array_sums_d = result_matrix_sums_d.min(axis=1).values
    avg_values_array_sums_d = result_matrix_sums_d.mean(axis=1).values

    max_values_array_sums_hc = result_matrix_sums_hc.max(axis=1).values
    min_values_array_sums_hc = result_matrix_sums_hc.min(axis=1).values
    avg_values_array_sums_hc = result_matrix_sums_hc.mean(axis=1).values

    max_day_array_sums_d = result_matrix_sums_d.max().values
    max_day_array_sums_hc = result_matrix_sums_hc.max().values

    all_day_vehicle_min_d.append(max_day_array_vehicles_d)
    all_day_sums_min_d.append(max_day_array_sums_d)

    all_day_vehicle_min_hc.append(max_day_array_vehicles_hc)
    all_day_sums_min_hc.append(max_day_array_sums_hc)

    print('Saving Graphs')

    ### Plot information for per vehicle data
    plt.figure()

    plt.plot(timedelta_index, avg_values_array_vehicle_d, label = 'Average Power per Vehicle - Depot Charging', color='#2D71E6')
    plt.plot(timedelta_index, avg_values_array_vehicle_hc, label = 'Average Power per Vehicle - Home Charging', color='#CB2D2D')

    plt.xticks(rotation=45)

    plt.fill_between(timedelta_index, min_values_array_vehicle_d, max_values_array_vehicle_d, alpha=0.3, color='#ADD8E6', edgecolor='none')
    plt.fill_between(timedelta_index, min_values_array_vehicle_hc, max_values_array_vehicle_hc, alpha=0.3, color='#FFB9B9', edgecolor='none')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.ylim(0, 30)
    plt.xlabel('Time of Day')
    plt.ylabel('Grid Power [kW]')
    plt.title('Maximum and Minimum Grid Power per Vehicle')
    plt.legend()

    plt.subplots_adjust(bottom = 0.2)

    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Vehicle_Separate.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Vehicle_Separate.svg'
    plt.savefig(save_path, format = 'svg')

    plt.close()

    ### Plot information for overall
    plt.figure()

    plt.plot(timedelta_index, avg_values_array_sums_d, label = 'Average Power - Depot Charging', color='#2D71E6')
    plt.plot(timedelta_index, avg_values_array_sums_hc, label = 'Average Power - Home Charging', color='#CB2D2D')

    plt.xticks(rotation=45)

    plt.fill_between(timedelta_index, min_values_array_sums_d, max_values_array_sums_d, alpha=0.3, color='#ADD8E6', edgecolor='none')
    plt.fill_between(timedelta_index, min_values_array_sums_hc, max_values_array_sums_hc, alpha=0.3, color='#FFB9B9', edgecolor='none')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.ylim(0, 170)
    plt.xlabel('Time of Day')
    plt.ylabel('Grid Power [kW]')
    plt.title('Maximum and Minimum Grid Power')
    plt.legend()

    plt.subplots_adjust(bottom = 0.2)

    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Separate.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = source_folder + '/' + sce_folder_name + '/Max_Min_Grid_Power_Separate.svg'
    plt.savefig(save_path, format = 'svg')

    plt.close()

################################### Overall #######################################
print('Creating Box Plots - Overall')

all_day_vehicle_min = pd.DataFrame(all_day_vehicle_min)
all_day_sums_min = pd.DataFrame(all_day_sums_min)

result_box_plot_vehicle = all_day_vehicle_min.T
result_box_plot_sums = all_day_sums_min.T

plt.figure()

fig, ax1 = plt.subplots()

box = plt.boxplot(result_box_plot_sums, patch_artist=True, showfliers=False)
for patch in box['boxes']:
    patch.set_facecolor('#FFE6B9')

# Add labels and title
ax1.set_xlabel('Number of Chargers')
ax1.set_ylabel('Grid Power [kW]')
ax1.set_title('Maximum Grid Power per Scenario (HC = True)')

ax1.set_ylim(0, 170)

# Calculate percentage completion
percentages = [day / total_vehicle_days * 100 for day in positive_vehicle_days_true]

# Create a twin y-axis for percentages
ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Completion')

ax2.set_ylim(0, 100)

# Plot percentages behind the box plots
ax2.plot(range(1, len(percentages) + 1), percentages, linestyle='-', label='Percentage Completion', color='#2D71E6')
ax2.fill_between(range(1, len(percentages) + 1), percentages, 0, alpha=0.2, color='#ADD8E6')

# Show the plot
plt.tight_layout()
save_path = source_folder + '/Grid_Power_Box_Plot_HC_True_Overall.png'
plt.savefig(save_path)
save_path = source_folder + '/Grid_Power_Box_Plot_HC_True_Overall.svg'
plt.savefig(save_path, format='svg')

plt.close()


plt.figure()

fig, ax1 = plt.subplots()

box = plt.boxplot(result_box_plot_vehicle, patch_artist=True, showfliers=False)
for patch in box['boxes']:
    patch.set_facecolor('#FFE6B9')

# Add labels and title
ax1.set_xlabel('Number of Chargers')
ax1.set_ylabel('Grid Power [kW]')
ax1.set_title('Maximum Grid Power per Vehicle per Scenario (HC = True)')

ax1.set_ylim(0, 25)

# Calculate percentage completion
percentages = [day / total_vehicle_days * 100 for day in positive_vehicle_days_true]

# Create a twin y-axis for percentages
ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Completion')

ax2.set_ylim(0, 100)

# Plot percentages behind the box plots
ax2.plot(range(1, len(percentages) + 1), percentages, linestyle='-', label='Percentage Completion', color='#2D71E6')
ax2.fill_between(range(1, len(percentages) + 1), percentages, 0, alpha=0.2, color='#ADD8E6')

# Show the plot
plt.tight_layout()
save_path = source_folder + '/Grid_Power_Vehicle_Box_Plot_HC_True_Overall.png'
plt.savefig(save_path)
save_path = source_folder + '/Grid_Power_Vehicle_Box_Plot_HC_True_Overall.svg'
plt.savefig(save_path, format='svg')

plt.close()


################################### Depot Charging #######################################
print('Creating Box Plots - Depot Charging')

all_day_vehicle_min_d = pd.DataFrame(all_day_vehicle_min_d)
all_day_sums_min_d = pd.DataFrame(all_day_sums_min_d)

result_box_plot_vehicle_d = all_day_vehicle_min_d.T
result_box_plot_sums_d = all_day_sums_min_d.T

plt.figure()

fig, ax1 = plt.subplots()

box = plt.boxplot(result_box_plot_sums_d, patch_artist=True, showfliers=False)
for patch in box['boxes']:
    patch.set_facecolor('#FFE6B9')

# Add labels and title
ax1.set_xlabel('Number of Chargers')
ax1.set_ylabel('Grid Power [kW]')
ax1.set_title('Maximum Depot Grid Power per Scenario (HC = True)')

ax1.set_ylim(0, 170)

# Calculate percentage completion
percentages = [day / total_vehicle_days * 100 for day in positive_vehicle_days_true]

# Create a twin y-axis for percentages
ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Completion')

ax2.set_ylim(0, 100)

# Plot percentages behind the box plots
ax2.plot(range(1, len(percentages) + 1), percentages, linestyle='-', label='Percentage Completion', color='#2D71E6')
ax2.fill_between(range(1, len(percentages) + 1), percentages, 0, alpha=0.2, color='#ADD8E6')

# Show the plot
plt.tight_layout()
save_path = source_folder + '/Grid_Power_Box_Plot_HC_True_Depot.png'
plt.savefig(save_path)
save_path = source_folder + '/Grid_Power_Box_Plot_HC_True_Depot.svg'
plt.savefig(save_path, format='svg')

plt.close()


plt.figure()

fig, ax1 = plt.subplots()

box = plt.boxplot(result_box_plot_vehicle_d, patch_artist=True, showfliers=False)
for patch in box['boxes']:
    patch.set_facecolor('#FFE6B9')

# Add labels and title
ax1.set_xlabel('Number of Chargers')
ax1.set_ylabel('Grid Power [kW]')
ax1.set_title('Maximum Depot Grid Power per Vehicle per Scenario (HC = True)')

ax1.set_ylim(0, 25)

# Calculate percentage completion
percentages = [day / total_vehicle_days * 100 for day in positive_vehicle_days_true]

# Create a twin y-axis for percentages
ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Completion')

ax2.set_ylim(0, 100)

# Plot percentages behind the box plots
ax2.plot(range(1, len(percentages) + 1), percentages, linestyle='-', label='Percentage Completion', color='#2D71E6')
ax2.fill_between(range(1, len(percentages) + 1), percentages, 0, alpha=0.2, color='#ADD8E6')

# Show the plot
plt.tight_layout()
save_path = source_folder + '/Grid_Power_Vehicle_Box_Plot_HC_True_Depot.png'
plt.savefig(save_path)
save_path = source_folder + '/Grid_Power_Vehicle_Box_Plot_HC_True_Depot.svg'
plt.savefig(save_path, format='svg')

plt.close()

################################### Home Charging #######################################
print('Creating Box Plots - Home Charging')

all_day_vehicle_min_hc = pd.DataFrame(all_day_vehicle_min_hc)
all_day_sums_min_hc = pd.DataFrame(all_day_sums_min_hc)

result_box_plot_vehicle_hc = all_day_vehicle_min_hc.T
result_box_plot_sums_hc = all_day_sums_min_hc.T

plt.figure()

fig, ax1 = plt.subplots()

box = plt.boxplot(result_box_plot_sums_hc, patch_artist=True, showfliers=False)
for patch in box['boxes']:
    patch.set_facecolor('#FFE6B9')

# Add labels and title
ax1.set_xlabel('Number of Chargers')
ax1.set_ylabel('Grid Power [kW]')
ax1.set_title('Maximum Home Grid Power per Scenario (HC = True)')

ax1.set_ylim(0, 170)

# Calculate percentage completion
percentages = [day / total_vehicle_days * 100 for day in positive_vehicle_days_true]

# Create a twin y-axis for percentages
ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Completion')

ax2.set_ylim(0, 100)

# Plot percentages behind the box plots
ax2.plot(range(1, len(percentages) + 1), percentages, linestyle='-', label='Percentage Completion', color='#2D71E6')
ax2.fill_between(range(1, len(percentages) + 1), percentages, 0, alpha=0.2, color='#ADD8E6')

# Show the plot
plt.tight_layout()
save_path = source_folder + '/Grid_Power_Box_Plot_HC_True_Home.png'
plt.savefig(save_path)
save_path = source_folder + '/Grid_Power_Box_Plot_HC_True_Home.svg'
plt.savefig(save_path, format='svg')

plt.close()


plt.figure()

fig, ax1 = plt.subplots()

box = plt.boxplot(result_box_plot_vehicle_hc, patch_artist=True, showfliers=False)
for patch in box['boxes']:
    patch.set_facecolor('#FFE6B9')

# Add labels and title
ax1.set_xlabel('Number of Chargers')
ax1.set_ylabel('Grid Power [kW]')
ax1.set_title('Maximum Home Grid Power per Vehicle per Scenario (HC = True)')

ax1.set_ylim(0, 25)

# Calculate percentage completion
percentages = [day / total_vehicle_days * 100 for day in positive_vehicle_days_true]

# Create a twin y-axis for percentages
ax2 = ax1.twinx()
ax2.set_ylabel('Percentage Completion')

ax2.set_ylim(0, 100)

# Plot percentages behind the box plots
ax2.plot(range(1, len(percentages) + 1), percentages, linestyle='-', label='Percentage Completion', color='#2D71E6')
ax2.fill_between(range(1, len(percentages) + 1), percentages, 0, alpha=0.2, color='#ADD8E6')

# Show the plot
plt.tight_layout()
save_path = source_folder + '/Grid_Power_Vehicle_Box_Plot_HC_True_Home.png'
plt.savefig(save_path)
save_path = source_folder + '/Grid_Power_Vehicle_Box_Plot_HC_True_Home.svg'
plt.savefig(save_path, format='svg')

plt.close()

    


"""

####################################################################################################
################################## Home Charging = False ###########################################
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

"""