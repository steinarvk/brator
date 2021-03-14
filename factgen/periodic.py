import json
import sys
import requests

URI = "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json"
CACHE = "periodic.cache.json"

def get_periodic_table_json():
    try:
        with open(CACHE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        pass

    resp = requests.get(URI)
    resp.raise_for_status()
    data = resp.json()
    with open(CACHE, "w") as f:
        json.dump(data, f, indent="  ")

    return data


def get_elements():
    return get_periodic_table_json()["elements"]

def get_meltboil_facts():
    for element in get_elements():
        name = f"{element['name'].lower()} ({element['symbol']})"
        melting_point_kelvin = element["melt"]
        boiling_point_kelvin = element["boil"]
        
        if melting_point_kelvin:
            yield {
                "key": "periodictable-melt-" + element["symbol"].lower(),
                "category": "periodictable-meltboil",
                "numeric": {
                    "question_text": f"What's the melting point (in Kelvin) of {name}?",
                    "correct_answer": melting_point_kelvin,
                    "correct_answer_unit": "kelvin",
                },
            }

        if boiling_point_kelvin:
            yield {
                "key": "periodictable-boil-" + element["symbol"].lower(),
                "category": "periodictable-meltboil",
                "numeric": {
                    "question_text": f"What's the boiling point (in Kelvin) of {name}?",
                    "correct_answer": boiling_point_kelvin,
                    "correct_answer_unit": "kelvin",
                },
            }

def get_density_facts():
    for element in get_elements():
        phase = element["phase"]
        name = f"{element['name'].lower()} ({element['symbol']}) in its {phase.lower()} form"

        grams_per_cc = element["density"]
        if not grams_per_cc:
            continue

        yield {
            "key": "periodictable-density-wocc-" + element["symbol"].lower() + "-" + phase,
            "category": "periodictable-density",
            "numeric": {
                "question_text": f"What's the mass (in grams) of one cubic centimeter (or milliliter) of {name}?",
                "correct_answer": grams_per_cc,
                "correct_answer_unit": "grams",
            },
        }

def get_atomic_number_facts():
    for element in get_elements():
        name = f"{element['name'].lower()} ({element['symbol']})"

        atomic_number = element["number"]
        if not atomic_number:
            continue

        yield {
            "key": "periodictable-atomic-number-" + str(atomic_number),
            "category": "periodictable-atomic-number",
            "numeric": {
                "question_text": f"What's the atomic number of {name}?",
                "correct_answer": atomic_number,
                "correct_answer_unit": "none",
            },
        }


def get_facts():
    yield from get_meltboil_facts()
    yield from get_density_facts()
    yield from get_atomic_number_facts()

if __name__ == "__main__":
    json.dump(list(get_facts()), sys.stdout, indent="  ")
