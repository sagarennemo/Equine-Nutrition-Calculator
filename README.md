# 🐴 Equine Nutrition Calculator (EquiNutr)

A Python-based equine nutrition calculator that estimates daily energy and nutrient requirements based on weight and workload, and uses linear programming to optimise a complete feed ration from hay and concentrates. This tool helps horse owners, stable managers, and equine nutritionists determine scientifically-based nutritional needs for horses, with plans to support hay analysis via OCR and a web interface in future versions.

## Features

- **Personalized Nutrition Calculations**: Calculate daily requirements based on:
  - Current and ideal body weight
  - Keeper type (easy, normal, or hard keeper)
  - Gender (stallions have increased requirements)
  - Workload level (maintenance to very hard work)
  - Grain sensitivity and number of concentrate meals per day

- **Advanced Workload Calculator**: Option to calculate custom energy requirements based on specific exercise routines (minutes of walking, trotting, cantering per week)

- **Ration Optimisation**: Uses linear programming (PuLP) to select the smallest practical combination of hay and concentrate feeds that meets the horse's requirements, subject to:
  - Minimum and maximum dry matter intake from hay
  - A calcium-to-phosphorus ratio within a safe range
  - Per-feed and per-meal intake limits
  - Upper bounds on energy and protein to avoid excessive surplus

- **Comprehensive Nutrient Analysis**: Estimates requirements and ration coverage for:
  - Metabolizable Energy (MJ/day)
  - Digestible Crude Protein (DCP)
  - Dry Mass Intake
  - Macrominerals (calcium, phosphorus, magnesium, salt)
  - Microminerals (copper, zinc, manganese, iron, selenium)


- **Source-Grounded Warnings**: Flags energy and protein surplus, and micromineral deficits that concentrates can't reliably solve, with thresholds based on SLU's own feed evaluation tool and industry practice where available

- **Interactive CLI**: User-friendly command-line interface with questionnaires and formatted output tables showing required vs. covered nutrients per feed
  

## Requirements

- Python 3.10+
- pandas
- questionary
- rich
- pulp==3.3.2

## Installation

1. Clone the repository:

```bash
git clone https://github.com/sagarennemo/Equine-Nutrition-Calculator.git
cd Equine-Nutrition-Calculator
```

2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the calculator from the `src` directory:

```bash
cd src
python main.py
```

The program will guide you through a series of questions covering the horse's weight, keeper type, gender, grain sensitivity, number of concentrate meals per day, and workload level, then compute a complete ration.

### Example Output

```
      Ration Result  |  Hay: 12 kg  |  Wheat Bran: 0.5 kg  |  Calcium Carbonate: 0.05 kg  |  Salt: 0.05 kg
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━┓
┃ Nutrient                   ┃ Required ┃ Covered ┃ From Hay ┃ Wheat Bran ┃ Calcium Carbonate ┃ Salt ┃ Coverage % ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━┩
│ Energy (MJ/day)            │       70 │    77.8 │     73.6 │        4.2 │                 0 │    0 │      111.2 │
│ Digestible Protein (g/day) │      420 │     532 │      480 │         52 │                 0 │    0 │      126.7 │
│ Calcium (g/day)            │       30 │      30 │     16.8 │        0.7 │              12.5 │    0 │        100 │
│ Phosphorus (g/day)         │       18 │      18 │     12.8 │        5.2 │                 0 │    0 │        100 │
│ Magnesium (g/day)          │      9.5 │    10.3 │        8 │        2.3 │                 0 │    0 │      108.4 │
│ Salt (g/day)               │       35 │      35 │        4 │        0.3 │                 0 │ 30.7 │        100 │
│ Iron (mg/day)              │      450 │   692.9 │    649.6 │       43.3 │                 0 │    0 │        154 │
│ Manganese (mg/day)         │      450 │   917.6 │    865.6 │         52 │                 0 │    0 │      203.9 │
│ Copper (mg/day)            │      110 │    38.1 │       32 │        6.1 │                 0 │    0 │       34.6 │
│ Zinc (mg/day)              │      450 │   224.9 │    181.6 │       43.3 │                 0 │    0 │         50 │
│ Selenium (mg/day)          │        1 │       0 │        0 │          0 │                 0 │    0 │        4.3 │
└────────────────────────────┴──────────┴─────────┴──────────┴────────────┴───────────────────┴──────┴────────────┘

Warnings:
  This ration assumes concentrate is split across 2 meal(s) per day. Giving it all at once increases the risk of colic or hindgut
disturbances.
  The ration does not meet the requirement for Copper. Supplement with a complete mineral feed to cover this. Note that a mineral feed
also contributes other nutrients, so review the full ration once you have chosen one.
  The ration does not meet the requirement for Zinc. Supplement with a complete mineral feed to cover this. Note that a mineral feed also
contributes other nutrients, so review the full ration once you have chosen one.
  The ration does not meet the requirement for Selenium. Supplement with a complete mineral feed to cover this. Note that a mineral feed
also contributes other nutrients, so review the full ration once you have chosen one.
```

