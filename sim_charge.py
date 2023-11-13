################################################## READ ME ##################################################
"""
    This programme simulates the vehicle driving and charging with limited number of chargers and different battery
    sizes and charging rates. Furthermore, charging takes place at the specified location, in this case the
    Stellenbosch Taxi Rank. The option is also there to include home charging into the simulation. The results are
    then categorised as Percentage_Day_Completion (how many vehicles completed there trip in that day) and 
    Vehicle_Completion (of the trips the vehicle needs to take, how many has it succesfully completed)

    When the program rearranges the data, it reads it from the individual folders of the vehicle per day,
    and combines the vehicles active on a specific day to the structure as follows:

    Day_k

    Vehicle_1   |   Vehicle_2   |   Vehicle_5   |   --------    |   Vehicle_n
    ----------------------------------------------------------------------------
    [ec/soc/    |   [ec/soc/    |   [ec/soc/    |   --------    |   [ec/soc/  
    cf/ac/dis]  |   cf/ac/dis]  |   cf/ac/dis]  |   --------    |   cf/ac/dis]

    Where:
        ec == energy consumed
        soc == state of charge
        cf == charging flag
        ac == available charging

    Each of these for variables have their own save files which the simulation then reads from. The simulation
    takes one row at a time and does the logic based on the values within the rows. It is important to note that
    the data is given as secondly data. Furthermore, other important values required for the vehicle are also
    created as dataframes for that day.

    The charging is classified as CP/CV (Constant Power followed by Constant Voltage). As a result, the battery 
    voltages and currents for each vehicle are thus also modelled and saved as graphs and files. 

    TO_NOTE this programme has been written with a month of data only, and so should be changed if more data is
    given.
     
"""

########## This only works because data is for a month, would need to be updated for multiple months ###########
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import os
import pandas as pd
import sys
import time
import math
import numpy as np
import re
import seaborn as sns
import concurrent.futures
import threading
import queue
from tqdm import tqdm
import multiprocessing


### Change directory for each new simulation
source_folder = 'D:/Masters/Simulations/Simulation_3/Usable_Data/'
destination_folder = 'D:/Masters/Simulations/Simulation_3/Outputs/'
file_common = 'Vehicle_'
file_name_min = 'vehicle_day_final.csv'
save_common = 'Day_'
file_suffix = '.csv'

### Subfolders to save files in
original_folder = 'Original_Data/'
energy_consumption_folder = 'Original_EC/'
charging_comsumption_folder = 'Charging_EC/'
soc_folder = 'Daily_SOC/'
charging_flag_folder = 'Charging_Flag/'
available_charging_folder_SL = 'Available_Charging_SL/'
available_charging_folder_SW = 'Available_Charging_SW/'
available_charging_folder_BL = 'Available_Charging_BL/'
grid_power_folder = 'Grid_Power/'
home_charging_folder = 'Home_Charging/'
distance_folder = 'Distance/'
area_location_folder = 'Area_Location/'

file_name_ac_sl = 'Available_Charging_SL'
file_name_ac_sw = 'Available_Charging_SW'
file_name_ac_bl = 'Available_Charging_BL'
file_name_ec = 'Energy_Consumption'
file_name_cf = 'Charging_Variable'
file_name_soc = 'SOC'
file_name_hc = 'Home_Charging'
file_name_dis = 'Distance'
file_name_area = 'Area_Location'

save_name_ac_sl = 'available_charging_sl.csv'
save_name_ac_sw = 'available_charging_sw.csv'
save_name_ac_bl = 'available_charging_bl.csv'
save_name_ec = 'energy_consumption.csv'
save_name_soc = 'soc.csv'
save_name_cf = 'charging_variable.csv'
save_name_gp = 'grid_power.csv'
save_name_charger_sl = 'charger_association_sl.csv'
save_name_charger_sw = 'charger_association_sw.csv'
save_name_charger_bl = 'charger_association_bl.csv'
save_name_V_b = 'battery_voltage.csv'
save_name_I_b = 'battery_current.csv'
save_name_dis = 'distance.csv'
save_name_area = 'area_location.csv'

### Constants for simulation
# Battery Model Parameters
battery_parameters = {
    'V_nom': 3.7, # [V]
    'V_max': 4.15, # [V]
    'R_cell': 0.148, # [Ohm]
    'Q_nom': 2.2, # [Ah]
    'E_nom': 8.14, # [Wh]
    'M_p': 78, # Number of batteries in parallel
    'M_s': 110, # Number of batteries in series
    'a_v': 0.06792, # [V/Wh]
    'b_v': 3.592 # [V] 
}

battery_capacity = battery_parameters['E_nom']*battery_parameters['M_p']*battery_parameters['M_s'] # Wh
R_eq = (battery_parameters['M_s'] * battery_parameters['R_cell']) / battery_parameters['M_p'] # Ohm

# Grid Model Parameters
grid_parameters = {
    'num_chargers_SL': 6,
    'num_chargers_SW': 6,
    'num_chargers_BL': 6,
    'P_max_SL': 22, # [kW]
    'P_max_SW': 22, # [kW]
    'P_max_BL': 22, # [kW]
    'efficiency': 0.88,
    'soc_upper_limit': 100, #TODO change to 80 for smart charging
    'soc_lower_limit': 0,
    'home_charge': True, # Set for each sim you wish to desire
    'home_power': 7.2 # [kW]
}


days = [str(num).zfill(2) for num in range(1, 32)]  # Days in the month
bad_days = [21, 22, 30] # Bad days within the data
num_vehicles = 32 # Total number of vehicles used in the sim

# length of lists
length_days = len(days)

# TODO: update this for secondly data
integer_list = list(range(0, 1440))
total_items = len(integer_list)

colour_list = [
    '#d9ff00', '#00ffd5', '#00ff15', '#f2ff00', '#0019ff', '#ffea00', '#ff2f00',
    '#00ff88', '#ff9d00', '#ef65db', '#653a2a', '#ffa200', '#bfff00', '#a481af',
    '#e7596a', '#d65fb2', '#9f5d54', '#a67311', '#ff7f50', '#87cefa', '#32cd32',
    '#da70d6', '#ff4500', '#696969', '#2e8b57', '#8b008b', '#556b2f', '#ff8c00',
    '#9932cc', '#8b0000', '#e9967a', '#8fbc8f', '#483d8b'
]

