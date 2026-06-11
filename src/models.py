from dataclasses import dataclass

import pandas as pd


@dataclass
class DataContext:
    energy_protein: dict
    macro: pd.DataFrame
    micro: pd.DataFrame
    vitamins: pd.DataFrame
    concentrates: pd.DataFrame


@dataclass
class HorseProfile:
    current_weight: int
    ideal_weight: int
    keeper_type: str
    is_stallion: bool
    workload_percent: int
    no_grain: bool


@dataclass
class EnergyProteinReq:
    maintenance_mj: int
    additional_mj: int
    total_mj: int
    total_dcp_g: int
    dry_matter: int


@dataclass
class MicroNutrients:
    vitamins: dict[str, float]
    micro_mineral_units: dict[str]
    microminerals: dict[str, float]
    macro_mineral_units: dict[str]
    macrominerals: dict[str, float]


@dataclass
class HayAnalysis:
    dry_matter_pct: int
    energy_mj_per_kg_dm: float
    digestible_protein_per_kg_dm: int
    calcium_g_per_kg_dm: float
    phosphorus_g_per_kg_dm: float
    magnesium_g_per_kg_dm: float
    copper_mg_per_kg_dm: float
    zinc_mg_per_kg_dm: float
    manganese_mg_per_kg_dm: float
    iron_mg_per_kg_dm: float
    sodium_g_per_kg_dm: float


@dataclass
class ConcentrateItem:
    name: str
    category: str
    no_grain: bool
    energy_mj_per_kg_dm: float
    digestible_protein_g_per_kg_dm: float
    calcium_g_per_kg_dm: float
    phosphorus_g_per_kg_dm: float
    magnesium_g_per_kg_dm: float
    sodium_g_per_kg_dm: float
    copper_mg_per_kg_dm: float
    zinc_mg_per_kg_dm: float
    manganese_mg_per_kg_dm: float
    iron_mg_per_kg_dm: float
    selenium_mg_per_kg_dm: float
    starch_g_per_kg_dm: float
    max_g_per_100kg_bw_per_meal: float
    notes: str


@dataclass
class FeedAmount:
    feed: ConcentrateItem
    amount_kg: float


@dataclass
class RationResult:
    hay_kg: float
    concentrates: list[FeedAmount]
    total_energy_mj: float
    total_protein_g: float
    total_dm_kg: float
    mineral_shortfalls: list[str]
    warnings: list[str]
