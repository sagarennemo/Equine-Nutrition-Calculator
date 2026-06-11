import math

from pulp import *

import models


def round_to_half(value: float) -> float:
    rounded = round(value * 2) / 2
    if int(rounded) == rounded:
        rounded = int(rounded)
    return rounded


def hay_contribution(
    hay: models.HayAnalysis,
    horse_req: models.EnergyProteinReq,
    micronutr: models.MicroNutrients,
) -> dict:
    warnings = [
        "Selenium is consistently deficient in Swedish hay and forage. Always supplement with a complete mineral feed or selenium-specific supplement."
    ]
    base_deficits = {}
    surpluses = {}

    base_contribution = {
        "energy_mj_per_kg_dm": hay.energy_mj_per_kg_dm * horse_req.dry_matter,
        "digestible_protein_g_per_kg_dm": hay.digestible_protein_per_kg_dm
        * horse_req.dry_matter,
        "calcium_g_per_kg_dm": hay.calcium_g_per_kg_dm * horse_req.dry_matter,
        "phosphorus_g_per_kg_dm": hay.phosphorus_g_per_kg_dm * horse_req.dry_matter,
        "magnesium_g_per_kg_dm": hay.magnesium_g_per_kg_dm * horse_req.dry_matter,
        # Convert natrium from hay to salt.
        "salt_g_per_kg_dm": (hay.sodium_g_per_kg_dm / 0.4) * horse_req.dry_matter,
    }

    micro_contributions = {
        "copper_mg_per_kg_dm": hay.copper_mg_per_kg_dm * horse_req.dry_matter,
        "zinc_mg_per_kg_dm": hay.zinc_mg_per_kg_dm * horse_req.dry_matter,
        "manganese_mg_per_kg_dm": hay.manganese_mg_per_kg_dm * horse_req.dry_matter,
        "iron_mg_per_kg_dm": hay.iron_mg_per_kg_dm * horse_req.dry_matter,
    }

    for nutrient, balance in [
        (
            "energy_mj_per_kg_dm",
            base_contribution["energy_mj_per_kg_dm"] - horse_req.total_mj,
        ),
        (
            "digestible_protein_g_per_kg_dm",
            base_contribution["digestible_protein_g_per_kg_dm"] - horse_req.total_dcp_g,
        ),
    ]:
        base_deficits[nutrient] = max(0, -balance)

        if balance >= 0:
            surpluses[nutrient] = balance

    for nutrient in micronutr.macrominerals:
        mineral_balance = (
            base_contribution[nutrient.lower() + "_g_per_kg_dm"]
            - micronutr.macrominerals[nutrient]
        )
        base_deficits[nutrient.lower() + "_g_per_kg_dm"] = max(0, -mineral_balance)

        if mineral_balance >= 0:
            surpluses[nutrient.lower() + "_g_per_kg_dm"] = mineral_balance

    for nutrient in micronutr.microminerals:
        if nutrient == "selenium":
            continue

        if (
            micro_contributions[nutrient.lower() + "_mg_per_kg_dm"]
            < micronutr.microminerals[nutrient]
        ):
            deficit = (
                micro_contributions[nutrient.lower() + "_mg_per_kg_dm"]
                - micronutr.microminerals[nutrient]
            )
            warnings.append(
                f"{nutrient.capitalize()} requirement not met. Deficit of. {round_to_half(deficit)}. Supplement with a complete mineral feed."
            )
    return warnings, base_deficits, surpluses, base_contribution


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
    hay_kg = round_to_half(epdm.dry_matter / (hay.dry_matter_pct / 100))
    max_per_meal = (profile.ideal_weight / 100) * 0.4

    warnings, deficits, surpluses, base_contribution = hay_contribution(hay, epdm, mn)

    hay_calcium = base_contribution["calcium_g_per_kg_dm"]
    hay_phosphorus = base_contribution["phosphorus_g_per_kg_dm"]

    for nutrient in deficits:
        lp_prob += (
            lpSum([nutrient_data[f][nutrient] * feed_vars[f] for f in feed_items])
            >= deficits[nutrient],
            f"{nutrient.split('_')[0].capitalize()}Minimum",
        )

    lp_prob += (
        lpSum([feed_vars[f] for f in feed_items]) <= max_per_meal,
        "AmountMaximum",
    )

    total_calcium = hay_calcium + lpSum(
        [nutrient_data[f]["calcium_g_per_kg_dm"] * feed_vars[f] for f in feed_items]
    )
    total_phosphorus = hay_phosphorus + lpSum(
        [nutrient_data[f]["phosphorus_g_per_kg_dm"] * feed_vars[f] for f in feed_items]
    )

    lp_prob += total_calcium - 1.5 * total_phosphorus >= 0, "CalciumPhosphorusRatio"

    feed_used = LpVariable.dicts("Used", feed_items, cat="Binary")

    for f in feed_items:
        lp_prob += (
            feed_vars[f]
            <= (
                nutrient_data[f]["max_g_per_100kg_bw_per_meal"]
                * (profile.ideal_weight / 100)
            )
            * feed_used[f],
            f"{f}Maximum",
        )

    max_amounts = {
        f: nutrient_data[f]["max_g_per_100kg_bw_per_meal"]
        * (profile.ideal_weight / 100)
        for f in feed_items
    }
    lp_prob += (
        lpSum([feed_used[f] for f in feed_items])
        + lpSum(
            [feed_vars[f] / max_amounts[f] for f in feed_items if max_amounts[f] > 0]
        )
        * 0.001
    )

    lp_prob.solve()
    print(f"{hay_kg} kg hay per day")
    for f in feed_items:
        if feed_vars[f].varValue > 0.001:
            print(f, round(feed_vars[f].varValue, 2), "kg")
