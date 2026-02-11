from glob import glob
import shutil
import os
from loguru import logger
import datetime
import re
import pandas as pd
from zipfile import ZipFile
from typing import List, Union


def _ensure_list_destination(destination: Union[str, List[str]]) -> List[str]:
    if isinstance(destination, list):
        return destination
    return [destination]


def _apply_filename_transform(original_filename: str, transform: dict) -> str:
    """Apply transformations to a filename (e.g., date offsets).

    Args:
        original_filename: The original filename (without path).
        transform: A dict with transformation rules, e.g.:
            {"date_offset_days": 1, "date_format": "YYYYMMDD", "date_format_dt": "%Y%m%d"}

    Returns:
        The transformed filename.
    """
    if not transform:
        return original_filename

    date_offset = transform.get("date_offset_days", 0)
    if date_offset == 0:
        return original_filename

    date_format = transform.get("date_format", "YYYYMMDD")
    date_format_dt = transform.get("date_format_dt", "%Y%m%d")

    # Build regex to extract date from filename
    if " " in date_format:
        regex_search = r"(\d{2}(\s)\d{2}(\s)\d{4})"
    elif "_" not in date_format:
        regex_search = r"(\d{" + str(len(date_format)) + "})"
    elif len(date_format) == 8:
        regex_search = r"(\d{2}(_)\d{2}(_)\d{2})"
    elif len(date_format) == 10:
        regex_search = r"(\d{2}(_)\d{2}(_)\d{4})"
    else:
        return original_filename

    match = re.search(regex_search, original_filename)
    if not match:
        logger.warning(f"Could not extract date from filename {original_filename} using format {date_format}")
        return original_filename

    date_str = match.group(0)
    try:
        date_obj = datetime.datetime.strptime(date_str, date_format_dt)
        new_date = date_obj + datetime.timedelta(days=date_offset)
        new_date_str = new_date.strftime(date_format_dt)
        new_filename = original_filename.replace(date_str, new_date_str)
        logger.debug(f"Transformed filename: {original_filename} -> {new_filename} (offset: {date_offset} days)")
        return new_filename
    except Exception as e:
        logger.warning(f"Failed to apply date offset to {original_filename}: {e}")
        return original_filename


def _copy_to_destinations(src: str, dests: List[str], transforms: Union[List[dict], None] = None) -> None:
    """Copy a file to multiple destination directories with optional filename transformations.

    Each destination is treated as a folder; the source filename is preserved or transformed.

    Args:
        src: Source file path.
        dests: List of destination directories.
        transforms: Optional list of transformation dicts (one per destination).
    """
    fname = os.path.basename(src)
    for i, dest in enumerate(dests):
        try:
            os.makedirs(dest, exist_ok=True)
            # Apply transformation if provided
            target_name = fname
            if transforms and i < len(transforms) and transforms[i]:
                target_name = _apply_filename_transform(fname, transforms[i])
            shutil.copy2(src, os.path.join(dest, target_name))
            logger.info(f"Copied {fname} to {dest} as {target_name}")
        except Exception as e:
            logger.warning(f"Failed to copy {fname} to {dest}: {e}")


def move_single_file(source: str, destination: Union[str, List[str]], destination_transforms: Union[List[dict], None] = None):
    """Move a file to destination(s) with optional filename transformations.

    Args:
        source: Source file path.
        destination: Either a string (single destination) or a list of destination paths.
        destination_transforms: Optional list of transformation dicts (one per destination).
            Each dict can contain:
                - "date_offset_days": int (number of days to add/subtract from date in filename)
                - "date_format": str (e.g., "YYYYMMDD")
                - "date_format_dt": str (e.g., "%Y%m%d")
    """
    source = str(source)
    source_dir = os.path.dirname(source)
    file_name_indiv = os.path.basename(source)

    dest_list = _ensure_list_destination(destination)
    primary = dest_list[0]
    secondary = dest_list[1:]

    # Ensure primary dir exists
    try:
        os.makedirs(primary, exist_ok=True)
    except Exception:
        # best-effort; network paths may not allow mkdir
        pass

    try:
        # If there are secondary destinations, copy the file there first
        if secondary:
            # Extract transforms for secondary destinations (skip primary transform at index 0)
            secondary_transforms = None
            if destination_transforms and len(destination_transforms) > 1:
                secondary_transforms = destination_transforms[1:]
            _copy_to_destinations(source, secondary, secondary_transforms)

        # Move the original to the primary destination (with optional transformation)
        primary_target_name = file_name_indiv
        if destination_transforms and len(destination_transforms) > 0 and destination_transforms[0]:
            primary_target_name = _apply_filename_transform(file_name_indiv, destination_transforms[0])

        shutil.move(source, os.path.join(primary, primary_target_name))
        logger.success(f"Moved {file_name_indiv} to {primary} as {primary_target_name}")
    except FileExistsError:
        logger.critical(f"File {primary_target_name} already exists in {primary}")
    except FileNotFoundError:
        logger.critical(f"File {file_name_indiv} not found in {source_dir}")
    except Exception as e:
        logger.critical(f"Error: {e} with {file_name_indiv} in {source_dir}")


