# 🐴 Equine Nutrition Calculator

A Python-based equine nutrition calculator that estimates daily energy and nutrient requirements based on weight and workload. This tool helps horse owners, stable managers, and equine nutritionists determine scientifically-based nutritional needs for horses, with plans to support hay analysis and ration planning in future versions.

## Features

- **Personalized Nutrition Calculations**: Calculate daily requirements based on:
  - Current and ideal body weight
  - Keeper type (easy, normal, or hard keeper)
  - Gender (stallions have increased requirements)
  - Workload level (maintenance to very hard work)

- **Advanced Workload Calculator**: Option to calculate custom energy requirements based on specific exercise routines (minutes of walking, trotting, cantering per week)
  
- **Comprehensive Nutrient Analysis**: Estimates requirements for:
  - Metabolizable Energy (MJ/day)
  - Digestible Crude Protein (DCP)
  - Dry Mass Intake
  - Macrominerals (calcium, phosphorus, magnesium, salt)
  - Microminerals (copper, zinc, manganese, selenium, iodine)
  - Vitamins

- **Interactive CLI**: User-friendly command-line interface with questionnaires and formatted output tables

## Requirements

- Python 3.10+
- pandas
- questionary
- rich

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
The program will guide you through a series of questions:

1. **Weight Information**: Enter the horse's current weight and ideal weight
2. **Keeper Type**: Select how the horse maintains weight (easy/normal/hard keeper)
3. **Gender**: Indicate if the horse is a stallion (stallions have 10% higher energy requirements)
4. **Workload Level**: Choose from predefined levels or use the advanced calculator for custom work routines

### Example Output

```
              Horse Nutrient Requirements               
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃         Nutrient         ┃ Target Intake ┃   Unit    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│        Dry Matter        │       8       │  kg/day   │
│   Metabolizable Energy   │      56       │  MJ/day   │
│ Digestible Crude Protein │      336      │ grams/day │
│         Calcium          │      20       │ grams/day │
│        Phosphorus        │      14       │ grams/day │
│        Magnesium         │       7       │ grams/day │
│           Salt           │      25       │ grams/day │
│           Iron           │      225      │  mg/day   │
│        Manganese         │      225      │  mg/day   │
│          Copper          │      55       │  mg/day   │
│           Zinc           │      225      │  mg/day   │
│          Cobalt          │       0       │  mg/day   │
│          Iodine          │       1       │  mg/day   │
│         Selenium         │       1       │  mg/day   │
└──────────────────────────┴───────────────┴───────────┘
```

## Project Structure

```
Equine-Nutrition-Calculator/
├── dataset/
│   ├── energy_protein_dry_matter.json  # Energy and protein requirement data
│   ├── macrominerals.csv               # Macromineral requirements
│   ├── microminerals.csv               # Micromineral requirements
│   └── vitamins.csv                    # Vitamin requirements
├── src/
│   ├── main.py                         # Main application and CLI interface
│   ├── calculations.py                 # Calculation logic for nutrients
│   ├── models.py                       # Data models and structures
│   └── file_reader.py                  # Data loading utilities
└── requirements.txt                    # Project dependencies
```

## Calculation Methodology

The calculator uses scientifically-based formulas to determine nutritional requirements:

- **Maintenance Energy**: Calculated using metabolic body weight (BW^0.75) with adjustments for keeper type
- **Workload Energy**: Additional energy requirements based on percentage increases or custom exercise calculations
- **Protein Requirements**: Calculated proportionally to total energy needs
- **Minerals & Vitamins**: Scaled based on body weight and workload intensity

## Workload Levels

| Level | Energy Increase | Typical Activities |
|-------|-----------------|-------------------|
| Maintenance | 0% | Pasture, no work |
| Light Work | 25% | Regular riding |
| Moderate Work | 50% | School horses, low level competition |
| Hard Work | 75% | Intensive training and competition |
| Very Hard Work | 120% | Elite level competition, race horses |

## Roadmap

Future enhancements planned:
- Hay and feed analysis integration
- Ration formulation and balancing
- Comparison of multiple feeding plans
- Export results to PDF/CSV
- Web-based interface
- Multi-horse management

## Data Sources

Nutritional requirements are based on **"Utfodringsrekommendationer för häst"** (Feeding Recommendations for Horses) published by the Swedish University of Agricultural Sciences (SLU - Sveriges lantbruksuniversitet). The reference data is stored in the `dataset/` directory and follows established equine nutrition research standards.

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

This calculator is designed as an educational tool and starting point for equine nutrition planning. Always consult with a qualified equine nutritionist or veterinarian for specific dietary recommendations, especially for horses with special needs, medical conditions, or performance requirements.

The nutritional data is based on Swedish research and standards, which may differ from recommendations in other countries or regions.

---

*Developed with 🐴 for better equine nutrition*