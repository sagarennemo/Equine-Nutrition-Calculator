from text_extraction import process_all
from difflib import get_close_matches

# The nutrients we want, each with the label keywords that identify its row.
KEYWORDS = [
    "torrsubstans",
    "smältbart",
    "energi",
    "fosfor",
    "kalcium",
    "magnesium",
    "natrium",
    "koppar",
    "zinc",
    "mangan",
    "järn"
    ]

# Lookalike words that we don't want, so all words are as accurately matched as possible.
VOCABULARY = KEYWORDS + ["kalium", "råprotein", "svavel", "socker"]

# paths for the test images, for testing and debugging
FILE_PATHS = [
    "test_images/test_hay_analysis1.jpg", 
    "test_images/test_hay_analysis2.jpg", 
    "test_images/test_hay_analysis3.jpg",
    "test_images/hay_analysis.pdf"
    ]


def is_number(token):
    """True if the token is a number (handles Swedish decimal commas)."""
    try:
        float(token.strip("<>").replace(",", "."))
        return True
    except ValueError:
        return False

def parse_line(line):
    label_parts, numbers = [], []
    for token in line.split():
        low = token.lower()
        if numbers and ("torrsubstans" in low or low == "ts" or "foder" in low):
            break                      # trailing unit reached — ignore the rest of the line
        if is_number(token):
            numbers.append(float(token.strip("<>").replace(",", ".")))
        elif not numbers:
            label_parts.append(token)
    return " ".join(label_parts), numbers

def match_nutrient(label):
    for word in label.lower().split():
        matches = get_close_matches(word, VOCABULARY, n=1, cutoff=0.75)
        if matches and matches[0] in KEYWORDS:
            return matches[0]
    return None

def extract_nutrients(text):
    nutrients = {}
    for line in text.splitlines():
        label, numbers = parse_line(line)
        if not numbers:
            continue
        nutrient = match_nutrient(label)
        if nutrient is None:
            continue
        if nutrient == "torrsubstans":
            if nutrient not in nutrients:
                nutrients[nutrient] = [min(numbers)]
        elif nutrient not in nutrients:
            nutrients[nutrient] = numbers
        else:
            nutrients[nutrient].append(numbers[0]) 

    return {nutrient: nutrients.get(nutrient) for nutrient in KEYWORDS}     



def main():
    text = process_all([FILE_PATHS[0]])[0]["text"]
    print(extract_nutrients(text))


if __name__ == "__main__":
    main()



