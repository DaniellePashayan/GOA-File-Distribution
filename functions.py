def move_single_file(source:str, destination:str):
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

def move_inputs(json_data: dict, source_dir: str):
    # setup the logging
    logger.add("logs/inputs.log", rotation="14 days")

    for use_case, use_case_data in data.items():
        logger.info(f"Moving files for {use_case}")
        file_name = use_case_data['inputs']['name']
        destination = use_case_data['inputs']['destination']
        has_date_formatting = True if use_case_data['inputs'].get('date_formatting') else False
        # logger.info(f'{has_date_formatting=}')
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
                    if date_formatting and date_formatting_dt:
                        # extract date from file name using value from date_formatting
                        regex_search = "(\d{"+str(len(date_formatting))+"})"
                        match = re.search(regex_search, file)
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
                move_single_file(file, destination)

