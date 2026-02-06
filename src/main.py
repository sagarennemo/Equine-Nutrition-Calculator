from pathlib import Path
from file_reader import *

# To avoid file path issues on different devices
BASE_DIR = Path(__file__).parent.parent
VITAMINS_FILE_PATH = BASE_DIR / "dataset" / "vitamins.csv"
MACRO_FILE_PATH = BASE_DIR / "dataset" / "macrominerals.csv"
MICRO_FILE_PATH = BASE_DIR / "dataset" / "microminerals.csv"
ENERGY_PROTEIN_FILE_PATH = BASE_DIR / "dataset" / "energy_protein.json"

