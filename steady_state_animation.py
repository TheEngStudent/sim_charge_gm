import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import cv2
import os

source_folder = 'D:/Masters/Simulations/Simulation_2/Outputs/Uncontrolled_Charging/SCE_22kW_N6_B70_HC_False/Day_04/'
file_name = 'soc.csv'
iteration_name = 'Iteration_'

save_folder = 'D:/Masters/Simulations/Simulation_2/Outputs/Animation/'
soc_video = 'soc_steady_state.mp4'

num_vehicles = 17
num_minutes = 1440
num_iterations = 7

colour_list = [ '#d9ff00',
                '#00ffd5',
                '#00ff15',
                '#f2ff00',
                '#0019ff',
                '#ffea00',
                '#ff2f00',
                '#00ff88',
                '#ff9d00',
                '#ef65db',
                '#653a2a',
                '#ffa200',
                '#bfff00',
                '#a481af',
                '#e7596a',
                '#d65fb2',
                '#9f5d54',
                '#a67311' ]

color_palette = {'V_' + str(i): colour_list[i - 1] for i in range(1, num_vehicles + 1)}

integer_list = list(range(0, num_minutes))
timedelta_index = pd.to_timedelta(integer_list, unit='m') # TODO: change back to s for secondly data
base_date = pd.to_datetime('04:00:00')
timedelta_index = base_date + timedelta_index

plt.rcParams['figure.dpi'] = 600

column_to_color = {}

# Generate column_to_color mappings using a for loop from 1 to num_vehicles
for i in range(1, num_vehicles + 1):
    # Replace 'data_column_name_i' with the actual column name for the corresponding vehicle index i
    data_column_name = 'Vehicle_' + str(i)  # Replace 'data_column_name_' with the appropriate prefix
    color_key = 'V_' + str(i)
    column_to_color[data_column_name] = color_key


save_path = save_folder + soc_video

# Read data from CSV file


integer_list = list(range(0, 1440))
timedelta_index = pd.to_timedelta(integer_list, unit='m') # TODO: change back to s for secondly data
base_date = pd.to_datetime('04:00:00')
timedelta_index = base_date + timedelta_index

x_min = timedelta_index.min()
x_max = timedelta_index.max()






for k in range(1, num_iterations + 1):

    new_folder = source_folder + iteration_name + str(k) + '/'

    read_path = new_folder + file_name

    print(read_path)
    data = pd.read_csv(read_path)    

    # Plotting the first i rows
    plt.figure(figsize=(8, 6))
    fig, axes = plt.subplots(nrows=1,ncols=1)

    for i in range(1, len(data) + 1):
        for column in data.columns:

            incomplete_data = data[column][:i]
            empty_rows_count = num_minutes - len(incomplete_data)
            empty_rows = pd.Series([np.nan] * empty_rows_count)
            filled_data = pd.concat([incomplete_data, empty_rows])

            color_key = column_to_color.get(column, column)
            plt.plot(timedelta_index, filled_data, color=color_palette[color_key], label=color_key)
            
        plt.xlabel('Time of Day')
        plt.ylabel('SOC [%]')
        plt.title(f'Iteration {k}')
        
        plt.tight_layout()
        plt.xticks(rotation=45)

        plt.xlim(x_min, x_max)
        plt.ylim(-20, 140)


        
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())


        plt.legend(loc='upper center', ncol=5)

        # Adding the solid black line at y = 0
        plt.axhline(y=0, color='black', linewidth=plt.gca().spines['bottom'].get_linewidth())

        # Saving the plot to a specific location as png, svg, and pdf
        save_name = 'image_' + str((k-1)*num_minutes + i) + '.png'
        save_path_png = save_folder + save_name
        print(save_path_png)

        # Adjust the size of the plotting area within the figure
        left, bottom, right, top = 0.1, 0.1, 0.9, 0.9 
        fig.subplots_adjust(left=0.12, bottom=0.19, right=0.96, top=0.92)
        plt.savefig(save_path_png)


        # Close the current figure to free up memory
        plt.cla()

    


######################################### Create mp4 version ###########################################
images = [img for img in os.listdir(save_folder) if img.endswith(".png")]

# Sort the images to maintain the correct order
images.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))

first_image_path = os.path.join(save_folder, images[0])
first_image = cv2.imread(first_image_path)
height, width, layers = first_image.shape
frame_size = (width, height)


# Specify the frame size (width, height) and frame rate (frames per second)
frame_rate = 60  # Set your desired frame rate

# Define the codec and create a VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec for MP4 format
out = cv2.VideoWriter('D:/Masters/Simulations/Simulation_2/Outputs/Animation/output.mp4', fourcc, frame_rate, frame_size)

# Read and write the images to the video
for image in images:
    image_path = os.path.join(save_folder, image)
    print(f"Processing: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error loading image: {image_path}")
    else:
        out.write(img)


# Release the VideoWriter and close all windows
out.release()
cv2.destroyAllWindows()