import math
import re
import questionary
from pathlib import Path
from file_reader import *

# To avoid file path issues on different devices
BASE_DIR = Path(__file__).parent.parent
VITAMINS_FILE_PATH = BASE_DIR / "dataset" / "vitamins.csv"
MACRO_FILE_PATH = BASE_DIR / "dataset" / "macrominerals.csv"
MICRO_FILE_PATH = BASE_DIR / "dataset" / "microminerals.csv"
ENERGY_PROTEIN_FILE_PATH = BASE_DIR / "dataset" / "energy_protein.json"

def weight_info():
    try:
        current_weight = int(input("Input the horses weight in kg: "))
        ideal_weight = questionary.confirm("Is the horse ideal weight?").ask()

        if not ideal_weight:
            ideal_weight = int(input("What is the horses ideal weight?"))
            print("The horses energy needs will be calculated after the ideal weight")
            return ideal_weight, current_weight
        
        else:
            ideal_weight = current_weight
        return ideal_weight, current_weight

    except ValueError:
        print("Weight needs to be a number.")


def keeper_info():
    ask_keeper_type = questionary.rawselect(
        "How does the horse maintain its weight?",
        choices = ["Gains Weight Easily (easy keeper)", 
                    "Maintains Weight Normally (normal keeper)", 
                    "Has Difficulty Gaining Weight (hard keeper)"]).ask()

    match = re.search(r"\b(easy|norma|hard)", ask_keeper_type)
    keeper_type = match.group(1) + "_keeper"

    return keeper_type

def gender_info():
    return questionary.confirm("Is the horse a stallion?").ask()

def additional_energy_needs():
    workload = questionary.rawselect(
        "Select workload level of the horse (energy requirement increase)",
        choices = ["Maintenance (No additional energy)",
                   "Light work (25%)",
                   "Moderate (50%)",
                   "Hard (75%)",
                   "Very Hard (120%)",
                   "Custom"]).ask()
    
    if workload == "Custom":
        try:
            workload = int(input("Enter estimated energy increase (%) above maintenance: "))
        except ValueError:
            print("Custom Workload must be a numeric value")
    return workload
    