color_palette = {'Vehicle_' + str(i): colour_list[i - 1] for i in range(1, num_vehicles + 1)}


### Create colour coordination for different data
color_data = {}
label_data = {}
for i in range(1, num_vehicles + 1):
    if i < 18:
        color_data['Vehicle_' + str(i)] = '#fc0f03' # Use colors 1 to 18 for numbers less than or equal to 18
        label_data['Vehicle_' + str(i)] = 'GoMetro Data'
    else:
        color_data['Vehicle_' + str(i)] = '#03f8fc'
        label_data['Vehicle_' + str(i)] = 'MixTelematics Data'

unique_labels = {'GoMetro Data': '#fc0f03', 'MixTelematics Data': '#03f8fc'}

unique_labels_2 = {'Intra-city': '#02e31c', 
                   'Inter-city': '#0227e3'}



plt.rcParams['figure.dpi'] = 600
 
### Colour dictionary for vehicle tracking through each graph

another_colour = colour_list[32]

# Thread-safe printing using a lock
print_lock = threading.Lock()


### Functions
# Count the number of folders
def count_folders(directory):
    folder_count = 0
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_dir():
                folder_count += 1
    return folder_count

# Create folder if it does not exist
def create_folder(directory):
    # Create folder if not exist
    if not os.path.exists(directory):
        os.makedirs(directory)

