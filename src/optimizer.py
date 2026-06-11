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
	warnings = ["Selenium is consistently deficient in Swedish hay and forage. Always supplement with a complete mineral feed or selenium-specific supplement."]
	base_deficits = {}
	surpluses = {}

	base_contribution = {
		"energy_mj_per_kg_dm": hay.energy_mj_per_kg_dm * horse_req.dry_matter,
		"digestible_protein_g_per_kg_dm": hay.digestible_protein_per_kg_dm * horse_req.dry_matter,
		"calcium_g_per_kg_dm": hay.calcium_g_per_kg_dm * horse_req.dry_matter,
		"phosphorus_g_per_kg_dm": hay.phosphorus_g_per_kg_dm * horse_req.dry_matter,
		"magnesium_g_per_kg_dm": hay.magnesium_g_per_kg_dm * horse_req.dry_matter,
		#Convert natrium from hay to salt.
		"salt_g_per_kg_dm": (hay.sodium_g_per_kg_dm / 0.4) * horse_req.dry_matter,
	}

	micro_contributions = {
		"copper_mg_per_kg_dm": hay.copper_mg_per_kg_dm * horse_req.dry_matter,
		"zinc_mg_per_kg_dm": hay.zinc_mg_per_kg_dm * horse_req.dry_matter,
		"manganese_mg_per_kg_dm": hay.manganese_mg_per_kg_dm * horse_req.dry_matter,
		"iron_mg_per_kg_dm": hay.iron_mg_per_kg_dm * horse_req.dry_matter,
	}

	for nutrient, balance in [
		("energy_mj_per_kg_dm", base_contribution["energy_mj_per_kg_dm"] - horse_req.total_mj),
		("digestible_protein_g_per_kg_dm", base_contribution["digestible_protein_g_per_kg_dm"] - horse_req.total_dcp_g),
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
