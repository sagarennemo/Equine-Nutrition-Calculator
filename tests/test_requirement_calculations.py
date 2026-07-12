import pytest
from requirement_calculations import *
from models import HorseProfile


def make_test_profile(
    current_weight=500,
    ideal_weight=500,
    keeper_type="normal_keeper",
    is_stallion=False,
    workload_percent=0,
    no_grain=False,
    meals=2,
):

    return HorseProfile(
        current_weight=current_weight,
        ideal_weight=ideal_weight,
        keeper_type=keeper_type,
        is_stallion=is_stallion,
        workload_percent=workload_percent,
        no_grain=no_grain,
        meals=meals,
    )


@pytest.mark.parametrize(
    "keeper_type, expected",
    [("easy_keeper", 53), ("normal_keeper", 56), ("hard_keeper", 58)],
)
def test_energy_by_keeper_type(ctx, keeper_type, expected):
    result = energy_maintenance(ctx, 500, keeper_type, False)
    assert result == expected


@pytest.mark.parametrize(
    "keeper_type, expected",
    [("easy_keeper", 58), ("normal_keeper", 61), ("hard_keeper", 64)],
)
def test_stallion_energy_addition(ctx, keeper_type, expected):
    result = energy_maintenance(ctx, 500, keeper_type, True)
    assert result == expected


def test_resting_total_energy(ctx):
    profile = make_test_profile()
    result = calc_energy_protein_dm(ctx, profile)
    assert result.maintenance_mj == result.total_mj

# workload_percent=61.8 is not realistic input (the CLI only produces
# integers), but is chosen deliberately so maintenance * (workload/100)
# lands on a value with a decimal remainder — this verifies round()
# behaves as expected rather than truncating.
def test_additional_energy(ctx):
    profile = make_test_profile(workload_percent=61.8)
    result = calc_energy_protein_dm(ctx, profile)
    assert result.additional_mj == 35


@pytest.mark.parametrize(
    "keeper_type, expected",
    [("easy_keeper", 5), ("normal_keeper", 7.5), ("hard_keeper", 10)],
)
def test_dm_recomendation(ctx, keeper_type, expected):
    profile = make_test_profile(keeper_type=keeper_type)
    result = calc_energy_protein_dm(ctx, profile)
    assert result.dry_matter == expected


def test_protein_calculetions(ctx):
    profile = make_test_profile(workload_percent=25)
    result = calc_energy_protein_dm(ctx, profile)
    assert result.total_dcp_g == result.total_mj * 6


def test_energy_protein_req(ctx):
    profile = make_test_profile()
    result = calc_energy_protein_dm(ctx, profile)
    assert result.maintenance_mj == 56
    assert result.additional_mj == 0
    assert result.total_mj == 56
    assert result.total_dcp_g == 336
    assert result.dry_matter == 7.5


@pytest.mark.parametrize(
    "workload, expected",
    [
        (0, ("maintenance", "maintenance", "maintenance")),
        (29, ("lt30", "working_horses", "maintenance")),
        (30, ("30_50", "working_horses", "maintenance")),
        (51, ("50_75", "working_horses", "maintenance")),
        (76, ("75_130", "working_horses", "very_hard_working")),
        (131, ("75_130", "working_horses", "very_hard_working")),
    ],
)
def test_workload(workload, expected):
    result = workload_to_column(workload)
    assert result == expected


def test_macro_mineral_scales_with_workload(ctx):
    profile_rest = make_test_profile()
    profile_work = make_test_profile(workload_percent=75)

    rest_result = calc_micro_nutrients(ctx, profile_rest)
    work_result = calc_micro_nutrients(ctx, profile_work)

    assert rest_result.macrominerals["calcium"] != work_result.macrominerals["calcium"]


def test_micro_mineral_scales_with_workload(ctx):
    profile_rest = make_test_profile()
    profile_work = make_test_profile(workload_percent=75)

    rest_result = calc_micro_nutrients(ctx, profile_rest)
    work_result = calc_micro_nutrients(ctx, profile_work)

    assert rest_result.microminerals["iron"] != work_result.microminerals["iron"]


def test_vitamin_scales_with_workload(ctx):
    profile_rest = make_test_profile()
    profile_work = make_test_profile(workload_percent=76)

    rest_result = calc_micro_nutrients(ctx, profile_rest)
    work_result = calc_micro_nutrients(ctx, profile_work)

    assert rest_result.vitamins["A"] != work_result.vitamins["A"]
