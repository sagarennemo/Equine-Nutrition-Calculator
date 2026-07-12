import pytest
from optimizer import *
from conftest import *
from dataclasses import asdict

@pytest.mark.parametrize(
    "value, step, expected",
    [(12.1, 0.5, 12), (12.4, 0.5, 12.5), (12.5, 0.5, 12.5), (0.43, 0.05, 0.45)],
)
def test_round_to_nearest_values(value, step, expected):
    result = round_to_nearest(value, step)
    assert result == expected


@pytest.mark.parametrize(
    "value, step, expected_type", [(12.1, 0.5, int), (0.43, 0.05, float)]
)
def test_round_to_nearest_return_type(value, step, expected_type):
    result = round_to_nearest(value, step)
    assert isinstance(result, expected_type)

def test_contribution_calculator_concentrate():
    # Oats
    source = {
            "energy_mj_per_kg_dm": 11.1,
            "digestible_protein_g_per_kg_dm": 86,
            "calcium_g_per_kg_dm": 0.8,
            "phosphorus_g_per_kg_dm": 3.8,
            "magnesium_g_per_kg_dm": 1.3,
            "salt_g_per_kg_dm": 1.25,
            "copper_mg_per_kg_dm": 4,
            "zinc_mg_per_kg_dm": 35,
            "manganese_mg_per_kg_dm": 40,
            "iron_mg_per_kg_dm": 80,
            "selenium_mg_per_kg_dm": 0.1,}
    
    result = contribution_calculator(source, 2)

    assert result["energy_mj_per_kg_dm"] == 22.2
    assert result["calcium_g_per_kg_dm"] == 1.6
    assert result["copper_mg_per_kg_dm"] == 8

def test_contribution_calculator_with_hay():
    hay = make_test_hay()
    result = contribution_calculator(asdict(hay), 10.0)
    assert result["energy_mj_per_kg_dm"] == hay.energy_mj_per_kg_dm * 10.0
    assert result["calcium_g_per_kg_dm"] == hay.calcium_g_per_kg_dm * 10.0
    assert result["copper_mg_per_kg_dm"] == hay.copper_mg_per_kg_dm * 10.0

def test_optimized_nutrient_needs():
    epdm = make_test_epdm()
    mn = make_test_mn()

    result = optimized_nutrient_needs(epdm, mn)
    assert result["energy_mj_per_kg_dm"] == epdm.total_mj
    assert result["digestible_protein_g_per_kg_dm"] == epdm.total_dcp_g
    assert result["calcium_g_per_kg_dm"] == mn.macrominerals["calcium"]
    assert result["phosphorus_g_per_kg_dm"] == mn.macrominerals["phosphorus"]
    assert result["magnesium_g_per_kg_dm"] == mn.macrominerals["magnesium"]
    assert result["salt_g_per_kg_dm"] == mn.macrominerals["salt"]

 
def test_optimize_ration_meets_energy_and_protein(ctx):
    profile = make_test_profile()
    hay = make_test_hay()
    epdm = make_test_epdm()
    mn = make_test_mn()

    result = optimize_ration(ctx, profile, hay, epdm, mn)

    energy = result.nutrient_coverage["energy_mj_per_kg_dm"]
    protein = result.nutrient_coverage["digestible_protein_g_per_kg_dm"]
    assert energy.covered >= energy.required
    assert protein.covered >= protein.required

def test_optimize_ration_calcium_phosphorus_ratio(ctx):
    profile = make_test_profile()
    hay = make_test_hay()
    epdm = make_test_epdm()
    mn = make_test_mn()

    result = optimize_ration(ctx, profile, hay, epdm, mn)

    calcium = result.nutrient_coverage["calcium_g_per_kg_dm"].covered
    phosphorus = result.nutrient_coverage["phosphorus_g_per_kg_dm"].covered
    assert calcium >= 1.5 * phosphorus

def test_optimize_ration_never_goes_below_hay_floor(ctx):
    profile = make_test_profile(keeper_type="hard_keeper")
    hay = make_test_hay()
    epdm = make_test_epdm(maintenance_mj=58, total_mj=58, total_dcp_g=348, dry_matter=10.0)
    mn = make_test_mn(microminerals={'iron': 225.0, 'manganese': 225.0, 'copper': 55.0, 'zinc': 225.0, 'selenium': 1.0},
                      macrominerals={'calcium': 20.0, 'phosphorus': 14.0, 'magnesium': 7.5, 'salt': 25.5})

    result = optimize_ration(ctx, profile, hay, epdm, mn)

    min_hay_dm = (profile.ideal_weight / 100) * MIN_HAY_DM_PCT
    actual_hay_dm = result.hay_kg * (hay.dry_matter_pct / 100)
    assert actual_hay_dm >= min_hay_dm