def extract_date_from_file_and_replace_date_in_destination(file_name: str, destination: Union[str, List[str]], date_formatting: str, date_formatting_dt: str, create_folder = True):
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
        date = datetime.datetime.strptime(date, date_formatting_dt)
        year = date.year
        month = date.month
        day = date.day

        # destination may be a list; process each
        dests = _ensure_list_destination(destination)
        replaced = []
        for dest in dests:
            d = dest.replace("YYYY", str(year))
            d = d.replace("YY", str(year)[2:])
            d = d.replace("MM", str(month).zfill(2))
            d = d.replace("DD", str(day).zfill(2))
            if create_folder:
                try:
                    os.makedirs(d, exist_ok=True)
                except Exception:
                    # network paths might not allow mkdir; continue best-effort
                    pass
            replaced.append(d)
        # if single dest return string for backward compatibility
        if len(replaced) == 1:
            return replaced[0], date
        return replaced, date
    return destination, None


def move_inputs(data: dict, source_dir: str):
    # setup the logging
    for use_case, use_case_data in data.items():
        file_name = use_case_data['inputs']['name']
        destination = use_case_data['inputs']['destination']
        destination_transforms = use_case_data['inputs'].get('destination_transforms')
        has_date_formatting = True if use_case_data['inputs'].get(
            'date_formatting') else False
        files = glob(f"{source_dir}/{file_name}")
        
        if len(files) > 0:
            logger.info(f'---------{use_case} inputs---------')
            logger.info(f"Found {len(files)} files for {use_case}")
            try:
                for file in files:
                    # check if use_case_data['inputs']['date_formatting'] exists
                    if has_date_formatting:
                        date_formatting = use_case_data['inputs']['date_formatting']
                        date_formatting_dt = use_case_data['inputs']['date_formatting_dt']
                        destination, date = extract_date_from_file_and_replace_date_in_destination(
                            file, destination, date_formatting, date_formatting_dt)
                        if date is None:
                            logger.warning(f"Could not parse date from filename {file}; using unmodified destination")
                    # move_single_file now supports list destinations and transforms
                    move_single_file(file, destination, destination_transforms)
            except Exception as e:
                logger.critical(f"Error: {e} with {file} in {source_dir}")
                continue


def lab_appeals_merged(data:dict, destination:str, date:datetime.datetime):
    logger.info(f'----------lab appeals merged files---------')
    # date may be a datetime; ensure it's valid
    if date is None:
        logger.warning('No date provided to lab_appeals_merged; skipping')
        return
    date_formatting_dt = data.get('date_formatting_dt', '%m_%d_%y')

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

def archive_folder(file, source_dir, date):
     # move the folder to the moved folder
    file_name = file.split('\\')[-1]
    pre_moved_folder_path = f'{source_dir}/{file_name}'
    moved_folder_date = date.strftime('%Y %m')
    moved_folder_dir = f'{source_dir}/moved/{moved_folder_date}/'
    # make folder if not exists
    os.makedirs(moved_folder_dir, exist_ok=True)
    moved_folder_dir = f'{moved_folder_dir}/{file_name}'
    logger.debug(f'Moving folder from {pre_moved_folder_path} to {moved_folder_dir}')

    try:
        os.rename(pre_moved_folder_path, moved_folder_dir)
    except FileExistsError:
        logger.warning(f'{moved_folder_dir} already exists')
    except PermissionError:
        logger.critical(f'Permission denied to move {pre_moved_folder_path}')

