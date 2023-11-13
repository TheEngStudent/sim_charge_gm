################################################## READ ME ##################################################
"""
    This programme some columns to the data to be used by sim_charge.py

    Currently, the data exists as the table structure below. However, this is not enough for sim_charge.py to
    run and so further columns would need to be added about when charging is availble and which area it is in.

    Time_of_Day | Energy_Consumption    | Latitude  | Longitude | Stop      | 20_Min_Stop   | 10_Min_Stop   | 5_Min_Stop    |  Distance     
    --------------------------------------------------------------------------------------------------------------------------------------
    (string)    | (float)               | (float)   | (float)   | (boolean) | (boolean)     | (boolean)     | (boolean)     |   (float)
    [YYYY/MM/DD | [Wh/s]                | [degres]  | [degrees] |           |               |               |               |   [meters]
      HH:MM:SS]

    For this dataset, the following locations were used for charging locations:
        Stellenbosch Taxi Rank
        Somerset West Taxi Rank and surrounding areas
        Bellville Taxi Rank

    Time_of_Day | Energy_Consumption    | Latitude  | Longitude | Stop      | 20_Min_Stop   | 10_Min_Stop   | 5_Min_Stop    |  Distance     |   Area    |   Hub_Locations...    |   Available_Charging...   |   Home_Charging
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    (string)    | (float)               | (float)   | (float)   | (boolean) | (boolean)     | (boolean)     | (boolean)     |   (float)     |   (int)   |   (boolean)           |   (boolean)               |   (boolean)
    [YYYY/MM/DD | [Wh/s]                | [degres]  | [degrees] |           |               |               |               |   [meters]    |           |                       |                           |
      HH:MM:SS]

    The only nescessary columns for sim_charge.py
    is:
        Time_of_Day
        Energy_Consumption
        Available_Charging
        Home_Charging
    The other columns are merely there for ease of use and visualisations to ensure that the code is running smoothly.
    

    The HC_Location and Home_Charging is created in the second iteration of going through everything. This portion of code
    also re-samples the day to start from 04:00:00 to 03:59:59 of the next day. It is able to get the stop location for home
    charging by finding the most occuring location between 20:00:00 and 03:59:59. This is set as the stop oint for the vehicle
    and if the vehicle is within a 25m radius of this point, then it is available to charge at home.

    TO_NOTE -- This is setup for data that is for a month, would need to change for data that is more than a month. Also,
    this code is specific to the GoMetro and MixTelematics datasets and would need to be changed accordingly. Go through all
    the code first if used for other datasets

"""


import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
from haversine import haversine
from scipy.stats import mode
from tqdm import tqdm
import re


source_folder = 'D:/Masters/Simulations/Simulation_3/Usable_Data/'


### General Functions
def is_point_in_stop(point, location):
    lat, lon = point
    latitudes = [coord[0] for coord in location]
    longitudes = [coord[1] for coord in location]
    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)
    
    if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
        return True
    else:
        return False
    
def is_point_in_area(point, areas):
    lat, lon = point
    
    for idx, location in enumerate(areas, start=1):
        min_lat, max_lat = min(location, key=lambda x: x[0])[0], max(location, key=lambda x: x[0])[0]
        min_lon, max_lon = min(location, key=lambda x: x[1])[1], max(location, key=lambda x: x[1])[1]

        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return idx
    
    return 0
    

def is_point_at_home(row, most_common):
    target_latitude = most_common[0]
    target_longitude = most_common[1]
    point_latitude = row['Latitude']
    point_longitude = row['Longitude']
    distance = haversine((target_latitude, target_longitude), (point_latitude, point_longitude), unit = 'm')
    return distance <= 150  

### Suburban areas
### Box coordinates - Stellenbosch Boundary
area_location_SL_boundary = [
    (-33.894752, 18.807879),  
    (-33.894752, 18.90418),       
    (-33.990013, 18.90418),      
    (-33.990013, 18.807879)       
]

### Box coordinates - Bellville Boundary
area_location_BL_boundary = [
    (-33.806716, 18.734015),  
    (-33.806716, 18.615481),       
    (-33.954868, 18.615481),      
    (-33.954868, 18.734015)       
]

### Box coordinates - Blue Downs Boundary
area_location_BD_boundary = [
    (-33.954868, 18.763686),  
    (-33.954868, 18.615481),       
    (-34.079267, 18.615481),      
    (-34.079267, 18.763686)       
]

### Box coordinates - Blue Downs Boundary
area_location_SW_boundary = [
    (-34.041012, 18.90418),  
    (-34.041012, 18.807631),       
    (-34.161965, 18.807631),      
    (-34.161965, 18.90418)       
]



### Suburban Taxi Ranks
### Box coordinates - Stellenbosch Taxi Rank
stop_location_taxi_SL = [
    (-33.932359, 18.857750),  
    (-33.932359, 18.859046),       
    (-33.933172, 18.859046),      
    (-33.933172, 18.857750)       
]

### Box coordinates - Somerset West Taxi Rank
stop_location_taxi_SW = [
    (-34.082664, 18.849362),  
    (-34.082664, 18.853885),       
    (-34.086543, 18.853885),      
    (-34.086543, 18.849362)       
]

