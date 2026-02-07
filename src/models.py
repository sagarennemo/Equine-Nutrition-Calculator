from dataclasses import dataclass
import pandas as pd

@dataclass
class DataContext:
    energy_protein: dict
    macro: pd.DataFrame
    micro: pd.DataFrame
    vitamins: pd.DataFrame

@dataclass
class HorseProfile:
    current_weight: int
    ideal_weight: int
    keeper_type: str
    is_stallion: bool
    workload_percent: int

@dataclass
class EnergyProteinReq:
    maintenance_mj: int
    additional_mj: int
    total_mj: int
    total_dcp_g: int

@dataclass
class MicroNutrients:
    vitamins: dict[str, float]
    microminerals: dict[str, float]
    macrominerals: dict[str, float]



