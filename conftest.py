import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pytest
from file_reader import load_context
import models


@pytest.fixture(scope="module")
def ctx():
    return load_context()


def make_test_profile(
    current_weight=500,
    ideal_weight=500,
    keeper_type="normal_keeper",
    is_stallion=False,
    workload_percent=0,
    no_grain=False,
    meals=2,
):
    return models.HorseProfile(
        current_weight=current_weight,
        ideal_weight=ideal_weight,
        keeper_type=keeper_type,
        is_stallion=is_stallion,
        workload_percent=workload_percent,
        no_grain=no_grain,
        meals=meals,
    )


def make_test_hay(
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
):
    return models.HayAnalysis(
        dry_matter_pct=dry_matter_pct,
        energy_mj_per_kg_dm=energy_mj_per_kg_dm,
        digestible_protein_g_per_kg_dm=digestible_protein_g_per_kg_dm,
        calcium_g_per_kg_dm=calcium_g_per_kg_dm,
        phosphorus_g_per_kg_dm=phosphorus_g_per_kg_dm,
        magnesium_g_per_kg_dm=magnesium_g_per_kg_dm,
        copper_mg_per_kg_dm=copper_mg_per_kg_dm,
        zinc_mg_per_kg_dm=zinc_mg_per_kg_dm,
        manganese_mg_per_kg_dm=manganese_mg_per_kg_dm,
        iron_mg_per_kg_dm=iron_mg_per_kg_dm,
        salt_g_per_kg_dm=salt_g_per_kg_dm,
    )


def make_test_epdm(
    maintenance_mj=56, additional_mj=0, total_mj=56, total_dcp_g=336, dry_matter=7.5
):

    return models.EnergyProteinReq(
        maintenance_mj=maintenance_mj,
        additional_mj=additional_mj,
        total_mj=total_mj,
        total_dcp_g=total_dcp_g,
        dry_matter=dry_matter,
    )


def make_test_mn(
    vitamins={
        "A": 17500.0,
        "D": 2250.0,
        "E": 375.0,
        "B1": 35.0,
        "B2": 20.0,
        "biotin": 0.5,
    },
    micro_mineral_units={
        "iron": "mg/day",
        "manganese": "mg/day",
        "copper": "mg/day",
        "zinc": "mg/day",
        "selenium": "mg/day",
    },
    microminerals={
        "iron": 225.0,
        "manganese": 225.0,
        "copper": 55.0,
        "zinc": 225.0,
        "selenium": 1.0,
    },
    macro_mineral_units={
        "calcium": "grams/day",
        "phosphorus": "grams/day",
        "magnesium": "grams/day",
        "salt": "grams/day",
    },
    macrominerals={"calcium": 20.0, "phosphorus": 14.0, "magnesium": 7.5, "salt": 25.5},
):

    return models.MicroNutrients(
        vitamins=vitamins,
        micro_mineral_units=micro_mineral_units,
        microminerals=microminerals,
        macro_mineral_units=macro_mineral_units,
        macrominerals=macrominerals,
    )
