from glob import glob
import json

from functions import move_single_file, move_inputs


if __name__ == "__main__":
    # check if connected to MDrive
    if not os.path.exists('M:/'):
        logger.critical("M Drive not connected")
    
    inputs_dir = r'M:\CPP-Data\Sutherland RPA\Northwell Process Automation ETM Files\GOA\Inputs'
    if len(glob(inputs_dir+ '/*')) > 0:
        # read the input file
        with open('inputs.json', 'r') as file:
            data = json.load(file)

        # move the input files to their respective destinations
        move_inputs(data, inputs_dir)
    else:
        logger.critical("No files found in the inputs directory")
    
  
