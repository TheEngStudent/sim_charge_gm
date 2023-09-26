################################ Read Me #######################################
"""
This program creates the results after sim_charge has completed its simulations.
It does it for the scenario where Home Charging is false and for the scenario
where Home Charging is true. It needs to be done seperately as the results are
completely different.
    False   - A histogram is plotted for the total number of iterations it took
            for the simulation to reach steady state. The number of iteratioons
            is placed on the x-axis and the count is placed on the y-axis. The 
            total is also printed out. The positive steady state is given above
            the x-axis and the results where the steady state was zero are given
            below the x-axis
            - The second plot distinguishes the distances that resulted in a 
            positive steady and a steady state that was zero
"""


import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import re
import matplotlib.dates as mdates
import numpy as np

source_folder = 'D:/Masters/Simulations/Simulation_2/Outputs/Uncontrolled_Charging/'
#source_folder = 'D:/Masters/Simulations/Simulation_2/Outputs/Smart_Charging_1/' 
num_vehicles = 17
save_common = 'Day_'
days = [str(num).zfill(2) for num in range(1, 32)]  # Days in the month

plt.rcParams['figure.dpi'] = 600


#################################################################################################################
################################## Distance and Steady State Reached ############################################
#################################################################################################################

print('Results - No Home Charging')

sce_folders = glob.glob(os.path.join(source_folder, 'SCE*'))

