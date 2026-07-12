from dataclasses import asdict

from pulp import *

import models

# Energy surplus warning thresholds (fraction of requirement).
# Easy and hard keeper values follow the levels used by Krafft/PC-Horse.
# The normal keeper value is interpolated between them and is not yet
# independently verified.
ENERGY_WARNING_SURPLUS = {
    "easy_keeper": 1.10,
    "normal_keeper": 1.15,  # interpolated - verify against a source
    "hard_keeper": 1.20,
}


# SLU's feed tool flags protein above 160% of requirement; a surplus
# from forage up to this level is acceptable, but concentrate-driven
# surplus should be reduced regardless.
PROTEIN_SURPLUS_MAX = 1.6

# Practical upper limit for voluntary dry matter intake, ~2.5% of bodyweight.
# Common equine nutrition guideline - not yet verified against a specific source.
MAX_HAY_DM_PCT = 2.5

# Absolute minimum hay intake (SLU: never reduce hay below this
# even to correct energy/protein surplus). The keeper-type-based
# recommended level in energy_protein_dry_matter.json is a target,
# not a hard floor.
MIN_HAY_DM_PCT = 1.0

ENERGY_MAX = {
    "easy_keeper": 1.20,  # 10 pts above the 1.10 warning threshold
    "normal_keeper": 1.25,  # 10 pts above the 1.15 warning threshold
    "hard_keeper": 1.30,  # 10 pts above the 1.20 warning threshold
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


def optimized_nutrient_needs(
    epdm: models.EnergyProteinReq, mn: models.MicroNutrients
) -> dict[str, float]:
    horse_needs = {
        "energy_mj_per_kg_dm": epdm.total_mj,
        "digestible_protein_g_per_kg_dm": epdm.total_dcp_g,
    }

    for nutrient in mn.macrominerals:
        horse_needs[nutrient.lower() + "_g_per_kg_dm"] = mn.macrominerals[nutrient]

    return horse_needs


def ration_coverage(
    epdm: models.EnergyProteinReq,
    mn: models.MicroNutrients,
    hay_nutrients: dict[str, float],
    concentrate_contribution: dict[str, float],
    horse_needs: dict[str, float],
) -> dict[str, models.NutrientCoverage]:

    total_coverage = dict(hay_nutrients)
    horse_needs = dict(horse_needs)

    nutrient_needs_coverage = {}

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
    concentrates: list[str],
    total_dm: float,
    recomended_dm: float
) -> list[str]:

    warnings = []

    if concentrates:
        warnings.append(
            f"This ration assumes concentrate is split across {profile.meals} meal(s) per day. "
            "Giving it all at once increases the risk of colic or hindgut disturbances."
        )

    protein = nutrient_coverage["digestible_protein_g_per_kg_dm"]

    keeper_type = profile.keeper_type
    threshold = ENERGY_WARNING_SURPLUS[keeper_type]
    energy = nutrient_coverage["energy_mj_per_kg_dm"]

    microminerals = mn.microminerals

    if total_dm < recomended_dm * 0.9: 
        warnings.append(
            "The recommended dry matter intake for this horse's keeper type has not been fully met by hay alone, in order to avoid excess energy or protein. Consider adding a low-energy fibre source (e.g. straw) to increase chewing time and support digestive health without adding extra nutrients."
        )

    if energy.covered > (energy.required * threshold):
        warnings.append(
            "The ration provides more energy than the horse needs, which can lead to unhealthy weight gain over time. Consider reducing concentrate, increasing training intensity, or switching to a forage with lower energy content."
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
        mineral = nutrient_coverage[nutrient.lower() + "_mg_per_kg_dm"]
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

    max_per_meal = ((profile.ideal_weight / 100) * 0.4) * profile.meals

    optimized_horse_needs = optimized_nutrient_needs(epdm, mn)

    hay_max = (profile.ideal_weight / 100) * MAX_HAY_DM_PCT
    hay_min = (profile.ideal_weight / 100) * MIN_HAY_DM_PCT
    recomended_hay_min = epdm.dry_matter
    hay_var = LpVariable("Hay", lowBound=hay_min, upBound=hay_max, cat="Continuous")

    for nutrient in optimized_horse_needs:
        lp_prob += (
            (hay_var * getattr(hay, nutrient))
            + lpSum([nutrient_data[f][nutrient] * feed_vars[f] for f in feed_items])
            >= optimized_horse_needs[nutrient],
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

    total_calcium = (hay.calcium_g_per_kg_dm * hay_var) + lpSum(
        [nutrient_data[f]["calcium_g_per_kg_dm"] * feed_vars[f] for f in feed_items]
    )
    total_phosphorus = (hay.phosphorus_g_per_kg_dm * hay_var) + lpSum(
        [nutrient_data[f]["phosphorus_g_per_kg_dm"] * feed_vars[f] for f in feed_items]
    )

    lp_prob += total_calcium - 1.5 * total_phosphorus >= 0, "CalciumPhosphorusRatio"

    total_protein = (hay.digestible_protein_g_per_kg_dm * hay_var) + lpSum(
        [
            nutrient_data[f]["digestible_protein_g_per_kg_dm"] * feed_vars[f]
            for f in feed_items
        ]
    )
    lp_prob += total_protein <= (epdm.total_dcp_g * PROTEIN_SURPLUS_MAX), "ProteinMaximum"

    total_energy = (hay.energy_mj_per_kg_dm * hay_var) + lpSum(
        [nutrient_data[f]["energy_mj_per_kg_dm"] * feed_vars[f] for f in feed_items]
    )
    lp_prob += (
        total_energy <= (epdm.total_mj * ENERGY_MAX[profile.keeper_type]),
        "EnergyMaximum",
    )


    total_starch = lpSum(
        [nutrient_data[f]["starch_g_per_kg_dm"] * feed_vars[f] for f in feed_items])

    starch_per_meal = total_starch / profile.meals
    # SLU: max 500g of starch per 100 kg bodyweight per day 
    lp_prob += (total_starch <= 500 * (profile.ideal_weight / 100)), "TotalStarchMaximum"
    #SLU: max 150 g of starch per 100 kg bodyweight per meal
    lp_prob += (starch_per_meal <= 150 * (profile.ideal_weight / 100)), "StarchPerMeal"
    
    oil_feeds = [f for f in feed_items if nutrient_data[f]["category"] == "oil"]
    total_oil = lpSum(feed_vars[f] for f in oil_feeds)
    # SLU: max 75 g oil per 100 kg bodyweight per day, regardless of oil source.
    lp_prob += (total_oil <= 0.075 * (profile.ideal_weight / 100)), "DailyOilMaximum"
    
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
                * profile.meals
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
    protein_surplus = (
        total_protein - optimized_horse_needs["digestible_protein_g_per_kg_dm"]
    )
    energy_surplus = total_energy - optimized_horse_needs["energy_mj_per_kg_dm"]

    energy_from_concentrate = total_energy - (hay.energy_mj_per_kg_dm * hay_var)

    # recomended_hay_min is the keeper-type-based target dry matter intake
    # (from epdm.dry_matter), distinct from the absolute MIN_HAY_DM_PCT floor
    # above. dm_below_recomended is a soft penalty for falling short of that
    # target. It lets the optimiser go below the recommendation (down to the
    # hard floor) when reaching it would otherwise force excess energy/protein.
    dm_below_recomended = LpVariable("HaySurplus", lowBound=0)
    lp_prob += (dm_below_recomended >= (recomended_hay_min - hay_var)), "HayBelowRecomended" 

    lp_prob += (
        lpSum([feed_used[f] for f in feed_items])
        + lpSum(
            [feed_vars[f] / max_amounts[f] for f in feed_items if max_amounts[f] > 0]
        )
        * 0.001
        + protein_surplus * 0.1
        + energy_surplus * 0.1
        + energy_from_concentrate * 0.5
        + dm_below_recomended * 0.3
    )

    lp_prob.solve(PULP_CBC_CMD(msg=0))

    if LpStatus[lp_prob.status] != "Optimal":
        fallback_hay_nutrients = contribution_calculator(asdict(hay), hay_min)
        fallback_hay_kg = round_to_nearest(hay_min / (hay.dry_matter_pct / 100), 0.5)

        hay_energy_min = hay.energy_mj_per_kg_dm * hay_min
        hay_protein_min = hay.digestible_protein_g_per_kg_dm * hay_min

        if hay_energy_min > epdm.total_mj * ENERGY_MAX[profile.keeper_type]:
            diagnosis = "The minimum recommended hay amount alone exceeds the safe energy limit for this horse. This forage may be too energy-dense for this horse's profile — consider a lower-energy hay or grass hay instead."
        elif hay_protein_min > epdm.total_dcp_g * PROTEIN_SURPLUS_MAX:
            diagnosis = "The minimum recommended hay amount alone exceeds the safe protein limit for this horse. This forage may be too protein-rich for this horse's profile — consider a lower-protein hay."
        else:
            diagnosis = "This usually happens when the horse's requirements are very high relative to the available feeds."

        warnings = [
            f"A complete ration could not be calculated. {diagnosis} Please consult a veterinarian or equine nutritionist for an individually tailored ration."
        ]

        return models.RationResult(
            hay_kg=fallback_hay_kg,
            hay_coverage=fallback_hay_nutrients,
            warnings=warnings,
        )
    
    hay_contribution = contribution_calculator(asdict(hay), hay_var.varValue)
    raw_hay_kg = hay_var.varValue / (hay.dry_matter_pct / 100)
    hay_kg = round_to_nearest(raw_hay_kg, 0.5)

    concentrates = []
    concentrate_contribution = {}
    for f in feed_items:
        raw_amount = feed_vars[f].varValue / (nutrient_data[f]["dry_matter_pct"] / 100)
        step = 0.005 if raw_amount < 0.1 else 0.05
        amount = round_to_nearest(raw_amount, step)
        if amount == 0 and raw_amount > 0.0001:
            amount = step

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
        epdm,
        mn,
        hay_contribution,
        concentrate_contribution,
        horse_needs=optimized_horse_needs,
    )
    total_dm = hay_kg * (hay.dry_matter_pct / 100)

    warnings = generate_warnings(profile, nutrient_coverage, mn, concentrates, total_dm, recomended_hay_min)

    ration = models.RationResult(
        hay_kg=hay_kg,
        hay_coverage=hay_contribution,
        concentrates=concentrates,
        nutrient_coverage=nutrient_coverage,
        warnings=warnings,
    )
    return ration
