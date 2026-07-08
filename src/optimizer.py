from dataclasses import asdict

from pulp import *

import models

# Energy surplus warning thresholds (fraction of requirement).
# Easy and hard keeper values follow the levels used by Krafft/PC-Horse.
# The normal keeper value is interpolated between them and is not yet
# independently verified.
ENERGY_SURPLUS = {
    "easy_keeper": 1.10,
    "normal_keeper": 1.15,  # interpolated - verify against a source
    "hard_keeper": 1.20,
}


# SLU's feed tool flags protein above 160% of requirement; a surplus
# from forage up to this level is acceptable, but concentrate-driven
# surplus should be reduced regardless.
PROTEIN_SURPLUS_MAX = 1.6

ENERGY_MAX = {
    "easy_keeper": 1.20,    # 10 pts above the 1.10 warning threshold
    "normal_keeper": 1.25,  # 10 pts above the 1.15 warning threshold
    "hard_keeper": 1.30,    # 10 pts above the 1.20 warning threshold
}


def round_to_nearest(value: float, step: float) -> float | int:
    rounded = round(value / step) * step
    if int(rounded) == rounded:
        rounded = int(rounded)
    return rounded


def contribution_calculator(source: dict, amount: float):
    return {
        "energy_mj_per_kg_dm": source["energy_mj_per_kg_dm"] * amount,
        "digestible_protein_g_per_kg_dm": source["digestible_protein_g_per_kg_dm"]
        * amount,
        "calcium_g_per_kg_dm": source["calcium_g_per_kg_dm"] * amount,
        "phosphorus_g_per_kg_dm": source["phosphorus_g_per_kg_dm"] * amount,
        "magnesium_g_per_kg_dm": source["magnesium_g_per_kg_dm"] * amount,
        "salt_g_per_kg_dm": source["salt_g_per_kg_dm"] * amount,
        "copper_mg_per_kg_dm": source["copper_mg_per_kg_dm"] * amount,
        "zinc_mg_per_kg_dm": source["zinc_mg_per_kg_dm"] * amount,
        "manganese_mg_per_kg_dm": source["manganese_mg_per_kg_dm"] * amount,
        "iron_mg_per_kg_dm": source["iron_mg_per_kg_dm"] * amount,
        "selenium_mg_per_kg_dm": source["selenium_mg_per_kg_dm"] * amount,
    }


def hay_contribution(
    hay: models.HayAnalysis,
    horse_req: models.EnergyProteinReq,
    micronutr: models.MicroNutrients,
) -> dict:

    base_deficits = {}
    hay_analysis = asdict(hay)
    hay_nutrients = contribution_calculator(hay_analysis, horse_req.dry_matter)

    for nutrient, balance in [
        (
            "energy_mj_per_kg_dm",
            hay_nutrients["energy_mj_per_kg_dm"] - horse_req.total_mj,
        ),
        (
            "digestible_protein_g_per_kg_dm",
            hay_nutrients["digestible_protein_g_per_kg_dm"] - horse_req.total_dcp_g,
        ),
    ]:
        base_deficits[nutrient] = max(0, -balance)

    for nutrient in micronutr.macrominerals:
        mineral_balance = (
            hay_nutrients[nutrient.lower() + "_g_per_kg_dm"]
            - micronutr.macrominerals[nutrient]
        )
        base_deficits[nutrient.lower() + "_g_per_kg_dm"] = max(0, -mineral_balance)

    return base_deficits, hay_nutrients


