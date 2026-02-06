import json
import csv

def csv_reader(file_path):
    with open(file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return reader
    
def json_reader(file_path):
   with open(file_path, "r", encoding="utf-8" ) as file:
            data = json.load(file)
            return data