import csv
import json
import sys

def read_surnames(limit=50_000):
    with open("Names_2010Census.csv", "r") as f:
        rd = csv.reader(f)
        headers = next(rd)
        for row in rd:
            data = dict(zip(headers, row))
            name = data["name"]
            if name == "ALL OTHER NAMES":
                continue
            freq = int(data["count"])
            if freq > limit:
                yield data["name"], freq

def get_surname_facts():
    for name, freq in read_surnames():
        yield {
            "key": f"census-surname-{name}",
            "category": "census-surname",
            "numeric": {
                "question_text": f"In 2010, how many people in the US had the surname '{name}'?",
                "correct_answer": freq,
                "correct_answer_unit": "none",
            },
            "fine_print": "As registered in the 2010 US Census. Capitalization data is not available.",
            "source": "United States Census Bureau (2010 Census (2010 Census))",
            "source_link": "https://www.census.gov/topics/population/genealogy/data/2010_surnames.html",
        }

def get_facts():
    yield from get_surname_facts()

if __name__ == "__main__":
    json.dump(list(get_facts()), sys.stdout, indent="  ")