### Box coordinates - Bellville Taxi Rank
stop_location_taxi_BL = [
    (-33.904079, 18.630054),  
    (-33.904079, 18.632125),       
    (-33.906430, 18.632125),      
    (-33.906430, 18.630054)       
]

intra_city_vehicle_days = 0
inter_city_vehicle_days = 0
gm_vehicle_days = 0
mt_vehicle_days = 0

intra_city_vehicle_days_gm = 0
inter_city_vehicle_days_gm = 0
intra_city_vehicle_days_mt = 0
inter_city_vehicle_days_mt = 0


### Read the nescessary files and update 
total_files = len([file for root, dirs, files in os.walk(source_folder) for file in files if file == 'vehicle_day_min.csv']) + 31

for root, dirs, files in tqdm(os.walk(source_folder), total=total_files, desc='Processing Files'):

    for file in files:
        if file == 'vehicle_day_min.csv':
            # Find the vehicle number
            match = re.search(r'Vehicle_(\d+)_\d+', os.path.basename(root))
            i_value = int(match.group(1))

            if i_value < 18:
                gm_vehicle_days = gm_vehicle_days + 1
            else:
                mt_vehicle_days = mt_vehicle_days + 1

            file_path = os.path.join(root, file)
            vehicle_day = pd.read_csv(file_path)

            vehicle_day['Time_of_Day'] = pd.to_datetime(vehicle_day['Time_of_Day'])

            home_charging_location = vehicle_day[(vehicle_day['Time_of_Day'].dt.time >= pd.to_datetime('20:00:00').time()) |
                            (vehicle_day['Time_of_Day'].dt.time <= pd.to_datetime('03:59:59').time())]

            most_common_combination = home_charging_location.groupby(['Latitude', 'Longitude']).size().idxmax()

            # Check area which vehicle is driving in
            vehicle_day['Area_Location'] = vehicle_day[['Latitude', 'Longitude']].apply(lambda x: is_point_in_area(x, [area_location_SL_boundary, 
                                                                                                              area_location_SW_boundary, 
                                                                                                              area_location_BD_boundary, 
                                                                                                              area_location_BL_boundary]), axis=1)
            
            # Check to see where the vehicle travelled
            unique_values = vehicle_day['Area_Location'].unique()
            values_other_than_1_and_0 = any(value for value in unique_values if value not in [0, 1])

            if values_other_than_1_and_0:
                # Vehicle travelled outside stellies
                inter_city_vehicle_days = inter_city_vehicle_days + 1
                if i_value < 18:
                    inter_city_vehicle_days_gm = inter_city_vehicle_days_gm + 1
                else:
                    inter_city_vehicle_days_mt = inter_city_vehicle_days_mt + 1
            else:
                # Vehicle travelled inside stellies
                intra_city_vehicle_days = intra_city_vehicle_days + 1
                if i_value < 18:
                    intra_city_vehicle_days_gm = intra_city_vehicle_days_gm + 1
                else:
                    intra_city_vehicle_days_mt = intra_city_vehicle_days_mt + 1


            # Check to see if vehicle has stopped in taxi rank location Location
            vehicle_day['Hub_Location_SL'] = vehicle_day[['Latitude', 'Longitude']].apply(lambda x: is_point_in_stop(x, stop_location_taxi_SL), axis=1)
            vehicle_day['Hub_Location_SW'] = vehicle_day[['Latitude', 'Longitude']].apply(lambda x: is_point_in_stop(x, stop_location_taxi_SW), axis=1)
            vehicle_day['Hub_Location_BL'] = vehicle_day[['Latitude', 'Longitude']].apply(lambda x: is_point_in_stop(x, stop_location_taxi_BL), axis=1)

            # Create Available_Charging column for all locations - is the vehicle able to charge
            vehicle_day['Available_Charging_SL'] = vehicle_day['Hub_Location_SL'] & vehicle_day['20_Min_Stop']
            vehicle_day['Available_Charging_SW'] = vehicle_day['Hub_Location_SW'] & vehicle_day['20_Min_Stop']
            vehicle_day['Available_Charging_BL'] = vehicle_day['Hub_Location_BL'] & vehicle_day['20_Min_Stop']

            # Create Home-Charging Charging
            vehicle_day['HC_Location'] = vehicle_day[['Latitude', 'Longitude']].apply(lambda x: is_point_at_home(x, most_common_combination), axis=1)
            vehicle_day['Home_Charging'] = vehicle_day['HC_Location'] & vehicle_day['20_Min_Stop']

            vehicle_day.to_csv(os.path.join(root, 'vehicle_day_final.csv'), index=False)

print('Processing complete.')

print(f'GoMetro vehicle-days: {gm_vehicle_days}')
print(f'MixTelematics vehicle-days: {mt_vehicle_days}')

print(f'Intra-city vehicle-days: {intra_city_vehicle_days}')
print(f'Inter-city vehicle-days: {inter_city_vehicle_days}')

print(f'Intra-city vehicle-days (GM): {intra_city_vehicle_days_gm}')
print(f'Inter-city vehicle-days (GM): {inter_city_vehicle_days_gm}')
print(f'Intra-city vehicle-days (MT): {intra_city_vehicle_days_mt}')
print(f'Inter-city vehicle-days (MT): {inter_city_vehicle_days_mt}')

