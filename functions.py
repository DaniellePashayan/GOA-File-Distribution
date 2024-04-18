from glob import glob
import shutil
import os
from loguru import logger
import datetime
import re
import pandas as pd
from zipfile import ZipFile


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
    logger.add("logs/inputs.log", rotation="14 days")

    for use_case, use_case_data in data.items():
        logger.info(f"Moving files for {use_case}")
        file_name = use_case_data['inputs']['name']
        destination = use_case_data['inputs']['destination']
        has_date_formatting = True if use_case_data['inputs'].get(
            'date_formatting') else False
        files = glob(f"{source_dir}/{file_name}")
        logger.info(f"Found {len(files)} files for {use_case}")

        if len(files) > 0:
            for file in files:
                # check if use_case_data['inputs']['date_formatting'] exists
                if use_case_data['inputs'].get('date_formatting'):
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
    logger.add("logs/outputs.log", rotation="14 days")
    for use_case, use_case_data in data.items():
        logger.info('moving outputs for '+ use_case)
        files = glob(os.path.join(source_dir, use_case_data['zip_name']))
        logger.info(f"Found {len(files)} output files for {use_case}")

        if len(files) > 0:
            for file in files:
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
                
                if not os.path.exists(destination):
                    # unzip the file
                    with ZipFile(file, 'r') as zf:
                        zf.extractall(destination)
                    logger.success('moved files for '+ use_case)
                # delete zip
                zip_dest = file.replace(source_dir, 'M:/CPP-Data/Sutherland RPA/Northwell Process Automation ETM Files/GOA/Inputs/moved/')
                shutil.move(file, zip_dest)

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
            print(folder)
            destination = destination+file_name
            print(destination)
            if os.path.exists(folder) and df.shape[0] > 0:
                df.to_excel(destination, index=False, sheet_name='export')
                print('saved')
        shutil.move(output_file,output_file_dest)