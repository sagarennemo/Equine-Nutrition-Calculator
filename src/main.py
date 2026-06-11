import re

import questionary
from questionary import Choice
from rich.console import Console
from rich.table import Table

import models
import requirement_calculations as calc
from file_reader import load_context
from optimizer import optimize_ration

hay_analysis = models.HayAnalysis(
    dry_matter_pct=66,
    energy_mj_per_kg_dm=9.2,
    digestible_protein_per_kg_dm=60,
    calcium_g_per_kg_dm=2.1,
    phosphorus_g_per_kg_dm=1.6,
    magnesium_g_per_kg_dm=1.0,
    copper_mg_per_kg_dm=4.0,
    zinc_mg_per_kg_dm=22.7,
    manganese_mg_per_kg_dm=108.2,
    iron_mg_per_kg_dm=81.2,
    sodium_g_per_kg_dm=0.2,
)


def build_profile(ctx) -> models.HorseProfile:
    ideal_weight, current_weight = weight_info()
    keeper_type = keeper_info()
    is_stallion = gender_info()
    no_grain = feed_sensitivity()

    maintenance = calc.energy_maintenance(ctx, ideal_weight, keeper_type, is_stallion)

    workload = additional_energy_needs(ctx, current_weight, maintenance)

    return models.HorseProfile(
        current_weight=current_weight,
        ideal_weight=ideal_weight,
        keeper_type=keeper_type,
        is_stallion=is_stallion,
        workload_percent=workload,
        no_grain=no_grain,
    )


def weight_info():

    current_weight = input("Input the horse's weight in kg: ").strip()

    while not current_weight.isdigit() or int(current_weight) <= 0:
        print("Weight must be a positive integer.")
        current_weight = input("Input the horse's weight in kg: ").strip()

    current_weight = int(current_weight)

    is_ideal = questionary.confirm("Is the horse at ideal weight?").ask()

    if not is_ideal:
        ideal_weight = input("What is the horse's ideal weight in kg? ").strip()

        while not ideal_weight.isdigit() or int(ideal_weight) <= 0:
            print("Ideal weight must be a positive integer.")
            ideal_weight = input("What is the horse's ideal weight in kg? ").strip()

        ideal_weight = int(ideal_weight)
        print("Energy requirements will be calculated based on ideal weight.")

    else:
        ideal_weight = current_weight

    return ideal_weight, current_weight


def keeper_info():
    ask_keeper_type = questionary.select(
        "How does the horse maintain its weight?",
        choices=[
            "Gains Weight Easily (easy keeper)",
            "Maintains Weight Normally (normal keeper)",
            "Has Difficulty Gaining Weight (hard keeper)",
        ],
    ).ask()

    match = re.search(r"\b(easy|normal|hard)", ask_keeper_type)
    keeper_type = match.group(1) + "_keeper"

    return keeper_type


def gender_info():
    return questionary.confirm("Is the horse a stallion?").ask()


def additional_energy_needs(ctx, current_weight, maintenance):
    data = ctx.energy_protein

    choices = [
        Choice("Maintenance (No additional energy)", value="maintenance"),
        Choice("Light work (25%)", value="light"),
        Choice("Moderate (50%)", value="moderate"),
        Choice("Hard (75%)", value="hard"),
        Choice("Very Hard (120%)", value="very_hard"),
        Choice("Advanced", value="advanced"),
    ]

    workload = questionary.select(
        "Select workload level of the horse (energy requirement increase)",
        choices=choices,
    ).ask()

    if workload == "advanced":
        try:
            walk_miutes = int(
                input("Average minutes of walking/day (enter 0 if none): ")
            )
            trot_canter = int(input("Average minutes of trot/canter/gallop per day: "))
            days = int(input("How many days a week? "))

            walk_miutes = (walk_miutes * days) / 7
            trot_canter = (trot_canter * days) / 7

            additional_mj = (current_weight / 100) * (
                (0.2 * (walk_miutes / 10)) + (1.3 * (trot_canter / 10))
            )

            workload_percent = round((additional_mj / maintenance) * 100)

        except ValueError:
            print("Must be a numeric values")

    elif workload == "maintenance":
        workload_percent = 0

    else:
        workload_percent = data["energy_maintenance"]["work_factors"][workload] * 100

    return workload_percent


def feed_sensitivity():
    return questionary.confirm("Does the horse have a grain sensitivity?").ask()


def nutrients_table(epdm, mn):
    table = Table(title="Horse Nutrient Requirements")

    table.add_column("Nutrient", justify="center")
    table.add_column("Target Intake", justify="center")
    table.add_column("Unit", justify="center")

    table.add_row("Dry Matter", str(epdm.dry_matter), "kg/day")
    table.add_row("Metabolizable Energy", str(epdm.total_mj), "MJ/day")
    table.add_row("Digestible Crude Protein", str(epdm.total_dcp_g), "grams/day")

    for mineral in mn.macrominerals:
        value = mn.macrominerals[mineral]
        unit = mn.macro_mineral_units[mineral]
        if value - int(value) <= 0:
            value = int(value)
        else:
            value = round(value, 1)
        table.add_row(mineral.capitalize(), str(value), unit)

    for mineral in mn.microminerals:
        value = mn.microminerals[mineral]
        unit = mn.micro_mineral_units[mineral]
        if value - int(value) <= 0:
            value = int(value)
        else:
            value = round(value, 1)
        table.add_row(mineral.capitalize(), str(value), unit)

    console = Console()
    console.print(table)


def main():
    ctx = load_context()
    profile = build_profile(ctx)

    epdm = calc.calc_energy_protein_dm(ctx, profile)
    mn = calc.calc_micro_nutrients(ctx, profile)
    nutrients_table(epdm, mn)


if __name__ == "__main__":
    main()