def move_outputs(data: dict, source_dir: str):
    for use_case, use_case_data in data.items():
        files = glob(os.path.join(source_dir, use_case_data['zip_name']))
        
        if len(files) == 0:
            continue
        else:
            logger.info(f'---------{use_case} outputs---------')
            logger.info(f"Found {len(files)} output files for {use_case}")
        
            try:
                for file in files:
                    # get the date from the file name so it can be used for the destination folder
                    date_formatting = use_case_data['date_formatting']
                    date_formatting_dt = use_case_data['date_formatting_dt']
                    destination = use_case_data['destination']
                    destination, date = extract_date_from_file_and_replace_date_in_destination(
                        file, destination, date_formatting, date_formatting_dt)

                    # normalize destinations
                    dest_list = _ensure_list_destination(destination)
                    primary_dest = dest_list[0]
                    secondary_dests = dest_list[1:]

                    if date is None:
                        logger.warning(f"Could not parse date from filename {file}; skipping")
                        continue

                    if use_case == 'chargecorrection':
                        fldr_frmt = '%m%d%Y'
                        primary_dest = f'{primary_dest}{date.strftime(fldr_frmt)}/'
                    primary_dest = f'{primary_dest}{date.strftime(date_formatting_dt)}'

                    # check if destination folder exists
                    if os.path.exists(primary_dest):
                        logger.warning(f'{primary_dest} already exists')
                                               
                        # delete the file
                        # os.remove(file)
                        continue

                    # unzip the files and move them to the primary destination
                    with open(file, 'rb') as src:
                        zf = ZipFile(src)
                        folder_count = [m for m in zf.infolist() if m.filename.endswith("/")].__len__()
                        file_count = [m for m in zf.infolist() if not m.filename.endswith("/")].__len__()
                        logger.info(f'Found {folder_count} folders and {file_count} files in the zip file')
                        single_files = [m for m in zf.infolist() if not m.filename.endswith("/")]
                        file_names = [m.filename.split('/')[-1] for m in single_files]
                        folder_names = [m.filename.split('/')[0] for m in zf.infolist()]
                        for single_file in single_files:
                            zf.extract(single_file, primary_dest)
                        zf.close()

                    # If there are secondary destinations, copy the original zip there for archival
                    if secondary_dests:
                        _copy_to_destinations(file, secondary_dests)

                    if use_case == 'lab_appeals':
                        # pass the primary destination and date
                        lab_appeals_merged(use_case_data, primary_dest, date)

                    # confirm the destination folder has all the correct files and folders
                    new_file_names = []
                    new_subdir_names = []
                    for _, subdirs, files in os.walk(primary_dest):
                        new_file_names += files
                        new_subdir_names += subdirs
                    
                    logger.info(f'Found {len(new_subdir_names)} folders and {len(new_file_names)} files in the zip file')
                    logger.debug(f'Missing files: {set(file_names) - set(new_file_names) if set(file_names) - set(new_file_names) else "None"}')
                    logger.debug(f'Missing folders: {set(folder_names) - set(new_subdir_names) if set(folder_names) - set(new_subdir_names) else "None"}')

                    if len(new_file_names) >= file_count and len(new_subdir_names) >= folder_count:
                        if len(new_file_names) == file_count and len(new_subdir_names) == folder_count:
                            logger.success(f'Moved {folder_count} folders and {file_count} files into the destination')
                            logger.info(f'New folder contains {len(new_subdir_names)} folders and {len(new_file_names)} files into the destination')
                        else:
                            logger.warning(f'Moved {folder_count} folders and {file_count} files into the destination')
                            logger.info(f'New folder contains {len(new_subdir_names)} folders and {len(new_file_names)} files into the destination')
                        archive_folder(file, source_dir, date)
                       
                    elif len(new_file_names) < file_count:
                        logger.critical(f"Failed to move all files to {primary_dest}")
                        logger.critical(f"Expected {file_count} files but only found {len(new_file_names)}")
                    elif len(new_subdir_names) < folder_count:
                        if len(new_file_names) == file_count:
                            logger.info(f'Empty folder not transferred')
                            # move the folder to the moved folder
                            archive_folder(file, source_dir, date)
                        else:
                            logger.critical(f"Failed to move all subdirectories to {primary_dest}")
            except Exception as e:
                logger.critical(f"Error: {e} with {file} in {source_dir}")
                continue

