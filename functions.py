from glob import glob
import shutil
import os
from loguru import logger
import datetime
import re
import pandas as pd
from zipfile import ZipFile
from tqdm import tqdm


def S_or_Z_drive(destination:str) -> str:
    if os.path.exists('Z:/') and 'S:/' in destination:
        return destination.replace('S:/','Z:/')
    return destination
    

def move_single_file(source: str, destination: str):
    source = str(source)
    source_dir = os.path.dirname(source)
    file_name_indiv = os.path.basename(source)

    try:
        shutil.move(
            source, f'{os.path.join(destination, file_name_indiv)}')
        logger.success(
            f"Moved {file_name_indiv} to {destination}")
    except FileExistsError:
        logger.critical(
            f"File {file_name_indiv} already exists in {destination}")
    except FileNotFoundError:
        logger.critical(
            f"File {file_name_indiv} not found in {source_dir}")
    except Exception as e:
        logger.critical(
            f"Error: {e} with {file_name_indiv} in {source_dir}")


def extract_date_from_file_and_replace_date_in_destination(file_name: str, destination: str, date_formatting: str, date_formatting_dt: str, create_folder = True):
    # check if "_" exists in date_formatting:
    if "_" not in date_formatting:
        regex_search = "(\d{"+str(len(date_formatting))+"})"
    else:
        regex_search = "(\d{2}(_)\d{2}(_)\d{2})"
    match = re.search(regex_search, file_name)
    if match:
        date = match.group(0)
        # convert date into date_formatting_dt
        date = datetime.datetime.strptime(
            date, date_formatting_dt)
        year = date.year
        month = date.month
        day = date.day

        # replace date in destination with date
        destination = destination.replace(
            "YYYY", str(year))
        destination = destination.replace(
            "MM", str(month).zfill(2))
        destination = destination.replace(
            "DD", str(day).zfill(2))

        # make the directory if it doesnt exist
        if create_folder:
            os.makedirs(destination, exist_ok=True)
    return destination, date


def move_inputs(data: dict, source_dir: str):
    # setup the logging
    logger.add("M:/CPP-Data/Sutherland RPA/Northwell Process Automation ETM Files/GOA/Inputs/logs/inputs.log", rotation="7 day", level="INFO")

    for use_case, use_case_data in data.items():
        logger.info(f'---------{use_case} inputs---------')
        file_name = use_case_data['inputs']['name']
        destination = use_case_data['inputs']['destination']
        has_date_formatting = True if use_case_data['inputs'].get(
            'date_formatting') else False
        files = glob(f"{source_dir}/{file_name}")
        logger.info(f"Found {len(files)} files for {use_case}")

        if len(files) > 0:
            for file in files:
                # check if use_case_data['inputs']['date_formatting'] exists
                if has_date_formatting:
                    # YYYYMMDD
                    date_formatting = use_case_data['inputs']['date_formatting']
                    # %Y%m%d
                    date_formatting_dt = use_case_data['inputs']['date_formatting_dt']
                    # change the destination only
                    destination, date = extract_date_from_file_and_replace_date_in_destination(
                        file, destination, date_formatting, date_formatting_dt)
                destination = S_or_Z_drive(destination)
                move_single_file(file, destination)