If a ration cannot be calculated for a horse's profile with the available feeds, the program reports the minimum recommended hay amount and explains why a complete ration wasn't possible, recommending professional consultation.

## Project Structure

```
Equine-Nutrition-Calculator/
├── dataset/
│   ├── energy_protein_dry_matter.json  # Energy and protein requirement data
│   ├── macrominerals.csv               # Macromineral requirements
│   ├── microminerals.csv               # Micromineral requirements
│   ├── vitamins.csv                    # Vitamin requirements
│   └── concentrates.csv                # Concentrate feed nutrient database
├── src/
│   ├── main.py                         # Main application and CLI interface
│   ├── requirement_calculations.py     # Nutrient requirement calculations
│   ├── optimizer.py                    # Linear programming ration optimiser
│   ├── models.py                       # Data models and structures
│   └── file_reader.py                  # Data loading utilities
├── tests/
│   ├── test_file_reader.py             # integration test for load_context()
│   ├── test_requirement_calculations.py # Unit tests for nutrient requirements
│   ├── test_optimizer.py               # Unit and integration tests for the ration optimiser
├── requirements.txt                    # Project dependencies
└── conftest.py                         # Shared pytest fixture and test helpers
```

## Calculation Methodology
└──
- **Maintenance Energy**: Calculated using metabolic body weight (BW^0.75) with adjustments for keeper type
- **Workload Energy**: Additional energy requirements based on percentage increases or custom exercise calculations
- **Protein Requirements**: Calculated proportionally to total energy needs
- **Minerals & Vitamins**: Scaled based on body weight and workload intensity
- **Ration Optimisation**: A linear program (PuLP) treats hay quantity and each concentrate's quantity as variables, with binary variables indicating whether a feed is used. The objective minimises the number of feeds used, the amount fed, and energy/protein surplus, subject to hard constraints on minimum nutrient coverage, the calcium-to-phosphorus ratio, and maximum practical intake per meal.

## Testing
The project includes unit and integration tests covering requirement 
calculations, dataset loading, and the ration optimiser.

## Workload Levels

| Level          | Energy Increase | Typical Activities                   |
| -------------- | --------------- | ------------------------------------ |
| Maintenance    | 0%              | Pasture, no work                     |
| Light Work     | 25%             | Regular riding                       |
| Moderate Work  | 50%             | School horses, low level competition |
| Hard Work      | 75%             | Intensive training and competition   |
| Very Hard Work | 120%            | Elite level competition, race horses |

## Roadmap

Future enhancements planned:

- Hay analysis via OCR (photo/PDF upload)
- Web interface (Vue + FastAPI)
- Life stage support (pregnancy, lactation, growth)
- User-entered mineral feeds for full micromineral coverage
- Export results to PDF/CSV

## Data Sources

Nutritional requirements and concentrate feed values are based on **"Utfodringsrekommendationer för häst"** (Feeding Recommendations for Horses) and SLU's official feed composition tables, published by the Swedish University of Agricultural Sciences (SLU - Sveriges lantbruksuniversitet). The reference data is stored in the `dataset/` directory and follows established equine nutrition research standards.

Some warning thresholds (energy surplus for normal keepers, maximum voluntary hay intake) are interpolated from related sources and not yet independently verified — these are marked in the code and will be reviewed with an equine nutritionist before any production use.

### References

Jansson, A. (2013), Utfodringsrekommendationer för häst, Sveriges lantbruksuniversitet, accessed 5 Feb 2026, https://pub.epsilon.slu.se/37156/1/jansson-a-20250516.pdf

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).

## Author

**sagarennemo**

- GitHub: [@sagarennemo](https://github.com/sagarennemo)

## Disclaimer

This calculator is designed as an educational tool and starting point for equine nutrition planning. It calculates ration recommendations from standardised requirement formulas; it does not replace individual assessment by a qualified equine nutritionist or veterinarian, especially for horses with special needs, medical conditions, or performance requirements.

The nutritional data is based on Swedish research and standards, which may differ from recommendations in other countries or regions.

---

_Developed with 🐴 for better equine nutrition_
