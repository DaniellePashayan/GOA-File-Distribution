from glob import glob
import json
import os
from loguru import logger

from functions import move_inputs, move_outputs, parse_output_files, parse_epic_output_files


if __name__ == "__main__":
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # logger.add('.\\logs\\local_log.log', level="INFO")
        logger.add("\\\\NT2KWB972SRV03\\SHAREDATA\\CPP-Data\\Sutherland RPA\\Northwell Process Automation ETM Files\\GOA\\Inputs\\logs\\log.log",
                rotation="1 day", level="INFO", retention="90 days", compression="zip")

        drives = {
            "M": "\\\\NT2KWB972SRV03\\SHAREDATA",
            "N": "\\\\NASDATA204\\SHAREDATA\\BOT CLAIMSTATUS DATA-PHI",
            "S": "\\\\NASHCN01\\SHAREDATA",
            "Y": "\\\\NASDATA201\\SHAREDATA\\MV-RCR01\\SHARED",
            "T": "\\\\NASDATA201\\SHAREDATA\\NSHS-CENTRAL-LAB\\SHARED\\BILLING"
        }

        # check if all drives are connected
        for drive_letter, drive_path in drives.items():
            # logger.info(f"Checking if drive {drive_letter} is connected")
            # logger.info(os.path.exists(drive_path))
            if not os.path.exists(drive_path):
                logger.info(f"Drive {drive_letter} is not connected")
        if all([os.path.exists(drive_path) for drive_path in drives.values()]):
            logger.success("All drives are connected")

        inputs_dir = '\\\\NT2KWB972SRV03\\SHAREDATA\\CPP-Data\\Sutherland RPA\\Northwell Process Automation ETM Files\\GOA\\Inputs'
        if len(glob(inputs_dir+ '/*')) > 0:
            # read the input file
            with open('./json_data/inputs.json', 'r') as file:
                inputs = json.load(file)
            with open('./json_data/outputs.json', 'r') as file:
                outputs = json.load(file)
            with open('./json_data/outbound_shs.json') as file:
                shs = json.load(file)
            with open('./json_data/epic_outbound_shs.json') as file:
                epic_shs = json.load(file)

            # move the input files to their respective destinations
            move_inputs(inputs, inputs_dir)
            parse_output_files(shs, inputs_dir)
            parse_epic_output_files(epic_shs, inputs_dir)
            move_outputs(outputs, inputs_dir)
            logger.success("All files have been moved successfully")
        else:
            logger.critical("No files found in the inputs directory")
    except Exception as e:
        logger.exception(e)