def move_outputs(data: dict, source_dir: str):
    logger.add("M:/CPP-Data/Sutherland RPA/Northwell Process Automation ETM Files/GOA/Inputs/logs/outputs.log", rotation="7 day", level="INFO")
    for use_case, use_case_data in data.items():
        files = glob(os.path.join(source_dir, use_case_data['zip_name']))
        logger.info(f"Found {len(files)} output files for {use_case}")

        if len(files) > 0:
            logger.info(f'---------{use_case} outputs---------')
            for file in files:
                # get the date from the file name so it can be used for the destination folder
                date_formatting = use_case_data['date_formatting']
                date_formatting_dt = use_case_data['date_formatting_dt']
                destination = use_case_data['destination']
                destination, date = extract_date_from_file_and_replace_date_in_destination(
                    file, destination, date_formatting, date_formatting_dt)

                if use_case == 'chargecorrection':
                    fldr_frmt = '%m%d%Y'
                    destination = f'{destination}{date.strftime(fldr_frmt)}/'
                destination = f'{destination}{date.strftime(date_formatting_dt)}'
                destination = S_or_Z_drive(destination)
            
                # unzip the files and move them to the destination
                with open(file, 'rb') as src:
                    zf = ZipFile(src)
                    folder_count = [m for m in zf.infolist() if m.filename.endswith("/")].__len__()
                    file_count = [m for m in zf.infolist() if not m.filename.endswith("/")].__len__()
                    logger.info(f'Found {folder_count} folders and {file_count} files in the zip file')
                    single_files = [m for m in zf.infolist() if not m.filename.endswith("/")]
                    for single_file in tqdm(single_files):
                        zf.extract(single_file, destination)
                    zf.close()
                
                # confirm the destination folder has all the correct files and folders
                new_file_count = 0
                new_subdir_count = 0
                for _, subdirs, files in os.walk(destination):
                    new_file_count += len(files)
                    new_subdir_count += len(subdirs)
                
                if new_file_count >= file_count and new_subdir_count >= folder_count:
                    if new_file_count == file_count and new_subdir_count == folder_count:
                        logger.success(f'Moved {folder_count} folders and {file_count} files into the destination')
                        logger.info(f'New folder contains {new_subdir_count} folders and {new_file_count} files into the destination')
                    else:
                        logger.warning(f'Moved {folder_count} folders and {file_count} files into the destination')
                        logger.info(f'New folder contains {new_subdir_count} folders and {new_file_count} files into the destination')
                    
                    # move the folder to the moved folder
                    file_name = file.split('\\')[-1]
                    pre_moved_folder_path = f'{source_dir}/{file_name}'
                    moved_folder_date = date.strftime('%Y %m')
                    moved_folder_dir = f'{source_dir}/moved/{moved_folder_date}/'
                    # make folder if not exists
                    os.makedirs(moved_folder_dir, exist_ok=True)
                    moved_folder_dir = f'{moved_folder_dir}/{file_name}'
                    
                    try:
                        os.rename(pre_moved_folder_path, moved_folder_dir)
                    except FileExistsError:
                        logger.warning(f'{moved_folder_dir} already exists')
                elif new_file_count < file_count:
                    logger.critical(f"Failed to move all files to {destination}")
                    logger.critical(f"Expected {file_count} files but only found {new_file_count}")
                elif new_subdir_count < folder_count:
                    logger.critical(f"Failed to move all subdirectories to {destination}")

def parse_output_files(data:dict, source_dir:str):
    output_files = glob(source_dir + "/Outbound*.xlsx")
    for output_file in output_files:
        main = pd.read_excel(output_file, sheet_name='export')
        output_file_dest = output_file.replace(source_dir,'M:/CPP-Data/Sutherland RPA/Combined Outputs')
        for use_case, use_case_data in data.items():
            logger.info(f'parsing output file for {use_case}')
            df = main[main['BotName'] == use_case_data['BotName']]
            
            date_formatting = 'MMDDYYYY'
            date_formatting_dt = '%m%d%Y'
                
            destination,date = extract_date_from_file_and_replace_date_in_destination(output_file, use_case_data['destination'], date_formatting, date_formatting_dt, create_folder=False)
            destination = S_or_Z_drive(destination)
            
            date_format = use_case_data['date_format'].replace("YYYY", str(date.year)).replace("MM", str(date.month).zfill(2)).replace("DD", str(date.day).zfill(2))
                
            file_name = use_case_data['file_name'].replace(use_case_data['date_format'], date_format)
            folder = destination
            destination = destination+file_name
            if os.path.exists(folder) and df.shape[0] > 0:
                df.to_excel(destination, index=False, sheet_name='export')
        shutil.move(output_file,output_file_dest)