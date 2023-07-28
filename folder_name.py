######################### READ ME ###################################
"""
This folder copies over the files from Chis A's simulation into a new folder 
of choosing. It copies over the exact same tree structure and unzips all the
folders into csv format.

TO_NOTE -- Directories need to be changed for each new sim

This is a test
"""


import os
import shutil
import gzip

### Change these directories for script usage if a new simulation is being done
source_folder_1 = "D:\Masters\Chris Data Model\Scenario_GoMetro\EV_Simulation\EV_Simulation_Outputs"
source_folder_2 = "D:\Masters\Chris Data Model\Scenario_GoMetro\Mobility_Simulation\FCD_Data"

destination_folder = "D:\Masters\Simulations\Simulation_2\Inputs"

# Create and copy file structure function
def copy_folder_structure(source_folder, destination_folder):
    # Copy the entire folder structure
    shutil.copytree(source_folder, destination_folder)

# Copy the other files over function
def copy_folder_structure(source_folder, destination_folder):
    for root, dirs, files in os.walk(source_folder):
        # Get the corresponding destination path based on the root path
        destination_root = os.path.join(destination_folder, os.path.relpath(root, source_folder))

        # Create the corresponding destination folder if it doesn't exist
        os.makedirs(destination_root, exist_ok=True)

        # Copy files to their respective positions in the destination folder
        for file in files:
            source_file_path = os.path.join(root, file)
            destination_file_path = os.path.join(destination_root, file)
            shutil.copy2(source_file_path, destination_file_path)

# Rename the folders function
def rename_subfolders_in_path(path):
    for folder_name in os.listdir(path):
        folder_path = os.path.join(path, folder_name)
        if os.path.isdir(folder_path):
            for subfolder_name in os.listdir(folder_path):
                subfolder_path = os.path.join(folder_path, subfolder_name)
                if os.path.isdir(subfolder_path):
                    subfolder_prefix = f"{folder_name}_{subfolder_name[-2:]}"
                    new_subfolder_name = subfolder_prefix
                    new_subfolder_path = os.path.join(folder_path, new_subfolder_name)
                    os.rename(subfolder_path, new_subfolder_path)

# Decompress folders function
def decompress_csv_gz_files_recursive(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.csv.gz'):
                gz_file_path = os.path.join(root, file)
                output_file_path = os.path.join(root, file[:-3])  # Remove the '.gz' extension

                with gzip.open(gz_file_path, 'rb') as gz_file:
                    with open(output_file_path, 'wb') as output_file:
                        output_file.write(gz_file.read())


copy_folder_structure(source_folder_1, destination_folder)
copy_folder_structure(source_folder_2, destination_folder)
rename_subfolders_in_path(destination_folder)
decompress_csv_gz_files_recursive(destination_folder)