### For each SCE folder that has HC = False
for sce_folder in sce_folders:

    positive_steady_state = 0
    positive_steady_state_oscilation = 0
    zero_steady_state_battery = 0
    zero_steady_state_chargers = 0

    postive_distances = []
    postive_distances_oscilation = []
    zero_distances_battery = []
    zero_distances_chargers = []

    total_vehicle_days = 0

    day_subfolders = glob.glob(os.path.join(sce_folder, 'Day*'))
    sce_folder_name = os.path.basename(sce_folder)

    print(sce_folder_name)

    ### For each day folder in the SCE folder
    for day_folder in day_subfolders:

        day_folder_name = os.path.basename(day_folder)
        iteration_subfolders = sorted(glob.glob(os.path.join(day_folder, 'Iteration*')), key=lambda x: int(x.split('_')[-1]))

        vehicle_steady_state = {'Vehicle_' + str(i): False for i in range(1, num_vehicles + 1)}
        vehicle_zero_steady_state = {'Vehicle_' + str(i): False for i in range(1, num_vehicles + 1)}
        vehicle_iteration_steady_state = {'Vehicle_' + str(i): False for i in range(1, num_vehicles + 1)}
        
        ### For each iteration in the day folder
        for iteration_folder in iteration_subfolders:

            iteration_folder_name = os.path.basename(iteration_folder)
            iteration_number = int(iteration_folder_name.split('_')[-1])
            
            soc_file_path = os.path.join(iteration_folder, 'soc.csv')
            dis_file_path = os.path.join(iteration_folder, 'distance.csv')

            soc_dataframe = pd.read_csv(soc_file_path)
            dis_dataframe = pd.read_csv(dis_file_path)


            ### Determine if steady state is reached
            if iteration_number == 1:
                steady_state_soc = pd.DataFrame(100, index = [1], columns=soc_dataframe.columns)
            if iteration_number == 2:
                columns_with_zero = soc_dataframe.columns[(soc_dataframe.iloc[0] == 0) & (soc_dataframe.iloc[-1] == 0)].tolist()

                for col in columns_with_zero:
                    vehicle_zero_steady_state[col] = True

            steady_state_soc = steady_state_soc.append(soc_dataframe.iloc[-1], ignore_index=True)

        # Only evaluating on the last iteration because that is when everything reached steady state
        total_length = len(steady_state_soc)

        max_mask = iteration_number // 2

        if max_mask != 0:

            # check for each size of the mask. The max mask size can only be half of the total number of rows
            for k in range(0, max_mask + 1):

                if k != 0:

                    begin_start_row = total_length - k
                    begin_end_row = total_length - 1

                    end_start_row = total_length - 2*k 
                    end_end_row = total_length - k - 1

                    # cycle through each vehicle and check
                    for vehicle_name in steady_state_soc.columns:

                        if vehicle_steady_state[vehicle_name] == False:

                            first_values = np.array(steady_state_soc.loc[begin_start_row:begin_end_row, vehicle_name].to_list())

                            end_values = np.array(steady_state_soc.loc[end_start_row:end_end_row, vehicle_name].to_list())

                            differences = np.abs(first_values - end_values)

                            if np.all(differences <= 1):
                                vehicle_steady_state[vehicle_name] = True
                                distance_sum = dis_dataframe[vehicle_name].sum() / 1000

                                if all(val == 0 for val in first_values) and all(val == 0 for val in end_values):
                                    ### Add steady state success to output
                                    if vehicle_zero_steady_state[vehicle_name] == True:
                                        zero_distances_battery.append(distance_sum)
                                        zero_steady_state_battery = zero_steady_state_battery + 1
                                    else:
                                        zero_distances_chargers.append(distance_sum)
                                        zero_steady_state_chargers = zero_steady_state_chargers + 1

                                ### If positive steady state has been reached        
                                else:
                                    # See which number steady state was reached
                                    if k <= 1:
                                        postive_distances.append(distance_sum)
                                        positive_steady_state = positive_steady_state + 1
                                    else:
                                        postive_distances_oscilation.append(distance_sum)
                                        positive_steady_state_oscilation = positive_steady_state_oscilation + 1
                                        

            vehicle_steady_state = {'Vehicle_' + str(i): False for i in range(1, num_vehicles + 1)}
                
        total_vehicle_days = total_vehicle_days + len(soc_dataframe.columns)

    print(f"Total Vehicle Days: {total_vehicle_days}")

    print(f"Total Positive Steady State: {positive_steady_state}")
    print(f"Total Positive Steady State - Oscilations: {positive_steady_state_oscilation}")
    print(f"Total Zero Steady State - Battery: {zero_steady_state_battery}")
    print(f"Total Zero Steady State - Charging: {zero_steady_state_chargers}")           

    print("Saving Graphs")


    # Calculate the range of the data for the non-empty sequences
    data_range_1 = max(postive_distances) - min(postive_distances) if postive_distances else 0
    data_range_2 = max(zero_distances_battery) - min(zero_distances_battery) if zero_distances_battery else 0
    data_range_3 = max(zero_distances_chargers) - min(zero_distances_chargers) if zero_distances_chargers else 0
    data_range_4 = max(postive_distances_oscilation) - min(postive_distances_oscilation) if postive_distances_oscilation else 0

    desired_bin_width = 5  # Adjust as needed

    # Calculate the number of bins based on the desired bin width
    num_bins_1 = max(1, int(np.ceil(data_range_1 / desired_bin_width)))
    num_bins_2 = max(1, int(np.ceil(data_range_2 / desired_bin_width)))
    num_bins_3 = max(1, int(np.ceil(data_range_3 / desired_bin_width)))
    num_bins_4 = max(1, int(np.ceil(data_range_4 / desired_bin_width)))


    ### Plot the distance distribution for zero and positive steady state
    plt.figure()
    # Create a histogram for the list above x-axis
    plt.hist(postive_distances, bins=num_bins_1, color='#FFA500', alpha=0.7, label='Positive Steady State')
    plt.hist(postive_distances_oscilation, bins=num_bins_4, color='#FFE6B9', alpha=0.7, label='Positive Steady State - Oscilation')

    # Create a histogram for the list below x-axis
    plt.hist(zero_distances_battery, bins=num_bins_2, color='#2D71E6', alpha=0.7, label='0% Steady State - Battery')
    plt.hist(zero_distances_chargers, bins=num_bins_3, color='#ADD8E6', alpha=0.7, label='0% Steady State - Charging')

    plt.title("Distance Distribution for Steady State")
    plt.xlabel("Distance per Day [km]")
    plt.ylabel("Frequency")
    plt.legend()

    save_path = sce_folder + '/Distance_Histogram.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = sce_folder + '/Distance_Histogram.svg'
    plt.savefig(save_path, format = 'svg')
    # Save the plot to a specific location as a svg
    save_path = sce_folder + '/Distance_Histogram.pdf'
    plt.savefig(save_path, format = 'pdf')

    plt.close()


