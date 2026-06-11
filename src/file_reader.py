import json
from pathlib import Path

import pandas as pd

import models

# To avoid file path issues on different devices
BASE_DIR = Path(__file__).parent.parent
VITAMINS_FILE_PATH = BASE_DIR / "dataset" / "vitamins.csv"
MACRO_FILE_PATH = BASE_DIR / "dataset" / "macrominerals.csv"
MICRO_FILE_PATH = BASE_DIR / "dataset" / "microminerals.csv"
ENERGY_PROTEIN_FILE_PATH = BASE_DIR / "dataset" / "energy_protein_dry_matter.json"
CONCENTRATES_FILE_PATH = BASE_DIR / "dataset" / "concentrates.csv"


def csv_reader(file_path):
    reader = pd.read_csv(file_path)
    return reader


def json_reader(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data


def load_context() -> models.DataContext:
    return models.DataContext(
        energy_protein=json_reader(ENERGY_PROTEIN_FILE_PATH),
        macro=csv_reader(MACRO_FILE_PATH),
        micro=csv_reader(MICRO_FILE_PATH),
        vitamins=csv_reader(VITAMINS_FILE_PATH),
        concentrates=csv_reader(CONCENTRATES_FILE_PATH),
    )
