from glob import glob
import json
import os
from loguru import logger

from functions import move_inputs, move_outputs, parse_output_files


if __name__ == "__main__":
    # check if connected to MDrive
    if not os.path.exists('M:/'):
        logger.critical("M Drive not connected")
    
    inputs_dir = r'M:\CPP-Data\Sutherland RPA\Northwell Process Automation ETM Files\GOA\Inputs'
    if len(glob(inputs_dir+ '/*')) > 0:
        # read the input file
        with open('inputs.json', 'r') as file:
            inputs = json.load(file)
        with open('outputs.json', 'r') as file:
            outputs = json.load(file)
        with open('./outbound_shs.json') as file:
            shs = json.load(file)

        # move the input files to their respective destinations
        move_inputs(inputs, inputs_dir)
        # move_outputs(outputs, inputs_dir)
        parse_output_files(shs, inputs_dir)
    else:
        logger.critical("No files found in the inputs directory")
    
  
