import models


def energy_maintenance(ctx, ideal_weight, keeper_type, is_stallion):
    data = ctx.energy_protein
    calc_ideal = ideal_weight ** 0.75

    calc_maintenance = round(data["energy_maintenance"]["keeper_type"][keeper_type] * calc_ideal)
    maintenance = round(calc_maintenance)

    if is_stallion:
        maintenance = round(calc_maintenance * 1.1)

    return maintenance

def calc_energy_protein_dm(ctx, profile):
    ideal_weight = profile.ideal_weight
    is_stallion = profile.is_stallion
    workload = profile.workload_percent
    keeper_type = profile.keeper_type
    
    data = ctx.energy_protein
    
    weight_factor_dm = ideal_weight / 100

    calc_dry_matter = data["dry_matter"]["keeper_type"][keeper_type] * weight_factor_dm
    dry_matter = round(calc_dry_matter)

    maintenance = energy_maintenance(ctx, ideal_weight, keeper_type, is_stallion)

    additional_energy = int(maintenance * (workload / 100))
    total_energy_need = maintenance + additional_energy
    protein_need = total_energy_need * data["protein"]["grams"]

    return models.EnergyProteinReq(maintenance_mj=maintenance,
                            additional_mj=additional_energy,
                            total_mj=total_energy_need,
                            total_dcp_g=protein_need,
                            dry_matter=dry_matter) 

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
    macro_units = macro_df["unit"].to_dict()
    macro_minerals = (macro_df[macro_col]* weight_factor).to_dict()
    micro_minerals = (micro_df[micro_col]* weight_factor).to_dict()
    micro_units = micro_df["unit"].to_dict()

    return models.MicroNutrients(vitamins=vitamins,
                                micro_mineral_units=micro_units,
                                microminerals=micro_minerals,
                                macro_mineral_units=macro_units,
                                macrominerals=macro_minerals)
