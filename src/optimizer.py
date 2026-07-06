from dataclasses import asdict

from pulp import *

import models


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
    profile: models.HorseProfile,
) -> tuple[list, models.NutrientCoverage]:
    pass


def optimize_ration(
    ctx,
    profile: models.HorseProfile,
    hay: models.HayAnalysis,
    epdm: models.EnergyProteinReq,
    mn: models.MicroNutrients,
) -> models.RationResult | str:

    df = ctx.concentrates
    lp_prob = LpProblem("Horse_Ration", LpMinimize)

    if profile.no_grain:
        df = df[df["no_grain"] == True]

    nutrient_data = df.set_index("name").to_dict(orient="index")
    feed_items = list(nutrient_data.keys())
    feed_vars = LpVariable.dicts("Feed", feed_items, lowBound=0, cat="Continuous")
    hay_kg = round_to_nearest(epdm.dry_matter / (hay.dry_matter_pct / 100), 0.5)
    max_per_meal = (profile.ideal_weight / 100) * 0.4

    deficits, base_contribution = hay_contribution(hay, epdm, mn)

    hay_calcium = base_contribution["calcium_g_per_kg_dm"]
    hay_phosphorus = base_contribution["phosphorus_g_per_kg_dm"]

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

    feed_used = LpVariable.dicts("Used", feed_items, cat="Binary")

    for f in feed_items:
        lp_prob += (
            feed_vars[f]
            <= (
                (
                    nutrient_data[f]["max_g_per_100kg_bw_per_meal"]
                    * (nutrient_data[f]["dry_matter_pct"] / 100)
                )
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
        amount = round_to_nearest(feed_vars[f].varValue / (nutrient_data[f]["dry_matter_pct"] / 100), 0.05)
        if amount > 0.001:
            concentrate_contribution[f] = contribution_calculator(nutrient_data[f], feed_vars[f].varValue)
            concentrates.append(
                models.FeedAmount(
                    feed=f, amount_kg=amount, contribution=concentrate_contribution[f]
                )
            )

    #ration = models.RationResult(
    #    hay_kg=hay_kg, hay_coverage=base_contribution, concentrates=concentrates, )
    return hay_kg, concentrates