"""
#################################################################################################################
################################# Scenario for Home Charging = True #############################################
#################################################################################################################

print('Results - Home Charging')

### Home charging scenario
sce_folders = glob.glob(os.path.join(source_folder, 'SCE*True'))

total_vehicle_days = 0

### For each SCE folder that has HC = False
for sce_folder in sce_folders:

    day_exists = {save_common + day: False for day in days}

    day_subfolders = glob.glob(os.path.join(sce_folder, 'Day*'))
    sce_folder_name = os.path.basename(sce_folder)

    vehicle_total_trips = {'Vehicle_' + str(i): 0 for i in range(1, num_vehicles + 1)}
    vehicle_completed_trips = {'Vehicle_' + str(i): 0 for i in range(1, num_vehicles + 1)}

    day_total_trips = {save_common + day: 0 for day in days}
    day_completed_trips = {save_common + day: 0 for day in days}

    vehicle_end_soc = {'Vehicle_' + str(i): 0 for i in range(1, num_vehicles + 1)}
    day_end_soc = {save_common + day: 0 for day in days}

    hundred_distances = []
    all_positive_distances = []
    zero_distances_chargers = []
    zero_distances_battery = []

    hundred_steady_state = 0
    all_positive_steady_state = 0
    zero_steady_state_chargers = 0
    zero_steady_state_battery = 0

    print(sce_folder_name)

    ### For each day folder in the SCE folder
    for day_folder in day_subfolders:

        day_folder_name = os.path.basename(day_folder)
        day_exists[day_folder_name] = True

        soc_file_path = os.path.join(day_folder, 'soc.csv')
        dis_file_path = os.path.join(day_folder, 'distance.csv')

        soc_dataframe = pd.read_csv(soc_file_path)
        dis_dataframe = pd.read_csv(dis_file_path)

        first_row = soc_dataframe.iloc[0]
        last_row = soc_dataframe.iloc[-1]

        day_total_trips[day_folder_name] = len(soc_dataframe.columns)

        total_vehicle_days = total_vehicle_days + len(soc_dataframe.columns)

        for column_name in soc_dataframe.columns:

            distance_sum = dis_dataframe[column_name].sum() / 1000 # change meters to kilometers

            vehicle_total_trips[column_name] = vehicle_total_trips[column_name] + 1

            if (soc_dataframe[column_name] > 0).all():
                vehicle_completed_trips[column_name] = vehicle_completed_trips[column_name] + 1
                day_completed_trips[day_folder_name] = day_completed_trips[day_folder_name] + 1

                all_positive_distances.append(distance_sum)
                all_positive_steady_state = all_positive_steady_state + 1

            if last_row[column_name] >= 98:
                vehicle_end_soc[column_name] = vehicle_end_soc[column_name] + 1
                day_end_soc[day_folder_name] = day_end_soc[day_folder_name] + 1

                hundred_distances.append(distance_sum)
                hundred_steady_state = hundred_steady_state + 1
            else:
                if (soc_dataframe[column_name] <= 0).any():
                    zero_distances_battery.append(distance_sum)
                    zero_steady_state_battery = zero_steady_state_battery + 1
                else:
                    zero_distances_chargers.append(distance_sum)
                    zero_steady_state_chargers = zero_steady_state_chargers + 1


    print(f"Total Vehicle Days: {total_vehicle_days}")
    print(f"Total Postive Days: {all_positive_steady_state}")
    print(f"Total 100% Steady State: {hundred_steady_state}")
    print(f"Total Zero - Chargers: {zero_steady_state_chargers}")
    print(f"Total Zero - Battery: {zero_steady_state_battery}")



    print("Saving Graphs")

    # Calculate the range of the data
    data_range_1 = max(hundred_distances) - min(hundred_distances)
    data_range_2 = max(zero_distances_chargers) - min(zero_distances_chargers)
    data_range_3 = max(zero_distances_battery) - min(zero_distances_battery)

    desired_bin_width = 5  # Adjust as needed

    # Calculate the number of bins based on the desired bin width
    num_bins_1 = int(np.ceil(data_range_1 / desired_bin_width))
    num_bins_2 = int(np.ceil(data_range_2 / desired_bin_width))
    num_bins_3 = int(np.ceil(data_range_3 / desired_bin_width))

    ### Plot the distance distribution for zero and positive steady state
    plt.figure()
    # Create a histogram for the list above x-axis
    plt.hist(hundred_distances, bins=num_bins_1, color='#FFA500', alpha=0.7, label='100% Steady State')

    # Create a histogram for the list below x-axis
    plt.hist(zero_distances_battery, bins=num_bins_3, color='#2D71E6', alpha=0.7, label='Non Steady State - Battery')
    plt.hist(zero_distances_chargers, bins=num_bins_2, color='#ADD8E6', alpha=0.7, label='Non Steady State - Charging')

    plt.title("Distance Distribution for Steady State")
    plt.xlabel("Distance per Day [km]")
    plt.ylabel("Frequency")
    plt.legend()

    save_path = sce_folder + '/Distance_Histogram.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = sce_folder + '/Distance_Histogram.svg'
    plt.savefig(save_path, format = 'svg')

    plt.close()

    ### Vehicle Succesful Trips for day - was it able to stay above 0%
    # Calculate completion and uncompletion percentages
    completion_percentages = []
    for vehicle in vehicle_total_trips:
        if vehicle_total_trips[vehicle] != 0:
            completion_percentage = (vehicle_completed_trips[vehicle] / vehicle_total_trips[vehicle]) * 100
        else:
            completion_percentage = 0
        completion_percentages.append(completion_percentage)

    uncompletion_percentages = [100 - percentage for percentage in completion_percentages]

    # Create the figure and axis objects
    fig, ax = plt.subplots()
    x = np.arange(len(vehicle_total_trips)) * 1.7
    bar_width = 1
    bar1 = ax.bar(x, completion_percentages, bar_width, label = 'Completed Trips', color = '#FFA500')
    bar2 = ax.bar(x, uncompletion_percentages, bar_width, bottom=completion_percentages, label = 'Uncompleted Trips', color = '#ADD8E6')

    for rect, completion_percentage in zip(bar1 + bar2, completion_percentages):
        height = rect.get_height()
        if completion_percentage > 0:
                if completion_percentage < 10:
                    ax.text(rect.get_x() + rect.get_width() / 2, height + 2, f'{completion_percentage:.1f}%', ha = 'center', va = 'bottom', fontsize = 8, rotation = 90)
                else:
                    ax.text(rect.get_x() + rect.get_width() / 2, height / 2, f'{completion_percentage:.1f}%', ha = 'center', va = 'center', fontsize = 8, rotation = 90)

    ax.set_xticks(x)
    ax.set_xticklabels(range(1, num_vehicles + 1), fontsize = 6)

    ax.set_ylabel('Percentage [%]')
    ax.set_ylim(0, 115)

    ax.set_title('Vehicle_Day Completion Rate')
    ax.set_xlabel('Vehicle')
    plt.legend(loc = 'upper center', ncol = 2)

    plt.tight_layout()

    save_path = sce_folder + '/Vehicle_Day_Trip_Completion.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = sce_folder + '/Vehicle_Day_Trip_Completion.svg'
    plt.savefig(save_path, format = 'svg')



    ### Succesful Day Trips - did all the vehicles of that day stay above 0%
    # Calculate completion and uncompletion percentages
    completion_percentages = []
    for vehicle in day_total_trips:
        if day_total_trips[vehicle] != 0:
            completion_percentage = (day_completed_trips[vehicle] / day_total_trips[vehicle]) * 100
        else:
            completion_percentage = 0
        completion_percentages.append(completion_percentage)
    uncompletion_percentages = [100 - percentage for percentage in completion_percentages]

    # Create the figure and axis objects
    fig, ax = plt.subplots()
    x = np.arange(len(day_total_trips)) * 3
    bar_width = 2
    bar1 = ax.bar(x, completion_percentages, bar_width, label = 'Completed Trips', color = '#FFA500')
    bar2 = ax.bar(x, uncompletion_percentages, bar_width, bottom=completion_percentages, label = 'Uncompleted Trips', color = '#ADD8E6')

    for rect, completion_percentage, vehicle_name in zip(bar1 + bar2, completion_percentages, day_total_trips.keys()):
        if day_exists[vehicle_name]:
            height = rect.get_height()
            if completion_percentage > 0:
                if completion_percentage < 10:
                    ax.text(rect.get_x() + rect.get_width() / 2, height + 2, f'{completion_percentage:.1f}%', ha = 'center', va = 'bottom', fontsize = 8, rotation = 90)
                else:
                    ax.text(rect.get_x() + rect.get_width() / 2, height / 2, f'{completion_percentage:.1f}%', ha = 'center', va = 'center', fontsize = 8, rotation = 90)


    for i, exists in enumerate(day_exists.values()):
        if not exists:
            bar1[i].set_height(0)
            bar2[i].set_height(0)

    ax.set_xticks(x)
    ax.set_xticklabels(range(1, len(days) + 1), fontsize = 6)

    ax.set_ylabel('Percentage [%]')
    ax.set_xlabel('Day')
    ax.set_ylim(0, 115)

    ax.set_title('Daily Completion Rate')
    plt.legend(loc = 'upper center', ncol = 2)

    plt.tight_layout()

    save_path = sce_folder + '/Daily_Valid_Trip_Completion.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = sce_folder + '/Daily_Valid_Trip_Completion.svg'
    plt.savefig(save_path, format = 'svg')
                


    ### Vehicle Valid Trips for next day - was it able to get back to 0%
    # Calculate completion and uncompletion percentages
    completion_percentages = []
    for vehicle in vehicle_total_trips:
        if vehicle_total_trips[vehicle] != 0:
            completion_percentage = (vehicle_completed_trips[vehicle] / vehicle_total_trips[vehicle]) * 100
        else:
            completion_percentage = 0
        completion_percentages.append(completion_percentage)

    uncompletion_percentages = [100 - percentage for percentage in completion_percentages]

    # Create the figure and axis objects
    fig, ax = plt.subplots()
    x = np.arange(len(vehicle_total_trips)) * 1.7
    bar_width = 1
    bar1 = ax.bar(x, completion_percentages, bar_width, label = 'Valid', color = '#FFA500')
    bar2 = ax.bar(x, uncompletion_percentages, bar_width, bottom=completion_percentages, label = 'Invalid', color = '#ADD8E6')

    for rect, completion_percentage in zip(bar1 + bar2, completion_percentages):
        height = rect.get_height()
        if completion_percentage > 0:
                if completion_percentage < 10:
                    ax.text(rect.get_x() + rect.get_width() / 2, height + 2, f'{completion_percentage:.1f}%', ha = 'center', va = 'bottom', fontsize = 8, rotation = 90)
                else:
                    ax.text(rect.get_x() + rect.get_width() / 2, height / 2, f'{completion_percentage:.1f}%', ha = 'center', va = 'center', fontsize = 8, rotation = 90)

    ax.set_xticks(x)
    ax.set_xticklabels(range(1, num_vehicles + 1), fontsize = 6)

    ax.set_ylabel('Percentage [%]')
    ax.set_ylim(0, 115)

    ax.set_title('Vehicle_Day Valid Completion Rate')
    ax.set_xlabel('Vehicle')
    plt.legend(loc = 'upper center', ncol = 2)

    plt.tight_layout()

    save_path = sce_folder + '/Vehicle_Day_Valid_Completion.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = sce_folder + '/Vehicle_Day_Valid_Completion.svg'
    plt.savefig(save_path, format = 'svg')



    ### Valid for next Day Trips - did all the vehicles manage to get to 100% SOC at the end of the day
    # Calculate completion and uncompletion percentages
    completion_percentages = []
    for vehicle in day_total_trips:
        if day_total_trips[vehicle] != 0:
            completion_percentage = (day_completed_trips[vehicle] / day_total_trips[vehicle]) * 100
        else:
            completion_percentage = 0
        completion_percentages.append(completion_percentage)
    uncompletion_percentages = [100 - percentage for percentage in completion_percentages]

    # Create the figure and axis objects
    fig, ax = plt.subplots()
    x = np.arange(len(day_total_trips)) * 3
    bar_width = 2
    bar1 = ax.bar(x, completion_percentages, bar_width, label = 'Validity', color = '#FFA500')
    bar2 = ax.bar(x, uncompletion_percentages, bar_width, bottom=completion_percentages, label = 'Invalidity', color = '#ADD8E6')

    for rect, completion_percentage, vehicle_name in zip(bar1 + bar2, completion_percentages, day_total_trips.keys()):
        if day_exists[vehicle_name]:
            height = rect.get_height()
            if completion_percentage > 0:
                if completion_percentage < 10:
                    ax.text(rect.get_x() + rect.get_width() / 2, height + 2, f'{completion_percentage:.1f}%', ha = 'center', va = 'bottom', fontsize = 8, rotation = 90)
                else:
                    ax.text(rect.get_x() + rect.get_width() / 2, height / 2, f'{completion_percentage:.1f}%', ha = 'center', va = 'center', fontsize = 8, rotation = 90)


    for i, exists in enumerate(day_exists.values()):
        if not exists:
            bar1[i].set_height(0)
            bar2[i].set_height(0)

    ax.set_xticks(x)
    ax.set_xticklabels(range(1, len(days) + 1), fontsize = 6)

    ax.set_ylabel('Percentage [%]')
    ax.set_xlabel('Day')
    ax.set_ylim(0, 115)

    ax.set_title('Daily Validity Rate')
    plt.legend(loc = 'upper center', ncol = 2)

    plt.tight_layout()

    save_path = sce_folder + '/Daily_Valid_Next_Trip.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = sce_folder + '/Daily_Valid_Next_Trip.svg'
    plt.savefig(save_path, format = 'svg')
    
    """