# Main algorithm for calculating
def simulate_charge(og_ec, og_ac_sl, og_ac_sw, og_ac_bl, og_soc, og_cf, og_hc, grid_power, charger_sl, charger_sw, charger_bl, priority_vehicles_sl, priority_vehicles_sw, priority_vehicles_bl, battery_capacity, pbar,
                    V_t, V_b, I_b, V_oc, V_oc_eq, CP_flag, battery_parameters, grid_parameters, vehicle_valid_drive, start_vehicle_soc):
    
    # Initialise starting SOC
    for vehicle_column_name in og_soc.columns:
        og_soc.iloc[0][vehicle_column_name] = start_vehicle_soc[vehicle_column_name]
    
    # Iterate over each row of og_ec
    for index in range(1, len(og_ec)):
        
        row = og_ac_sl.loc[index]
       
        # If SOC is below 100, the vehicle needs to be charged
        # only calculates new SOC later on, so has to be previous soc
        charging_mask_ac_sl = og_ac_sl.loc[index] & (og_soc.loc[index - 1] < 100)
        charging_mask_ac_sw = og_ac_sw.loc[index] & (og_soc.loc[index - 1] < 100)
        charging_mask_ac_bl = og_ac_bl.loc[index] & (og_soc.loc[index - 1] < 100)

        # Is home charging available
        if grid_parameters['home_charge'] == True:
            charging_mask_hc = og_hc.loc[index] & (og_soc.loc[index - 1] < 100)
            og_cf.loc[index, charging_mask_hc] = -1
        
        ### Charger distribution algorithm
        true_columns_sl = og_ac_sl.columns[charging_mask_ac_sl]
        true_columns_sw = og_ac_sw.columns[charging_mask_ac_sw]
        true_columns_bl = og_ac_bl.columns[charging_mask_ac_bl]  # Get column labels with true values

        row_headings_sl = []
        row_headings_sw = []
        row_headings_bl = []

        matrix_sl = [[value1 == value2 for value2 in charger_sl.loc[index - 1]] for value1 in true_columns_sl]
        matrix_sw = [[value1 == value2 for value2 in charger_sw.loc[index - 1]] for value1 in true_columns_sw]
        matrix_bl = [[value1 == value2 for value2 in charger_bl.loc[index - 1]] for value1 in true_columns_bl]

        # Print matrix
        for vehicle_name, row in zip(true_columns_sl, matrix_sl):
            row_headings_sl.append(vehicle_name)

        for vehicle_name, row in zip(true_columns_sw, matrix_sw):
            row_headings_sw.append(vehicle_name)

        for vehicle_name, row in zip(true_columns_bl, matrix_bl):
            row_headings_bl.append(vehicle_name)
            
        
        missing_vehicles_sl = set(priority_vehicles_sl).difference(row_headings_sl)
        missing_vehicles_sw = set(priority_vehicles_sw).difference(row_headings_sw)
        missing_vehicles_bl = set(priority_vehicles_bl).difference(row_headings_bl)

        # Remove vehicle if it has lost its position to charge
        for vehicle in missing_vehicles_sl:
            if vehicle in priority_vehicles_sl:
                priority_vehicles_sl.remove(vehicle)

        for vehicle in missing_vehicles_sw:
            if vehicle in priority_vehicles_sw:
                priority_vehicles_sw.remove(vehicle)
        
        for vehicle in missing_vehicles_bl:
            if vehicle in priority_vehicles_bl:
                priority_vehicles_bl.remove(vehicle)
        
        # Iterate over rows and row headings
        for vehicle_name, row in zip(true_columns_sl, matrix_sl):
            if any(row): # If vehicle has been assigned, keep vehicle in charger
                column_index = row.index(True)
                column_heading = charger_sl.columns[column_index]

                charger_sl.loc[index, column_heading] = vehicle_name
            else: # If vehicle has not been assigned charger, add to list of vehicles needing to be charged
                # only add if vehicle is driving and hasn't gone flat
                if og_cf.loc[index - 1, vehicle_name] != 4:
                    if vehicle_name not in priority_vehicles_sl:
                        priority_vehicles_sl.append(vehicle_name)

        for vehicle_name, row in zip(true_columns_sw, matrix_sw):
            if any(row): # If vehicle has been assigned, keep vehicle in charger
                column_index = row.index(True)
                column_heading = charger_sw.columns[column_index]

                charger_sw.loc[index, column_heading] = vehicle_name
            else: # If vehicle has not been assigned charger, add to list of vehicles needing to be charged
                # only add if vehicle is driving and hasn't gone flat
                if og_cf.loc[index - 1, vehicle_name] != 4:
                    if vehicle_name not in priority_vehicles_sw:
                        priority_vehicles_sw.append(vehicle_name)

        for vehicle_name, row in zip(true_columns_bl, matrix_bl):
            if any(row): # If vehicle has been assigned, keep vehicle in charger
                column_index = row.index(True)
                column_heading = charger_bl.columns[column_index]

                charger_bl.loc[index, column_heading] = vehicle_name
            else: # If vehicle has not been assigned charger, add to list of vehicles needing to be charged
                # only add if vehicle is driving and hasn't gone flat
                if og_cf.loc[index - 1, vehicle_name] != 4:
                    if vehicle_name not in priority_vehicles_bl:
                        priority_vehicles_bl.append(vehicle_name)

        # Reorganise pirioty_vehicles to have the lowest SOC at the top
        #priority_vehicles_sl = sorted(priority_vehicles_sl, key = lambda x: og_soc.loc[index - 1, x]) #TODO uncomment to have lowest SOC charge first, currently first in charges
        #priority_vehicles_sw = sorted(priority_vehicles_sw, key = lambda x: og_soc.loc[index - 1, x])
        #priority_vehicles_bl = sorted(priority_vehicles_bl, key = lambda x: og_soc.loc[index - 1, x])

        for k in range(0, len(priority_vehicles_sl)):
            if any(charger_sl.loc[index] == ''): # If available charger, add vehicle to it
                next_col = charger_sl.loc[index].eq('').idxmax()
                charger_sl.loc[index, next_col] = priority_vehicles_sl[0]
                priority_vehicles_sl.pop(0)
            else:
                # Check if there is a vehicle with an SOC higher than 80% that is on charge
                # If there is, remove vehicle from charger and add it to prirority_vehicles
                # Top value from priority_vehicles gets added to charger
                highest_soc_remove = sorted(charger_sl.loc[index], key = lambda x: og_soc.loc[index - 1, x], reverse = True)

                for w in range(0, len(highest_soc_remove)):

                    if og_soc.loc[index - 1, priority_vehicles_sl[0]] < grid_parameters['soc_upper_limit']: # It should only swap vehicles if the soc in priority vehicles is less than 80

                        column_name = highest_soc_remove[w] # Assign the highest column name with the highest soc to remove first
                        if og_soc.loc[index - 1, column_name] >= grid_parameters['soc_upper_limit']:
                            column_to_replace = charger_sl.loc[index] == column_name # find the location where that value is
                            charger_sl.loc[index, column_to_replace.idxmax()] = priority_vehicles_sl[0] # make it equal to the highest priority vehicle
                            priority_vehicles_sl.pop(0)
                            if vehicle_name not in priority_vehicles_sl:
                                priority_vehicles_sl.append(column_name) # add the vehicle that was on charge to priority list

                    else:    
                        break # If no available slot, break for loop to save processing power

        for k in range(0, len(priority_vehicles_sw)):
            if any(charger_sw.loc[index] == ''): # If available charger, add vehicle to it
                next_col = charger_sw.loc[index].eq('').idxmax()
                charger_sw.loc[index, next_col] = priority_vehicles_sw[0]
                priority_vehicles_sw.pop(0)
            else:
                # Check if there is a vehicle with an SOC higher than 80% that is on charge
                # If there is, remove vehicle from charger and add it to prirority_vehicles
                # Top value from priority_vehicles gets added to charger
                highest_soc_remove = sorted(charger_sw.loc[index], key = lambda x: og_soc.loc[index - 1, x], reverse = True)

                for w in range(0, len(highest_soc_remove)):

                    if og_soc.loc[index - 1, priority_vehicles_sw[0]] < grid_parameters['soc_upper_limit']: # It should only swap vehicles if the soc in priority vehicles is less than 80

                        column_name = highest_soc_remove[w] # Assign the highest column name with the highest soc to remove first
                        if og_soc.loc[index - 1, column_name] >= grid_parameters['soc_upper_limit']:
                            column_to_replace = charger_sw.loc[index] == column_name # find the location where that value is
                            charger_sw.loc[index, column_to_replace.idxmax()] = priority_vehicles_sw[0] # make it equal to the highest priority vehicle
                            priority_vehicles_sw.pop(0)
                            if vehicle_name not in priority_vehicles_sw:
                                priority_vehicles_sw.append(column_name) # add the vehicle that was on charge to priority list

                    else:    
                        break # If no available slot, break for loop to save processing power

        for k in range(0, len(priority_vehicles_bl)):
            if any(charger_bl.loc[index] == ''): # If available charger, add vehicle to it
                next_col = charger_bl.loc[index].eq('').idxmax()
                charger_bl.loc[index, next_col] = priority_vehicles_bl[0]
                priority_vehicles_bl.pop(0)
            else:
                # Check if there is a vehicle with an SOC higher than 80% that is on charge
                # If there is, remove vehicle from charger and add it to prirority_vehicles
                # Top value from priority_vehicles gets added to charger
                highest_soc_remove = sorted(charger_bl.loc[index], key = lambda x: og_soc.loc[index - 1, x], reverse = True)

                for w in range(0, len(highest_soc_remove)):

                    if og_soc.loc[index - 1, priority_vehicles_bl[0]] < grid_parameters['soc_upper_limit']: # It should only swap vehicles if the soc in priority vehicles is less than 80

                        column_name = highest_soc_remove[w] # Assign the highest column name with the highest soc to remove first
                        if og_soc.loc[index - 1, column_name] >= grid_parameters['soc_upper_limit']:
                            column_to_replace = charger_bl.loc[index] == column_name # find the location where that value is
                            charger_bl.loc[index, column_to_replace.idxmax()] = priority_vehicles_bl[0] # make it equal to the highest priority vehicle
                            priority_vehicles_bl.pop(0)
                            if vehicle_name not in priority_vehicles_bl:
                                priority_vehicles_bl.append(column_name) # add the vehicle that was on charge to priority list

                    else:    
                        break # If no available slot, break for loop to save processing power

        ### Update og_cf based on charger distibution
        for charger_col in charger_sl.columns:
            assigned_vehicle = charger_sl.loc[index, charger_col]
            if assigned_vehicle:
                og_cf.loc[index, assigned_vehicle] = 1

        for charger_col in charger_sw.columns:
            assigned_vehicle = charger_sw.loc[index, charger_col]
            if assigned_vehicle:
                og_cf.loc[index, assigned_vehicle] = 2

        for charger_col in charger_bl.columns:
            assigned_vehicle = charger_bl.loc[index, charger_col]
            if assigned_vehicle:
                og_cf.loc[index, assigned_vehicle] = 3
        





        ### Calculate battery characteristics
        for col_name in og_soc.columns:

            # Check if vehicle has gone below 0% for the day
            if og_soc.loc[index - 1, col_name] <= grid_parameters['soc_lower_limit']:
                vehicle_valid_drive[col_name] = False
                og_cf.loc[index, col_name] = 4

            # Calculate open circuit voltage
            V_oc.loc[index, col_name] = battery_parameters['a_v']*( (og_soc.loc[index - 1, col_name]/100)*battery_parameters['E_nom'] ) + battery_parameters['b_v']
            # Calculate battery pack open circuit voltage
            V_oc_eq.loc[index, col_name] = battery_parameters['M_s']*V_oc.loc[index, col_name]

            ### Check to see if the vehicle is on charge
            # Update the necessary power and battery characteristics
            if og_cf.loc[index, col_name] == 1 or og_cf.loc[index, col_name] == 2 or og_cf.loc[index, col_name] == 3:

                # Vehicle is charging at constant power (CP)
                if CP_flag[col_name] == 1:

                    if og_cf.loc[index, col_name] == 1:
                        grid_power.loc[index, col_name] = grid_parameters['P_max_SL']*1000
                    elif og_cf.loc[index, col_name] == 2:
                        grid_power.loc[index, col_name] = grid_parameters['P_max_SW']*1000
                    else:
                        grid_power.loc[index, col_name] = grid_parameters['P_max_BL']*1000

                    V_b.loc[index, col_name] = V_oc_eq.loc[index, col_name]/2 + math.sqrt( grid_parameters['efficiency']*grid_power.loc[index, col_name]*R_eq 
                                                    + 0.25*(V_oc_eq.loc[index, col_name] ** 2) )
                    
                    V_t.loc[index, col_name] = V_b.loc[index, col_name]/battery_parameters['M_s']

                    if V_t.loc[index, col_name] > battery_parameters['V_max']:
                        # Vehcile is no longer in constant power charging, but now constant voltage charging
                        CP_flag[col_name] = 0    

                # Vehicle is charging at constant voltage (CV)
                if CP_flag[col_name] == 0:

                    V_t.loc[index, col_name] = battery_parameters['V_max']
                    V_b.loc[index, col_name] = V_t.loc[index, col_name]*battery_parameters['M_s']

                    I_b.loc[index, col_name] = ( battery_parameters['M_s']*battery_parameters['V_max'] - V_oc_eq.loc[index, col_name] ) / R_eq

                    grid_power.loc[index, col_name] = ( battery_parameters['M_s']*battery_parameters['V_max']*I_b.loc[index, col_name] ) / grid_parameters['efficiency']

                # Update SOC for charging
                og_soc.loc[index, col_name] = og_soc.loc[index - 1, col_name] + (((grid_power.loc[index, col_name])/60)/battery_capacity)*100 # TODO chage back to 3600 for secondly data

                if og_soc.loc[index, col_name] > 100:
                    og_soc.loc[index, col_name] = 100
            
            # If vehicle is not on charge, simply update the battery characteristics
            elif og_cf.loc[index, col_name] == 0:

                grid_power.loc[index, col_name] = 0

                """
                # Calculate driving battery characterisitics
                roots = np.roots([ 1,
                                -V_oc_eq.loc[index, col_name],
                                (og_ec.loc[index, col_name]*3600)*R_eq])

                V_b.loc[index, col_name] = np.max(roots[roots > 0])
                V_t.loc[index, col_name] = V_b.loc[index, col_name] / battery_parameters['M_s']

                if V_t.loc[index, col_name] > battery_parameters['V_max']:
                    V_t.loc[index, col_name] = battery_parameters['V_max']
                    V_b.loc[index, col_name] = V_t.loc[index, col_name]*battery_parameters['M_s']

                I_b.loc[index, col_name] = ( V_b.loc[index, col_name] - V_oc_eq.loc[index, col_name] ) / R_eq
                I_t.loc[index, col_name] = I_b.loc[index, col_name] / battery_parameters['M_p']
                """

                # Update SOC for driving
                og_soc.loc[index, col_name] = og_soc.loc[index - 1, col_name] - (og_ec.loc[index, col_name]/battery_capacity)*100
                

                if CP_flag[col_name] == 0:
                    CP_flag[col_name] = 1
            
            # If vehicle is charging at home
            elif og_cf.loc[index, col_name] == -1: 
                # Vehicle is charging at constant power (CP)
                if CP_flag[col_name] == 1:
                    grid_power.loc[index, col_name] = grid_parameters['home_power']*1000

                    V_b.loc[index, col_name] = V_oc_eq.loc[index, col_name]/2 + math.sqrt( grid_parameters['efficiency']*grid_power.loc[index, col_name]*R_eq 
                                                    + 0.25*(V_oc_eq.loc[index, col_name] ** 2) )
                    
                    V_t.loc[index, col_name] = V_b.loc[index, col_name]/battery_parameters['M_s']

                    if V_t.loc[index, col_name] > battery_parameters['V_max']:
                        # Vehcile is no longer in constant power charging, but now constant voltage charging
                        CP_flag[col_name] = 0    

                # Vehicle is charging at constant voltage (CV)
                if CP_flag[col_name] == 0:

                    V_t.loc[index, col_name] = battery_parameters['V_max']
                    V_b.loc[index, col_name] = V_t.loc[index, col_name]*battery_parameters['M_s']

                    I_b.loc[index, col_name] = ( battery_parameters['M_s']*battery_parameters['V_max'] - V_oc_eq.loc[index, col_name] ) / R_eq

                    grid_power.loc[index, col_name] = ( battery_parameters['M_s']*battery_parameters['V_max']*I_b.loc[index, col_name] ) / grid_parameters['efficiency']

                # Update SOC for charging
                og_soc.loc[index, col_name] = og_soc.loc[index - 1, col_name] + (((grid_power.loc[index, col_name])/60)/battery_capacity)*100 # TODO chage back to 3600 for secondly data

                if og_soc.loc[index, col_name] > 100:
                    og_soc.loc[index, col_name] = 100
            # Vehicle is not charging and flat, og_cf == 4
            else:
                og_soc.loc[index, col_name] = 0
                grid_power.loc[index, col_name] = 0

        # TODO: update this to 100 for secondly data
        if index % 10 == 0:
                pbar.update(10)    


