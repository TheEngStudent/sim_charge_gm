################################################## READ ME ##################################################
"""
    This programme finds the stop locations of the taxis given 20, 10 and 5 minute stop intervals. It then
    plots the data on a map to visualise the stop locations to determine charging locations in
    available_charging.py. This information is also used to determine the trip information of the taxis for
    the scheduling problem

"""




import os
import pandas as pd
from tqdm import tqdm
import folium
from folium.plugins import HeatMap

source_folder = 'D:/Masters/Simulations/Simulation_3/Usable_Data/'

final_stop_5 = pd.DataFrame(columns=['Latitude', 'Longitude'])
final_stop_10 = pd.DataFrame(columns=['Latitude', 'Longitude'])
final_stop_20 = pd.DataFrame(columns=['Latitude', 'Longitude'])

total_files = len([file for root, dirs, files in os.walk(source_folder) for file in files if file == 'vehicle_day_sec.csv']) + 31

for root, dirs, files in tqdm(os.walk(source_folder), total=total_files, desc='Processing Files'):
    for file in files:

        if file == 'vehicle_day_sec.csv':
            file_path = os.path.join(root, file)
            # Read the CSV file using pandas and append it to the csv_data list
            vehicle_day = pd.read_csv(file_path)

            vehicle_day['lat_lon'] = vehicle_day['Latitude'].astype(str) + ',' + vehicle_day['Longitude'].astype(str)
            
            # Identify blocks of True values in 'boolean_column'
            blocks_5 = (vehicle_day['5_Min_Stop'] != vehicle_day['5_Min_Stop'].shift(1)).cumsum()
            blocks_10 = (vehicle_day['10_Min_Stop'] != vehicle_day['10_Min_Stop'].shift(1)).cumsum()
            blocks_20 = (vehicle_day['20_Min_Stop'] != vehicle_day['20_Min_Stop'].shift(1)).cumsum()


            true_blocks_5 = vehicle_day[vehicle_day['5_Min_Stop']].groupby(blocks_5[vehicle_day['5_Min_Stop']])['lat_lon'].agg(lambda x: x.mode().iloc[0]).reset_index(drop=True)
            true_blocks_10 = vehicle_day[vehicle_day['10_Min_Stop']].groupby(blocks_5[vehicle_day['10_Min_Stop']])['lat_lon'].agg(lambda x: x.mode().iloc[0]).reset_index(drop=True)
            true_blocks_20 = vehicle_day[vehicle_day['20_Min_Stop']].groupby(blocks_5[vehicle_day['20_Min_Stop']])['lat_lon'].agg(lambda x: x.mode().iloc[0]).reset_index(drop=True)


            new_true_blocks_5 = true_blocks_5.str.split(',', expand=True)
            new_true_blocks_10 = true_blocks_10.str.split(',', expand=True)
            new_true_blocks_20 = true_blocks_20.str.split(',', expand=True)

            new_true_blocks_5.columns = ['Latitude', 'Longitude']
            new_true_blocks_10.columns = ['Latitude', 'Longitude']
            new_true_blocks_20.columns = ['Latitude', 'Longitude']


            new_true_blocks_5['Latitude'] = new_true_blocks_5['Latitude'].astype(float)
            new_true_blocks_5['Longitude'] = new_true_blocks_5['Longitude'].astype(float)

            new_true_blocks_10['Latitude'] = new_true_blocks_10['Latitude'].astype(float)
            new_true_blocks_10['Longitude'] = new_true_blocks_10['Longitude'].astype(float)

            new_true_blocks_20['Latitude'] = new_true_blocks_20['Latitude'].astype(float)
            new_true_blocks_20['Longitude'] = new_true_blocks_20['Longitude'].astype(float)

            ### Save values to a larger sheet
            final_stop_5 = final_stop_5.append(new_true_blocks_5, ignore_index=True)
            final_stop_10 = final_stop_10.append(new_true_blocks_10, ignore_index=True)
            final_stop_20 = final_stop_20.append(new_true_blocks_20, ignore_index=True)



print("Processing completed.")
print("Saving Data")

final_stop_5.to_csv(os.path.join(source_folder, 'stop_locations_5.csv'), index=False)
final_stop_10.to_csv(os.path.join(source_folder, 'stop_locations_10.csv'), index=False)
final_stop_20.to_csv(os.path.join(source_folder, 'stop_locations_20.csv'), index=False)


### Plot points on map to visualise
latitudes_5 = final_stop_5['Latitude']
longitudes_5 = final_stop_5['Longitude']

latitudes_10 = final_stop_10['Latitude']
longitudes_10 = final_stop_10['Longitude']

latitudes_20 = final_stop_20['Latitude']
longitudes_20 = final_stop_20['Longitude']

map_object_5 = folium.Map(location=[latitudes_5.mean(), longitudes_5.mean()], zoom_start=10, min_zoom=2, max_zoom=20)
map_object_10 = folium.Map(location=[latitudes_10.mean(), longitudes_10.mean()], zoom_start=10, min_zoom=2, max_zoom=20)
map_object_20 = folium.Map(location=[latitudes_20.mean(), longitudes_20.mean()], zoom_start=10, min_zoom=2, max_zoom=20)

heat_data_5 = [[lat, lon] for lat, lon in zip(latitudes_5, longitudes_5)]
heat_data_10 = [[lat, lon] for lat, lon in zip(latitudes_10, longitudes_10)]
heat_data_20 = [[lat, lon] for lat, lon in zip(latitudes_20, longitudes_20)]


HeatMap(heat_data_5).add_to(map_object_5)
HeatMap(heat_data_10).add_to(map_object_10)
HeatMap(heat_data_20).add_to(map_object_20)


map_object_5.save(os.path.join(source_folder, 'stop_locations_5.html'))
map_object_10.save(os.path.join(source_folder, 'stop_locations_10.html'))
map_object_20.save(os.path.join(source_folder, 'stop_locations_20.html'))





