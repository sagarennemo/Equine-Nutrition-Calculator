import re

import questionary
from questionary import Choice
from rich.console import Console
from rich.table import Table

import models
import requirement_calculations as calc
from file_reader import load_context
from optimizer import optimize_ration

NUTRIENT_LABELS = {
    "energy_mj_per_kg_dm": "Energy (MJ/day)",
    "digestible_protein_g_per_kg_dm": "Digestible Protein (g/day)",
    "calcium_g_per_kg_dm": "Calcium (g/day)",
    "phosphorus_g_per_kg_dm": "Phosphorus (g/day)",
    "magnesium_g_per_kg_dm": "Magnesium (g/day)",
    "salt_g_per_kg_dm": "Salt (g/day)",
    "copper_mg_per_kg_dm": "Copper (mg/day)",
    "zinc_mg_per_kg_dm": "Zinc (mg/day)",
    "manganese_mg_per_kg_dm": "Manganese (mg/day)",
    "iron_mg_per_kg_dm": "Iron (mg/day)",
    "selenium_mg_per_kg_dm": "Selenium (mg/day)",
}

hay_analysis = models.HayAnalysis(
    dry_matter_pct=66,
    energy_mj_per_kg_dm=9.2,
    digestible_protein_g_per_kg_dm=60,
    calcium_g_per_kg_dm=2.1,
    phosphorus_g_per_kg_dm=1.6,
    magnesium_g_per_kg_dm=1.0,
    copper_mg_per_kg_dm=4.0,
    zinc_mg_per_kg_dm=22.7,
    manganese_mg_per_kg_dm=108.2,
    iron_mg_per_kg_dm=81.2,
    salt_g_per_kg_dm=0.5,
)


def build_profile(ctx) -> models.HorseProfile:
    ideal_weight, current_weight = weight_info()
    keeper_type = keeper_info()
    is_stallion = gender_info()
    no_grain = feed_sensitivity()
    meals = ration_amount()

    maintenance = calc.energy_maintenance(ctx, ideal_weight, keeper_type, is_stallion)

    workload = additional_energy_needs(ctx, current_weight, maintenance)

    return models.HorseProfile(
        current_weight=current_weight,
        ideal_weight=ideal_weight,
        keeper_type=keeper_type,
        is_stallion=is_stallion,
        workload_percent=workload,
        no_grain=no_grain,
        meals=meals,
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


def ration_amount():
    meals = input("How many concentrate meals per day is the horse fed? ").strip()

    while not meals.isdigit() or int(meals) <= 0:
        print("The minimum amount of meals is 1")
        meals = input("How many concentrate meals per day is the horse fed? ").strip()

    return int(meals)


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


def print_ration_table(result, epdm, mn):
    concentrates = result.concentrates
    console = Console()

    if result.nutrient_coverage == []:
        requirements = {
            "energy_mj_per_kg_dm": epdm.total_mj,
            "digestible_protein_g_per_kg_dm": epdm.total_dcp_g,
            **{k.lower() + "_g_per_kg_dm": v for k, v in mn.macrominerals.items()},
            **{k.lower() + "_mg_per_kg_dm": v for k, v in mn.microminerals.items()},
        }
        hay_cov = result.hay_coverage if isinstance(result.hay_coverage, dict) else {}
        coverage = {
            key: models.NutrientCoverage(
                required=requirements[key],
                covered=hay_cov.get(key, 0),
                from_hay=hay_cov.get(key, 0),
            )
            for key in NUTRIENT_LABELS
            if key in requirements
        }
    else:
        coverage = result.nutrient_coverage

    conc_parts = [
        f"{c.feed.replace('_', ' ').title()}: {c.amount_kg:g} kg" for c in concentrates
    ]
    conc_str = ("  |  " + "  |  ".join(conc_parts)) if conc_parts else ""
    table = Table(title=f"Ration Result  |  Hay: {result.hay_kg:g} kg{conc_str}")

    table.add_column("Nutrient", justify="left")
    table.add_column("Required", justify="right")
    table.add_column("Covered", justify="right")
    table.add_column("From Hay", justify="right")
    for c in concentrates:
        table.add_column(c.feed.replace("_", " ").title(), justify="right")
    table.add_column("Coverage %", justify="right")

    def fmt(v):
        return f"{round(v, 1):g}"

    for key, nc in coverage.items():
        label = NUTRIENT_LABELS.get(key, key)
        cov_pct = (nc.covered / nc.required * 100) if nc.required else 0
        row = [
            label,
            fmt(nc.required),
            fmt(nc.covered),
            fmt(nc.from_hay),
            *[fmt(c.contribution.get(key, 0)) for c in concentrates],
            fmt(cov_pct),
        ]
        table.add_row(*row)

    console.print(table)

    if result.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for w in result.warnings:
            console.print(f"  {w}")


def main():
    ctx = load_context()
    profile = build_profile(ctx)

    epdm = calc.calc_energy_protein_dm(ctx, profile)
    mn = calc.calc_micro_nutrients(ctx, profile)
    result = optimize_ration(ctx, profile, hay_analysis, epdm, mn)
    print_ration_table(result, epdm, mn)


if __name__ == "__main__":
    main()
