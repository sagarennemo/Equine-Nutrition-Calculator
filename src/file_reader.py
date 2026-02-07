import json
import csv
import pandas as pd

def csv_reader(file_path):
    reader = pd.read_csv(file_path)
    return reader
    
def json_reader(file_path):
   with open(file_path, "r", encoding="utf-8" ) as file:
            data = json.load(file)
            return data