def ration_coverage(
    epdm: models.EnergyProteinReq,
    mn: models.MicroNutrients,
    hay_nutrients: dict[str, float],
    concentrate_contribution: dict[str, float],
) -> dict[str, models.NutrientCoverage]:

    horse_needs = {
        "energy_mj_per_kg_dm": epdm.total_mj,
        "digestible_protein_g_per_kg_dm": epdm.total_dcp_g,
    }
    total_coverage = dict(hay_nutrients)

    nutrient_needs_coverage = {}

    for nutrient in mn.macrominerals:
        horse_needs[nutrient.lower() + "_g_per_kg_dm"] = mn.macrominerals[nutrient]

    for nutrient in mn.microminerals:
        horse_needs[nutrient.lower() + "_mg_per_kg_dm"] = mn.microminerals[nutrient]

    for feed in concentrate_contribution:
        for nutrient in concentrate_contribution[feed]:
            total_coverage[nutrient] += concentrate_contribution[feed][nutrient]

    for nutrient in horse_needs:
        nutrient_needs_coverage[nutrient] = models.NutrientCoverage(
            required=horse_needs[nutrient],
            covered=total_coverage[nutrient],
            from_hay=hay_nutrients[nutrient],
        )

    return nutrient_needs_coverage


def generate_warnings(
    profile: models.HorseProfile,
    nutrient_coverage: dict[str, models.NutrientCoverage],
    mn: models.MicroNutrients,
    concentrates: list[str]
) -> list[str]:
    
    warnings = []

    if concentrates:
        warnings.append(
            f"This ration assumes concentrate is split across {profile.meals} meal(s) per day. "
            "Giving it all at once increases the risk of colic or hindgut disturbances."
        )

    protein = nutrient_coverage["digestible_protein_g_per_kg_dm"]

    keeper_type = profile.keeper_type
    threshold = ENERGY_SURPLUS[keeper_type]
    energy = nutrient_coverage["energy_mj_per_kg_dm"]

    microminerals = mn.microminerals

    if energy.covered > (energy.required * threshold):
        warnings.append(
            "The ration provides more energy than the horse needs, which can lead to unhealthy weight gain over time. Consider reducing concentrate, lowering the forage amount, or switching to a forage with lower energy content."
        )

    if protein.from_hay >= (protein.required * PROTEIN_SURPLUS_MAX):
        warnings.append(
            "The forage alone provides well above the horse's protein requirement. A surplus from forage is usually harmless, but this level is high. Consider a forage with lower protein content if the horse gains weight."
        )

    elif protein.from_hay < protein.required and protein.covered > protein.required:
        warnings.append(
            "The concentrate adds more protein than the horse needs, which can contribute to weight gain. The excess is also excreted as nitrogen, adding to environmental leaching. Consider lowering or removing the concentrate."
        )
    elif protein.covered > (protein.required * PROTEIN_SURPLUS_MAX):
        warnings.append(
            "The total protein is well above the horse's requirement, with the concentrate pushing it over. Consider reducing or removing the concentrate to bring the protein down."
        )

    for nutrient in microminerals:
        mineral = nutrient_coverage[nutrient + "_mg_per_kg_dm"]
        if mineral.covered < mineral.required:
            warnings.append(
                f"The ration does not meet the requirement for {nutrient.split('_')[0].capitalize()}. Supplement with a complete mineral feed to cover this. Note that a mineral feed also contributes other nutrients, so review the full ration once you have chosen one."
            )

    return warnings


