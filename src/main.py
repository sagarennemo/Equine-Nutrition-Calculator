import re
import questionary
from questionary import Choice
from models import *
from pathlib import Path
from file_reader import *

# To avoid file path issues on different devices
BASE_DIR = Path(__file__).parent.parent
VITAMINS_FILE_PATH = BASE_DIR / "dataset" / "vitamins.csv"
MACRO_FILE_PATH = BASE_DIR / "dataset" / "macrominerals.csv"
MICRO_FILE_PATH = BASE_DIR / "dataset" / "microminerals.csv"
ENERGY_PROTEIN_FILE_PATH = BASE_DIR / "dataset" / "energy_protein.json"


def load_context() -> DataContext:
    return DataContext(energy_protein=json_reader(ENERGY_PROTEIN_FILE_PATH),
                       macro=csv_reader(MACRO_FILE_PATH),
                       micro=csv_reader(MICRO_FILE_PATH),
                       vitamins=csv_reader(VITAMINS_FILE_PATH))


def build_profile(ctx) -> HorseProfile:
    ideal_weight, current_weight = weight_info()
    keeper_type = keeper_info()
    is_stallion = gender_info()
    workload = additional_energy_needs(ctx)

    return HorseProfile(
        current_weight=current_weight,
        ideal_weight=ideal_weight,
        keeper_type=keeper_type,
        is_stallion=is_stallion,
        workload_percent=workload)


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

    match = re.search(r"\b(easy|normal|hard)", ask_keeper_type)
    keeper_type = match.group(1) + "_keeper"

    return keeper_type

def gender_info():
    return questionary.confirm("Is the horse a stallion?").ask()

def additional_energy_needs(ctx):
    data = ctx.energy_protein

    choices = [
        Choice("Maintenance (No additional energy)", value="maintenance"),
        Choice("Light work (25%)", value="light"),
        Choice("Moderate (50%)", value="moderate"),
        Choice("Hard (75%)", value="hard"),
        Choice("Very Hard (120%)", value="very_hard"),
        Choice("Custom", value="custom")]
    
    workload = questionary.select(
        "Select workload level of the horse (energy requirement increase)", choices=choices).ask()

    if workload == "custom":
        try:
            workload_percent = int(input("Enter estimated energy increase (%) above maintenance: "))
        except ValueError:
            print("Custom Workload must be a numeric value")
    
    elif workload == "maintenance":
        workload_percent = 0

    else:
        workload_percent = data["energy_maintenance"]["work_factors"][workload] * 100

    return workload_percent
    

def calc_energy_protein(ctx, profile):
    ideal_weight = profile.ideal_weight
    is_stallion = profile.is_stallion
    workload = profile.workload_percent
    keeper_type = profile.keeper_type
    
    data = ctx.energy_protein
    
    calc_ideal = ideal_weight ** 0.75

    calc_maintenance = round(data["energy_maintenance"]["keeper_type"][keeper_type] * calc_ideal)
    maintenance = round(calc_maintenance)

    if is_stallion:
       maintenance = round(calc_maintenance * 1.1)

    additional_energy = int(maintenance * (workload / 100))
    total_energy_need = maintenance + additional_energy
    protein_need = total_energy_need * data["protein"]["grams"]

    print(f"additional: {additional_energy}, maintenance: {maintenance}, total: {total_energy_need}, protein: {protein_need}")
    
    return EnergyProteinReq(maintenance_mj=maintenance,
                            additional_mj=additional_energy,
                            total_mj=total_energy_need,
                            total_dcp_g=protein_need) 

def workload_to_column(wl):
    if wl == 0:
        return "maintenance", "maintenance", "maintenance"
    elif wl < 30:
        return "lt30", "working_horses", "maintenance"
    elif wl <= 50:
        return "30-50", "working_horses", "maintenance"
    elif wl <= 75:
        return "50-75", "working_horses", "maintenance"
    elif wl <= 130:
        return "75-130", "working_horses", "very_hard_working"

def calc_micro_nutrients(ctx, profile):
    wl = profile.workload_percent
    weight_factor = profile.ideal_weight / 100
    macro_col, micro_col, vitamin_col = workload_to_column(wl)

    macro_df = ctx.macro.set_index("mineral")
    micro_df = ctx.micro.set_index("mineral")
    vitamin_df = ctx.vitamins.set_index("vitamin")


    vitamins = (vitamin_df[vitamin_col]* weight_factor).to_dict()
    macro_minerals = (macro_df[macro_col]* weight_factor).to_dict()
    micro_minerals = (micro_df[micro_col]* weight_factor).to_dict()

    return MicroNutrients(vitamins=vitamins,
                          microminerals=micro_minerals,
                          macrominerals=macro_minerals)

def main():
    ctx = load_context()
    profile = build_profile(ctx)

    calc_energy_protein(ctx, profile)
    calc_micro_nutrients(ctx, profile)

if __name__ == "__main__":
    main()




