from glob import glob
import shutil
import os
from loguru import logger
import datetime
import re
import pandas as pd
from zipfile import ZipFile
from tqdm import tqdm


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
    if " " in date_formatting: # checks for dates in MM DD YYYY format
        regex_search = r"(\d{2}(\s)\d{2}(\s)\d{4})"
    elif "_" not in date_formatting: # checks for dates in MMDDYYYY format
        regex_search = r"(\d{"+str(len(date_formatting))+"})"
    elif len(date_formatting) == 8: # checks for dates in MM_DD_YY format
        regex_search = r"(\d{2}(_)\d{2}(_)\d{2})"
    elif len(date_formatting) == 10: # checks for dates in MM_DD_YYYY format
        regex_search = r"(\d{2}(_)\d{2}(_)\d{4})"
            
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
            "YY", str(year)[2:])
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
    for use_case, use_case_data in data.items():
        logger.info(f'---------{use_case} inputs---------')
        file_name = use_case_data['inputs']['name']
        destination = use_case_data['inputs']['destination']
        has_date_formatting = True if use_case_data['inputs'].get(
            'date_formatting') else False
        files = glob(f"{source_dir}/{file_name}")
        logger.info(f"Found {len(files)} files for {use_case}")
        if len(files) > 0:
            try:
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
                    move_single_file(file, destination)
            except Exception as e:
                logger.critical(f"Error: {e} with {file} in {source_dir}")
                continue


def move_outputs(data: dict, source_dir: str):
    
    for use_case, use_case_data in data.items():
        files = glob(os.path.join(source_dir, use_case_data['zip_name']))
        logger.info(f"Found {len(files)} output files for {use_case}")

        if len(files) > 0:
            logger.info(f'---------{use_case} outputs---------')
            try:
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
                
                    # unzip the files and move them to the destination
                    with open(file, 'rb') as src:
                        zf = ZipFile(src)
                        folder_count = [m for m in zf.infolist() if m.filename.endswith("/")].__len__()
                        file_count = [m for m in zf.infolist() if not m.filename.endswith("/")].__len__()
                        logger.info(f'Found {folder_count} folders and {file_count} files in the zip file')
                        single_files = [m for m in zf.infolist() if not m.filename.endswith("/")]
                        for single_file in single_files:
                            zf.extract(single_file, destination)
                        zf.close()
                    
                    if use_case == 'lab_appeals':
                        lab_appeals_merged(use_case_data, destination, date)
                    
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
                        except PermissionError:
                            logger.critical(f'Permission denied to move {pre_moved_folder_path}')
                            continue
                    elif new_file_count < file_count:
                        logger.critical(f"Failed to move all files to {destination}")
                        logger.critical(f"Expected {file_count} files but only found {new_file_count}")
                    elif new_subdir_count < folder_count:
                        logger.critical(f"Failed to move all subdirectories to {destination}")
            except Exception as e:
                logger.critical(f"Error: {e} with {file} in {source_dir}")
                continue

def parse_output_files(data:dict, source_dir:str):
    
    lab_outputs = glob(source_dir + "/Labappeals Output*.xlsx")
    if len(lab_outputs) > 0:
        logger.info(f'parsing lab appeals output file')
        for output_file in lab_outputs:
            destination, date = extract_date_from_file_and_replace_date_in_destination(output_file, '\\\\NASDATA201\\SHAREDATA\\NSHS-CENTRAL-LAB\\SHARED\\BILLING\\RPA Medical Records Denials\\Bot Output Files', 'MM DD YYYY', '%m %d %Y', create_folder=False)
            file_name_base = os.path.basename(output_file).split(' - ')[0]
            file_name = file_name_base + " - " + date.strftime('%m%d%Y') + ".xlsx"
            shutil.move(output_file,f'{destination}/{file_name}')
    
    output_files = glob(source_dir + "/Outbound*.xlsx")
    for output_file in output_files:
        try:
            main = pd.read_excel(output_file, sheet_name='export')
            output_file_dest = output_file.replace(source_dir,'\\\\NT2KWB972SRV03\\SHAREDATA\\CPP-Data\\Sutherland RPA\\Combined Outputs')
            for use_case, use_case_data in data.items():
                logger.info(f'parsing output file for {use_case}')
                df = main[main['BotName'] == use_case_data['BotName']]
                
                date_formatting = 'MMDDYYYY'
                date_formatting_dt = '%m%d%Y'
                    
                destination,date = extract_date_from_file_and_replace_date_in_destination(output_file, use_case_data['destination'], date_formatting, date_formatting_dt, create_folder=False)
                
                date_format = use_case_data['date_format'].replace("YYYY", str(date.year)).replace("MM", str(date.month).zfill(2)).replace("DD", str(date.day).zfill(2))
                    
                file_name = use_case_data['file_name'].replace(use_case_data['date_format'], date_format)
                folder = destination
                destination = destination+file_name
                if os.path.exists(folder) and df.shape[0] > 0:
                    df.to_excel(destination, index=False, sheet_name='export')
        except Exception as e:
            logger.critical(f"Error: {e} with {output_file} in {source_dir}")
            continue
        shutil.move(output_file,output_file_dest)
        
def lab_appeals_merged(data:dict, destination:str, date:datetime.datetime):
    logger.info(f'----------lab appeals merged files---------')
    print(date)
    date_formatting_dt = data['date_formatting_dt']
    
    merged_date = date.strftime('%m_%d_%y')
    merged_date_full_year = date.strftime('%m_%d_%Y')
    merged_path = f'\\\\NT2KWB972SRV03\\SHAREDATA\\CPP-Data\\Sutherland RPA\\Northwell Process Automation ETM Files\\GOA\\Lab Appeals\\{merged_date}\\Labappeals_{merged_date_full_year}.zip'
    try:
        zf = ZipFile(merged_path)
        folders = [m for m in zf.namelist() if not m.endswith("/") and "_Merged" in m]
        for folder in folders:
            zf.extract(folder, destination)
    except FileNotFoundError:
        logger.critical(f'Lab Appeals Merged file not found for {date.strftime(date_formatting_dt)}')