# Saving graphs functions
def save_individual_graphs(og_soc, V_b, save_folder, day, timedelta_index):

    for column in og_soc.columns:
 
        # Create a new figure and axis for each column
        fig, ax1 = plt.subplots(figsize = (12, 9))

        # Plot the first graph (V_b) on the first axis        
        ax1.set_xlabel('Time of Day')
        ax1.set_ylabel('Battery Pack Voltage [V]', color = another_colour)
        ax1.set_ylim(0, 500)  # Set the desired y-axis limits for V_b
        ax1.tick_params(axis = 'y', colors = another_colour)
        ax1.set_xticks(ax1.get_xticks())
        ax1.set_xticklabels(ax1.get_xticks(), rotation = 45)

        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())

        ax1.plot(timedelta_index, V_b[column], color = another_colour)

        ax2 = ax1.twinx()

        # Plot the second graph (og_soc) on the second axis
        
        ax2.set_ylabel('SOC [%]', color = color_palette[column])
        ax2.set_ylim(-20, 105)  # Set the desired y-axis limits for og_soc
        ax2.tick_params(axis = 'y', colors = color_palette[column])
        ax2.set_xticks(ax2.get_xticks())
        ax2.set_xticklabels(ax2.get_xticks(), rotation = 45)

        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())

        ax2.plot(timedelta_index, og_soc[column], color = color_palette[column])

        ax1.set_title(column)

                        
        # Save the plot to a specific location as a png
        save_path = save_folder + column + '_' + day + '.png'
        plt.savefig(save_path)
        # Save the plot to a specific location as a svg
        save_path = save_folder + column + '_' + day + '.svg'
        plt.savefig(save_path, format = 'svg')
        # Save the plot to a specific location as a PDF
        save_path = save_folder + column + '_' + day + '.pdf'
        plt.savefig(save_path, format='pdf')

                        
        # Close the figure to free up memory
        plt.close(fig)  