def parse_output_files(data:dict, source_dir:str):
    
    lab_outputs = glob(source_dir + "/Labappeals Output*.xlsx")
    if len(lab_outputs) > 0:
        logger.info(f'parsing lab appeals output file')
        for output_file in lab_outputs:
            destination, date = extract_date_from_file_and_replace_date_in_destination(
                output_file,
                '\\NASDATA201\\SHAREDATA\\NSHS-CENTRAL-LAB\\SHARED\\BILLING\\RPA Medical Records Denials\\Bot Output Files',
                'MM DD YYYY',
                '%m %d %Y',
                create_folder=False,
            )
            if date is None:
                logger.warning(f"Could not parse date from filename {output_file}; skipping lab appeals move")
                continue
            dest_list = _ensure_list_destination(destination)
            primary_dest = dest_list[0]
            file_name_base = os.path.basename(output_file).split(' - ')[0]
            file_name = file_name_base + " - " + date.strftime('%m%d%Y') + ".xlsx"
            shutil.move(output_file, f'{primary_dest}/{file_name}')
    
    output_files = glob(source_dir + "/Outbound*.xlsx")
    for output_file in output_files:
        try:
            main = pd.read_excel(output_file, sheet_name=0)
            output_file_dest = output_file.replace(source_dir, '\\\\NT2KWB972SRV03\\SHAREDATA\\CPP-Data\\Sutherland RPA\\Combined Outputs')
            for use_case, use_case_data in data.items():
                logger.info(f'parsing output file for {use_case}')
                df = main[main['BotName'] == use_case_data['BotName']]

                date_formatting = 'MMDDYYYY'
                date_formatting_dt = '%m%d%Y'

                destination, date = extract_date_from_file_and_replace_date_in_destination(
                    output_file, use_case_data['destination'], date_formatting, date_formatting_dt
                )

                if date is None:
                    logger.warning(f"Could not parse date from filename {output_file} for {use_case}; skipping")
                    continue

                dest_list = _ensure_list_destination(destination)
                primary_dest = dest_list[0]
                secondary = dest_list[1:]

                date_format = use_case_data['date_format'].replace("YYYY", str(date.year)).replace("MM", str(date.month).zfill(2)).replace("DD", str(date.day).zfill(2))
                file_name = use_case_data['file_name'].replace(use_case_data['date_format'], date_format)
                folder = primary_dest
                destination_path = os.path.join(primary_dest, file_name)
                if os.path.exists(folder) and df.shape[0] > 0 and not os.path.exists(destination_path):
                    df.to_excel(destination_path, index=False, sheet_name='export')
                    # copy the saved file to any secondary destinations
                    if secondary:
                        _copy_to_destinations(destination_path, secondary)
                elif not os.path.exists(folder):
                    logger.error(f"Destination folder {folder} does not exist for {use_case}")
                    continue
                elif df.shape[0] == 0:
                    logger.warning(f"No data found for {use_case} in {output_file}")
                    continue
        except Exception as e:
            logger.critical(f"Error: {e} with {output_file} in {source_dir}")
            continue
        finally:
            try:
                shutil.move(output_file, output_file_dest)
            except Exception as e:
                logger.warning(f"Failed to move processed output file {output_file} to {output_file_dest}: {e}")


    
def parse_epic_output_files(data: dict, source_dir: str):
    """Parse EPIC_Outbound*.xlsx and distribute sheets per mapping.

    This mirrors parse_output_files but targets files named EPIC_Outbound*.xlsx
    and uses the provided mapping (typically loaded from epic_outbound_shs.json).
    """
    epic_output_files = glob(os.path.join(source_dir, "EPIC_Outbound*.xlsx"))
    for output_file in epic_output_files:
        try:
            main = pd.read_excel(output_file, sheet_name=0)
            output_file_dest = output_file.replace(
                source_dir,
                "\\\\NT2KWB972SRV03\\SHAREDATA\\CPP-Data\\Sutherland RPA\\Combined Outputs",
            )

            for use_case, use_case_data in data.items():
                logger.info(f'parsing EPIC output file for {use_case}')
                df = main[main['BotName'] == use_case_data['BotName']]

                # EPIC outbound files also use MMDDYYYY in filename
                date_formatting = 'MMDDYYYY'
                date_formatting_dt = '%m%d%Y'

                destination, date = extract_date_from_file_and_replace_date_in_destination(
                    output_file, use_case_data['destination'], date_formatting, date_formatting_dt
                )

                if date is None:
                    logger.warning(f"Could not parse date from filename {output_file} for {use_case}; skipping")
                    continue

                dest_list = _ensure_list_destination(destination)
                primary_dest = dest_list[0]
                secondary = dest_list[1:]

                date_format = (
                    use_case_data['date_format']
                    .replace("YYYY", str(date.year))
                    .replace("MM", str(date.month).zfill(2))
                    .replace("DD", str(date.day).zfill(2))
                )
                file_name = use_case_data['file_name'].replace(use_case_data['date_format'], date_format)
                folder = primary_dest
                destination_path = os.path.join(primary_dest, file_name)

                if os.path.exists(folder) and df.shape[0] > 0 and not os.path.exists(destination_path):
                    df.to_excel(destination_path, index=False, sheet_name='export')
                    # copy the saved file to any secondary destinations
                    if secondary:
                        _copy_to_destinations(destination_path, secondary)
                elif not os.path.exists(folder):
                    logger.error(f"Destination folder {folder} does not exist for {use_case}")
                    continue
                elif df.shape[0] == 0:
                    logger.warning(f"No data found for {use_case} in {output_file}")
                    continue
        except Exception as e:
            logger.critical(f"Error: {e} with {output_file} in {source_dir}")
            continue
        finally:
            try:
                shutil.move(output_file, output_file_dest)
            except Exception as e:
                logger.warning(f"Failed to move processed EPIC output file {output_file} to {output_file_dest}: {e}")


