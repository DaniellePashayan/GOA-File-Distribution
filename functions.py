import shutil
import os
from loguru import logger
import datetime
import re


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


def extract_date_from_file_and_replace_date_in_destination(file_name: str, destination: str, date_formatting: str, date_formatting_dt: str):
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
        os.makedirs(destination, exist_ok=True)
    return destination, date


def move_inputs(json_data: dict, source_dir: str):
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
                        file, date_formatting, date_formatting_dt)
                move_single_file(file, destination)


def move_outputs(data: dict, source_dir: str):
    logger.add("logs/outputs.log", rotation="14 days")
    for use_case, use_case_data in data.items():
        files = glob(os.path.join(source_dir, use_case_data['zip_name']))
        logger.info(f"Found {len(files)} files for {use_case}")

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
                if not os.path.exists(destination):
                    # unzip the file
                    shutil.unpack_archive(file, destination)
                # delete zip
                os.remove(file)
