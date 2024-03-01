from glob import glob
import shutil
import json
import os
from loguru import logger
import datetime

def move_inputs(json_data: dict, source_dir: str):
    # setup the logging
    logger.add("logs/inputs.log", rotation="14 days")
     
    for use_case, use_case_data in data.items():
        logger.info(f"Moving files for {use_case}")
        file_name = use_case_data['inputs']['name']
        destination = use_case_data['inputs']['destination']
        
        # check if use_case_data['inputs']['date_formatting'] exists
        if test['inputs']['date_formatting']:
            date_formatting = test['inputs']['date_formatting'] # YYYYMMDD
            date_formatting_dt = test['inputs']['date_formatting_dt'] # %Y%m%d
            # extract date from file name using value from date_formatting
            regex_search = "(\d{"+str(len(date_formatting))+"})"
            match = re.search(regex_search, test_file)
            if match:
                date = match.group(0)
                # convert date into date_formatting_dt
                date = datetime.datetime.strptime(date, date_formatting_dt)
                year = date.year
                month = date.month
                day = date.day
                
                # replace date in destination with date
                destination = destination.replace("YYYY", str(year))
                destination = destination.replace("MM", str(month).zfill(2))
                destination = destination.replace("DD", str(day).zfill(2))
                
                # make the directory if it doesnt exist
                os.makedirs(destination, exist_ok=True)
        
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