def optimize_ration(
    ctx,
    profile: models.HorseProfile,
    hay: models.HayAnalysis,
    epdm: models.EnergyProteinReq,
    mn: models.MicroNutrients,
) -> models.RationResult:

    df = ctx.concentrates
    lp_prob = LpProblem("Horse_Ration", LpMinimize)

    if profile.no_grain:
        df = df[df["no_grain"] == True]

    nutrient_data = df.set_index("name").to_dict(orient="index")
    feed_items = list(nutrient_data.keys())
    feed_vars = LpVariable.dicts("Feed", feed_items, lowBound=0, cat="Continuous")
    hay_kg = round_to_nearest(epdm.dry_matter / (hay.dry_matter_pct / 100), 0.5)
    max_per_meal = ((profile.ideal_weight / 100) * 0.4) * profile.meals

    deficits, base_contribution = hay_contribution(hay, epdm, mn)

    hay_calcium = base_contribution["calcium_g_per_kg_dm"]
    hay_phosphorus = base_contribution["phosphorus_g_per_kg_dm"]
    hay_protein = base_contribution["digestible_protein_g_per_kg_dm"]
    hay_energy = base_contribution["energy_mj_per_kg_dm"]

    for nutrient in deficits:
        lp_prob += (
            lpSum([nutrient_data[f][nutrient] * feed_vars[f] for f in feed_items])
            >= deficits[nutrient],
            f"{nutrient.split('_')[0].capitalize()}Minimum",
        )

    lp_prob += (
        lpSum(
            [
                feed_vars[f] / (nutrient_data[f]["dry_matter_pct"] / 100)
                for f in feed_items
            ]
        )
        <= max_per_meal,
        "AmountMaximum",
    )

    total_calcium = hay_calcium + lpSum(
        [nutrient_data[f]["calcium_g_per_kg_dm"] * feed_vars[f] for f in feed_items]
    )
    total_phosphorus = hay_phosphorus + lpSum(
        [nutrient_data[f]["phosphorus_g_per_kg_dm"] * feed_vars[f] for f in feed_items]
    )

    lp_prob += total_calcium - 1.5 * total_phosphorus >= 0, "CalciumPhosphorusRatio"

    total_protein = hay_protein + lpSum([nutrient_data[f]["digestible_protein_g_per_kg_dm"] * feed_vars[f] for f in feed_items])
    lp_prob += total_protein <= (epdm.total_dcp_g * 1.6), "ProteinMaximum"

    total_energy = hay_energy + lpSum([nutrient_data[f]["energy_mj_per_kg_dm"] * feed_vars[f] for f in feed_items])
    lp_prob += total_energy <= (epdm.total_mj * ENERGY_MAX[profile.keeper_type]), "EnergyMaximum"

    feed_used = LpVariable.dicts("Used", feed_items, cat="Binary")

    for f in feed_items:
        lp_prob += (
            feed_vars[f]
            <= (
                (
                    nutrient_data[f]["max_g_per_100kg_bw_per_meal"]
                    * (nutrient_data[f]["dry_matter_pct"] / 100)
                )
                * (profile.ideal_weight / 100) * profile.meals
            )
            * feed_used[f],
            f"{f}Maximum",
        )

    max_amounts = {
        f: (
            nutrient_data[f]["max_g_per_100kg_bw_per_meal"]
            * (nutrient_data[f]["dry_matter_pct"] / 100)
            * (profile.ideal_weight / 100)
            * profile.meals
        )
        for f in feed_items
    }

    lp_prob += (
        lpSum([feed_used[f] for f in feed_items])
        + lpSum(
            [feed_vars[f] / max_amounts[f] for f in feed_items if max_amounts[f] > 0]
        )
        * 0.001
    )

    lp_prob.solve(PULP_CBC_CMD(msg=0))

    if LpStatus[lp_prob.status] != "Optimal":
        return models.RationResult(
            hay_kg=hay_kg,
            warnings=[
                "A complete ration could not be calculated for this horse with the available feeds. This usually happens when the horse's energy or nutrient requirements are very high. Please consult a veterinarian or equine nutritionist for an individually tailored ration."
            ],
        )
    concentrates = []
    concentrate_contribution = {}
    for f in feed_items:
        raw_amount = feed_vars[f].varValue / (nutrient_data[f]["dry_matter_pct"] / 100)
        amount = round_to_nearest(raw_amount, 0.05)
        if amount == 0 and raw_amount > 0.001:
            amount = 0.05

        if amount > 0:
            concentrate_contribution[f] = contribution_calculator(
                nutrient_data[f], feed_vars[f].varValue
            )
            concentrates.append(
                models.FeedAmount(
                    feed=f, amount_kg=amount, contribution=concentrate_contribution[f]
                )
            )
    nutrient_coverage = ration_coverage(
        epdm, mn, base_contribution, concentrate_contribution
    )

    warnings = generate_warnings(profile, nutrient_coverage, mn, concentrates)

    ration = models.RationResult(
        hay_kg=hay_kg,
        hay_coverage=base_contribution,
        concentrates=concentrates,
        nutrient_coverage=nutrient_coverage,
        warnings=warnings,
    )
    return ration
