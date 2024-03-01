from glob import glob
import shutil
import json
import os
from loguru import logger

def move_inputs(json_data: dict, source_dir: str):
    # setup the logging
    logger.add("inputs.log", rotation="14 days")
     
    for use_case, use_case_data in data.items():
        logger.info(f"Moving files for {use_case}")
        file_name = use_case_data['inputs']['name']
        destination = use_case_data['inputs']['destination']
        
        files = glob(f"{source_dir}/{file_name}")
        logger.info(f"Found {len(files)} files for {use_case}")
        
        if files:
            for file in files:
                file_name_indiv = file.split("\\")[-1]
                try:
                    shutil.move(file, r'{os.path.join(destination, file_name_indiv)}')
                    logger.success(f"Moved {file_name_indiv} to {destination}")
                except FileExistsError:
                    logger.critical(f"File {file_name_indiv} already exists in {destination}")
                except FileNotFoundError:
                    logger.critical(f"File {file_name_indiv} not found in {source_dir}")
                except Exception as e:
                    logger.critical(f"Error: {e} with {file_name_indiv} in {source_dir}")
    
if __name__ == "__main__":
    # read the json file
    with open('data.json', 'r') as file:
        data = json.load(file)   
    
    # move the input files to their respective destinations
    inputs_dir = r'M:\CPP-Data\Sutherland RPA\Northwell Process Automation ETM Files\GOA\Inputs'
    move_inputs(data, inputs_dir)