def save_complete_graphs(og_soc, grid_power, day, save_folder, timedelta_index, num_vehicles_day, og_area):

    ### Plot and save all vehicles graph
    plt.figure()
    for column in og_soc.columns:
        plt.plot(timedelta_index, og_soc[column], color = color_palette[column], label = column)
    plt.xlabel('Time of Day')
    plt.ylabel('SOC [%]')
    plt.title('Day_' + day + ' SOC')
    plt.ylim(-20, 140)
    plt.tight_layout()
    plt.xticks(rotation=45)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.legend(loc = 'upper center', ncol = 4)
    plt.subplots_adjust(bottom = 0.2)

    # Adding the solid black line at y = 0
    plt.axhline(y=0, color='black', linewidth=plt.gca().spines['bottom'].get_linewidth())

    save_path = save_folder + 'Day_' + day + '_SOC.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Day_' + day + '_SOC.svg'
    plt.savefig(save_path, format = 'svg')
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Day_' + day + '_SOC.pdf'
    plt.savefig(save_path, format = 'pdf')

    plt.close()


    ### Plot and save all vehicles graph according to data
    plt.figure()
    for column in og_soc.columns:
        plt.plot(timedelta_index, og_soc[column], color = color_data[column])
    plt.xlabel('Time of Day')
    plt.ylabel('SOC [%]')
    plt.title('Day_' + day + ' SOC Data')
    plt.ylim(-20, 140)
    plt.tight_layout()
    plt.xticks(rotation=45)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.legend(handles=[plt.Line2D([0], [0], color=color, label=label) for label, color in unique_labels.items()], loc='upper center', ncol=2)
    plt.subplots_adjust(bottom = 0.2)

    # Adding the solid black line at y = 0
    plt.axhline(y=0, color='black', linewidth=plt.gca().spines['bottom'].get_linewidth())


    save_path = save_folder + 'Day_' + day + '_SOC_Data.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Day_' + day + '_SOC_Data.svg'
    plt.savefig(save_path, format = 'svg')
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Day_' + day + '_SOC_Data.pdf'
    plt.savefig(save_path, format = 'pdf')

    plt.close()

    ### Plot and save all vehicles graph according to area travelled
    plt.figure()
    for column in og_soc.columns:
        unique_values = og_area[column].unique()
        values_other_than_1_and_0 = any(value for value in unique_values if value not in [0, 1])
        if values_other_than_1_and_0:
            color = '#0227e3'
        else:
            color = '#02e31c'
         
        plt.plot(timedelta_index, og_soc[column], color = color)
    plt.xlabel('Time of Day')
    plt.ylabel('SOC [%]')
    plt.title('Day_' + day + ' SOC Inter vs Intra')
    plt.ylim(-20, 140)
    plt.tight_layout()
    plt.xticks(rotation=45)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.legend(handles=[plt.Line2D([0], [0], color=color, label=label) for label, color in unique_labels_2.items()], loc='upper center', ncol=4)
    plt.subplots_adjust(bottom = 0.2)

    # Adding the solid black line at y = 0
    plt.axhline(y=0, color='black', linewidth=plt.gca().spines['bottom'].get_linewidth())


    save_path = save_folder + 'Day_' + day + '_SOC_City.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Day_' + day + '_SOC_City.svg'
    plt.savefig(save_path, format = 'svg')
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Day_' + day + '_SOC_City.pdf'
    plt.savefig(save_path, format = 'pdf')

    plt.close()



    ### Plot grid power usage
    grid_sums = grid_power.sum(axis = 1)
    grid_sums = grid_sums/1000

    plt.figure()
    plt.plot(timedelta_index, grid_sums)
    plt.xlabel('Time of Day')
    plt.ylabel('Power [kW]')
    plt.title('Grid Power for Day_' + day)
    plt.ylim(0, 170)
    plt.xticks(rotation=45)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.subplots_adjust(bottom = 0.2)

    save_path = save_folder + 'Grid_Power_Day_' + day + '.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Grid_Power_Day_' + day + '.svg'
    plt.savefig(save_path, format = 'svg')
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Grid_Power_Day_' + day + '.pdf'
    plt.savefig(save_path, format = 'pdf')

    plt.close()

    ### Plot grid power usage per taxi of that day
    grid_sums = grid_sums/num_vehicles_day

    plt.figure()
    plt.plot(timedelta_index, grid_sums)
    plt.xlabel('Time of Day')
    plt.ylabel('Power [kW]')
    plt.title('Grid Power per Vehicle for Day_' + day)
    plt.ylim(0, 20)
    plt.xticks(rotation=45)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.subplots_adjust(bottom = 0.2)

    save_path = save_folder + 'Grid_Power_Vehicle_Day_' + day + '.png'
    plt.savefig(save_path)
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Grid_Power_Vehicle_Day_' + day + '.svg'
    plt.savefig(save_path, format = 'svg')
    # Save the plot to a specific location as a svg
    save_path = save_folder + 'Grid_Power_Vehicle_Day_' + day + '.pdf'
    plt.savefig(save_path, format = 'pdf')
    plt.close()

