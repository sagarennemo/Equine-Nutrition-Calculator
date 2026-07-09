from dataclasses import dataclass, field

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
    meals: int


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
    digestible_protein_g_per_kg_dm: int
    calcium_g_per_kg_dm: float
    phosphorus_g_per_kg_dm: float
    magnesium_g_per_kg_dm: float
    copper_mg_per_kg_dm: float
    zinc_mg_per_kg_dm: float
    manganese_mg_per_kg_dm: float
    iron_mg_per_kg_dm: float
    salt_g_per_kg_dm: float
    selenium_mg_per_kg_dm: float = 0


@dataclass
class FeedAmount:
    feed: str
    amount_kg: float
    contribution: dict[str, float]


@dataclass
class NutrientCoverage:
    required: float
    covered: float
    from_hay: float


@dataclass
class RationResult:
    hay_kg: float
    hay_coverage: dict[str, float] = field(default_factory=dict)
    concentrates: list[FeedAmount] = field(default_factory=list)
    nutrient_coverage: dict[str, NutrientCoverage] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