# Functions for finding and deleting days with bad data
def extract_day_from_filename(filename):
    # Implement the regular expression pattern to match the day value.
    # For example, if the filename format is "Day_01_xxxxxxxxxx", you can extract the day as follows:
    pattern = r'Day_(\d+)_'
    match = re.search(pattern, filename)
    if match:
        return int(match.group(1))
    return None

def delete_files_with_bad_days(folder_path, bad_days):
    for root, _, files in os.walk(folder_path):
        for filename in files:
            day = extract_day_from_filename(filename)
            if day is not None and day in bad_days:
                file_path = os.path.join(root, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")


"""
########################################################################################################################
################### Create nescessary original files that the simulation runs off of ###################################
########################################################################################################################

num_folders = count_folders(source_folder)

for k in range(0, length_days):  # Cycle through for each day

    data_list_ec = []  # create empty list to combine data at the end
    data_list_ac_sl = []
    data_list_ac_sw = []
    data_list_ac_bl = []
    data_list_hc = []
    data_list_dis = []
    data_list_area = []

    name_list = []  # create empty list for valid vehicles

    for i in range(1, num_folders + 1):  # Check in each vehicle if there is a valid driving day

        # Create file path to read
        sub_path = source_folder + file_common + str(i) + '/'  # //Vehicle_i/

        sub_sub_path = sub_path + file_common + str(i) + '_' + days[k] + '/'  # //Vehicle_i_k/

        if os.path.exists(sub_sub_path):
            # Create path to read file
            full_path = sub_sub_path + file_name_min  # TODO change back to file_name for secondly data

            # File path exists, read the file
            df = pd.read_csv(full_path)
            
            data_list_ec.append(df['Energy_Consumption'])
            data_list_ac_sl.append(df['Available_Charging_SL'])
            data_list_ac_sw.append(df['Available_Charging_SW'])
            data_list_ac_bl.append(df['Available_Charging_BL'])
            data_list_hc.append(df['Home_Charging'])
            data_list_dis.append(df['Distance'])
            data_list_area.append(df['Area_Location'])
            name_list.append(str(i))
        else:
            # File path does not exist, skip
            print(f"File path '{sub_sub_path}' does not exist. Skipping...")

    if data_list_ec:
        ### For Energy_Consumption data
        # Perform functions when the list is not empty
        combined_data_ec = pd.concat(data_list_ec, axis=1)
        vehicle_columns = [file_common + name for name in name_list]
        combined_data_ec.columns = vehicle_columns
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_ec + file_suffix
        save_folder = destination_folder + original_folder + energy_consumption_folder
        save_path = save_folder + save_name
        create_folder(save_folder)
        combined_data_ec.to_csv(save_path, index=False)

        ### For Available_Charging data
        # Perform functions when the list is not empty
        combined_data_ac_sl = pd.concat(data_list_ac_sl, axis=1)
        vehicle_columns = [file_common + name for name in name_list]
        combined_data_ac_sl.columns = vehicle_columns
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_ac_sl + file_suffix
        save_folder = destination_folder + original_folder + available_charging_folder_SL
        save_path = save_folder + save_name
        create_folder(save_folder)
        combined_data_ac_sl.to_csv(save_path, index=False)

        # Perform functions when the list is not empty
        combined_data_ac_sw = pd.concat(data_list_ac_sw, axis=1)
        vehicle_columns = [file_common + name for name in name_list]
        combined_data_ac_sw.columns = vehicle_columns
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_ac_sw + file_suffix
        save_folder = destination_folder + original_folder + available_charging_folder_SW
        save_path = save_folder + save_name
        create_folder(save_folder)
        combined_data_ac_sw.to_csv(save_path, index=False)

        # Perform functions when the list is not empty
        combined_data_ac_bl = pd.concat(data_list_ac_bl, axis=1)
        vehicle_columns = [file_common + name for name in name_list]
        combined_data_ac_bl.columns = vehicle_columns
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_ac_bl + file_suffix
        save_folder = destination_folder + original_folder + available_charging_folder_BL
        save_path = save_folder + save_name 
        create_folder(save_folder)
        combined_data_ac_bl.to_csv(save_path, index=False)

        ### For Home_Charging data
        # Perform functions when the list is not empty
        combined_data_hc = pd.concat(data_list_hc, axis=1)
        vehicle_columns = [file_common + name for name in name_list]
        combined_data_hc.columns = vehicle_columns
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_hc + file_suffix
        save_folder = destination_folder + original_folder + home_charging_folder
        save_path = save_folder + save_name
        create_folder(save_folder)
        combined_data_hc.to_csv(save_path, index=False)

        ### For Distance data
        # Perform functions when the list is not empty
        combined_data_dis = pd.concat(data_list_dis, axis=1)
        vehicle_columns = [file_common + name for name in name_list]
        combined_data_dis.columns = vehicle_columns
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_dis + file_suffix
        save_folder = destination_folder + original_folder + distance_folder
        save_path = save_folder + save_name
        create_folder(save_folder)
        combined_data_dis.to_csv(save_path, index=False)

        ### For starting off SOC data
        combined_data_soc = combined_data_ec.copy()
        combined_data_soc[:] = 100
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_soc + file_suffix
        save_folder = destination_folder + original_folder + soc_folder
        save_path = save_folder + save_name
        create_folder(save_folder)
        combined_data_soc.to_csv(save_path, index=False)

        ### For starting off Charging_Variable data
        combined_data_cf = combined_data_ec.copy()
        combined_data_cf[:] = 0
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_cf + file_suffix
        save_folder = destination_folder + original_folder + charging_flag_folder
        save_path = save_folder + save_name
        create_folder(save_folder)
        combined_data_cf.to_csv(save_path, index=False)

        ### For Available_Charging data
        # Perform functions when the list is not empty
        combined_data_area = pd.concat(data_list_area, axis=1)
        vehicle_columns = [file_common + name for name in name_list]
        combined_data_area.columns = vehicle_columns
        # Save the combined DataFrame to a CSV file
        save_name = save_common + days[k] + '_' + file_name_area + file_suffix
        save_folder = destination_folder + original_folder + area_location_folder
        save_path = save_folder + save_name
        create_folder(save_folder)
        combined_data_area.to_csv(save_path, index=False)
        
    else:
        # Skip over when the list is empty
        print("Day does not exist. Skipping...")

### Delete bad days of data
read_directory = destination_folder + original_folder
delete_files_with_bad_days(read_directory, bad_days)

"""


#######################################################################################################################
############################################ Main simulating code #####################################################
#######################################################################################################################

### Initialise scenario
scenario_folder = 'SCE_' + str(grid_parameters['P_max_SL']) + '-' + str(grid_parameters['P_max_SW']) + '-' + str(grid_parameters['P_max_BL']) + 'kW_N' + str(grid_parameters['num_chargers_SL']) + '-' + str(grid_parameters['num_chargers_SW']) + '-' + str(grid_parameters['num_chargers_BL']) + '_B' + str(round(battery_capacity/1000)) + '_HC_' + str(grid_parameters['home_charge']) + '/'
print(f'Scenario {scenario_folder}')
save_folder = destination_folder + scenario_folder
create_folder(save_folder)


### Introduce multithreading to handle 

def simulate_day(m): 
    
    # Create file paths to read nescessary data
    read_name_ec = save_common + days[m] + '_' + file_name_ec + file_suffix # Day_i_Data.csv
    read_name_ac_sl = save_common + days[m] + '_' + file_name_ac_sl + file_suffix
    read_name_ac_sw = save_common + days[m] + '_' + file_name_ac_sw + file_suffix
    read_name_ac_bl = save_common + days[m] + '_' + file_name_ac_bl + file_suffix
    read_name_soc = save_common + days[m] + '_' + file_name_soc + file_suffix
    read_name_cf = save_common + days[m] + '_' + file_name_cf + file_suffix
    read_name_hc = save_common + days[m] + '_' + file_name_hc + file_suffix
    read_name_dis = save_common + days[m] + '_' + file_name_dis + file_suffix
    read_name_area = save_common + days[m] + '_' + file_name_area + file_suffix

    read_path_ec = destination_folder + original_folder + energy_consumption_folder + read_name_ec
    read_path_ac_sl = destination_folder + original_folder + available_charging_folder_SL + read_name_ac_sl
    read_path_ac_sw = destination_folder + original_folder + available_charging_folder_SW + read_name_ac_sw
    read_path_ac_bl = destination_folder + original_folder + available_charging_folder_BL + read_name_ac_bl
    read_path_soc = destination_folder + original_folder + soc_folder + read_name_soc
    read_path_cf = destination_folder + original_folder + charging_flag_folder + read_name_cf
    read_path_hc = destination_folder + original_folder + home_charging_folder + read_name_hc
    read_path_dis = destination_folder + original_folder + distance_folder + read_name_dis
    read_path_area = destination_folder + original_folder + area_location_folder + read_name_area

    # If file exists for one day then that day exists
    if os.path.exists(read_path_ec):

        # Create save folder only if that day exists
        day_folder = save_common + days[m] + '/' # Day_i/
        save_folder = destination_folder + scenario_folder + day_folder
        create_folder(save_folder)
        
        # Read the nescessary files
        og_ec = pd.read_csv(read_path_ec)
        og_ac_sl = pd.read_csv(read_path_ac_sl)
        og_ac_sw = pd.read_csv(read_path_ac_sw)
        og_ac_bl = pd.read_csv(read_path_ac_bl)
        og_soc = pd.read_csv(read_path_soc)
        og_cf = pd.read_csv(read_path_cf)
        og_hc = pd.read_csv(read_path_hc)
        og_dis = pd.read_csv(read_path_dis)
        og_area = pd.read_csv(read_path_area)

        
        num_vehicles_day = len(og_soc.columns)

        # If there is vehicles to simulate, then simulate
        if not og_ac_sl.empty:

            # Declare variables
            vehicle_valid_drive = {'Vehicle_' + str(i): True for i in range(1, num_vehicles + 1)}
            start_vehicle_soc = {'Vehicle_' + str(i): 100 for i in range(1, num_vehicles + 1)}

            vehicle_steady_state = {col: False for col in og_soc.columns}
            steady_state_soc = pd.DataFrame(100, index = [1], columns=og_soc.columns)

            steady_state_reached = False
            iteration = 1

            ### Simulate until steady is reached
            while not steady_state_reached:

                # Initialise variables
                # Read the nescessary files
                og_ec = pd.read_csv(read_path_ec)
                og_ac_sl = pd.read_csv(read_path_ac_sl)
                og_ac_sw = pd.read_csv(read_path_ac_sw)
                og_ac_bl = pd.read_csv(read_path_ac_bl)
                og_soc = pd.read_csv(read_path_soc)
                og_cf = pd.read_csv(read_path_cf)
                og_hc = pd.read_csv(read_path_hc)
                og_dis = pd.read_csv(read_path_dis)
                og_area = pd.read_csv(read_path_area)

                # Create nescessary other data frames
                grid_power = pd.DataFrame(0, index = range(total_items), columns = og_ec.columns)

                charger_sl = pd.DataFrame('', index = range(len(og_ec)), columns = [f'Charger_{w}' for w in range(1, grid_parameters['num_chargers_SL'] + 1)])
                charger_sw = pd.DataFrame('', index = range(len(og_ec)), columns = [f'Charger_{w}' for w in range(1, grid_parameters['num_chargers_SW'] + 1)])
                charger_bl = pd.DataFrame('', index = range(len(og_ec)), columns = [f'Charger_{w}' for w in range(1, grid_parameters['num_chargers_BL'] + 1)])

                # Battery characteriistic dataframes
                V_t = pd.DataFrame(0, index = range(total_items), columns = og_ec.columns)
                V_b = pd.DataFrame(0, index = range(total_items), columns = og_ec.columns)
                I_b = pd.DataFrame(0, index = range(total_items), columns = og_ec.columns)
                V_oc = pd.DataFrame(0, index = range(total_items), columns = og_ec.columns)
                V_oc_eq = pd.DataFrame(0, index = range(total_items), columns = og_ec.columns)

                save_folder_2 = save_folder + 'Iteration_' + str(iteration) + '/'

                create_folder(save_folder_2) # Create iteration folder

                ### Re-initialise each vehicle to constant power charging
                CP_flag = {'Vehicle_' + str(i): 1 for i in range(1, num_vehicles + 1)}
                priority_vehicles_sl = []
                priority_vehicles_sw = []
                priority_vehicles_bl = []
                #print(f'Day {days[m]} Simulating - I_{iteration}')
                #start_time = time.time()

                # TODO: change back to 86400 for secondly data
                with tqdm(total=1440, desc=f"Day {days[m]} Simulating - I_{iteration}", position=m) as pbar:

                    ### Simulate actual data
                    simulate_charge(og_ec, og_ac_sl, og_ac_sw, og_ac_bl, og_soc, og_cf, og_hc, grid_power, charger_sl, charger_sw, charger_bl, priority_vehicles_sl, priority_vehicles_sw, priority_vehicles_bl, 
                                    battery_capacity, pbar, V_t, V_b, I_b, V_oc, V_oc_eq, CP_flag, battery_parameters, grid_parameters, vehicle_valid_drive, start_vehicle_soc) # Does the actual simulating of vehicles
                    #print('\n')


                pbar.close()

                #print(og_soc)

                steady_state_soc = steady_state_soc.append(og_soc.iloc[-1], ignore_index=True)

                total_length = len(steady_state_soc)

                max_mask = iteration // 2

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


                if all(value for value in vehicle_steady_state.values()):
                    steady_state_reached = True

                vehicle_steady_state = {col: False for col in og_soc.columns}

                ### See how many vehicles have completed their trips
                for vehicle_name in og_soc.columns:

                    start_vehicle_soc[vehicle_name] = og_soc.iloc[-1][vehicle_name]


                #print(end_vehicle_soc)
                #print(count_steady_states)
                #print(steady_state_reached)
                #print(save_folder_2)

                ### Prepare for plotting
                timedelta_index = pd.to_timedelta(integer_list, unit='m') # TODO: change back to s for secondly data
                base_date = pd.to_datetime('04:00:00')
                timedelta_index = base_date + timedelta_index

                ### Plot and save individual vehicle graphs
                print('\nSaving graphs')
                #save_individual_graphs(og_soc, V_b, save_folder_2, days[m], timedelta_index)
                save_complete_graphs(og_soc, grid_power, days[m], save_folder_2, timedelta_index, num_vehicles_day, og_area)
                    
                ### Save dataframes
                print('Saving files')
                save_path = save_folder_2 + save_name_ec
                og_ec.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_cf
                og_cf.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_ac_sl
                og_ac_sl.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_ac_sw
                og_ac_sw.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_ac_bl
                og_ac_bl.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_soc
                og_soc.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_dis
                og_dis.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_gp
                grid_power.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_charger_sl
                charger_sl.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_charger_sw
                charger_sw.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_charger_bl
                charger_bl.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_area
                og_area.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_V_b
                V_b.to_csv(save_path, index=False)

                save_path = save_folder_2 + save_name_I_b
                I_b.to_csv(save_path, index=False)

                if steady_state_reached == True: # If steady state has been reached, then stop simulating
                    break

                iteration = iteration + 1
            
            ### All vehicles become valid again to drive
            vehicle_valid_drive = {'Vehicle_' + str(i): True for i in range(1, num_vehicles + 1)}

            ### Save steady-state SOC
            plt.figure(figsize = (8, 5))

            for col in steady_state_soc.columns:
                plt.plot(steady_state_soc.index, steady_state_soc[col], color = color_palette[col], linestyle='-', label=col)


            plt.xticks(steady_state_soc.index)
            plt.ylim(-20, 140)

            plt.axhline(y=0, color='black', linewidth=plt.gca().spines['bottom'].get_linewidth())

            plt.xlabel('Number of Iterations')
            plt.ylabel('SOC')
            plt.title('Steady State of SOC')

            plt.legend(loc = 'upper center', ncol = 4)

            save_path = save_folder + 'Steady_State_SOC.png'
            plt.savefig(save_path)
            # Save the plot to a specific location as a svg
            save_path = save_folder + 'Steady_State_SOC.svg'
            plt.savefig(save_path, format = 'svg')
            # Save the plot to a specific location as a svg
            save_path = save_folder + 'Steady_State_SOC.pdf'
            plt.savefig(save_path, format = 'pdf')

            plt.close()


        else:
            print(f'Day {days[m]} Simulating')
            print('No vehicles to simulate')


        #print(f'Day {days[m]} does not exist')

    return m
    

### Actually run the next day

# Set the multiprocessing start method to 'fork' or 'spawn'
if __name__ == '__main__':
    start_method = multiprocessing.get_start_method()
    if start_method != 'fork' and start_method != 'spawn':
        multiprocessing.set_start_method('fork')

    # Define the range of days to simulate
    days_to_simulate = range(0, length_days)
    num_processes = 4
         
    # Create a process pool
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit simulations for the days and store the future objects
        futures = {executor.submit(simulate_day, day): day for day in days_to_simulate}

        # Wait for all simulations to complete
        for future in concurrent.futures.as_completed(futures):
            future.result()

    print("All simulations complete.")

