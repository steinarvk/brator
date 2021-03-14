import requests
import sys
import json

URI = "https://raw.githubusercontent.com/iancoleman/cia_world_factbook_api/master/data/factbook.json"
CACHE = "factbook.cache.json"

def get_factbook_json():
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

def get_countries():
    data = get_factbook_json()
    for country in data["countries"].values():
        try:
            orgs = country["data"]["government"]["international_organization_participation"]
            names = country["data"]["government"]["country_name"]
        except KeyError:
            continue
        orgs = set([o for o in [o.get("organization") for o in orgs] if o])
        if "UN" not in orgs:
            continue

        name = names["conventional_short_form"]

        yield name, country["data"]

def get_country_population_facts():
    for name, data in get_countries():
        population = data["people"]["population"]["total"]
        datestamp = data["people"]["population"]["date"]
        text = f"What is the total population of {name}? [Total population according to the CIA World Factbook, as of {datestamp}.]"
        yield {
            "key": "cia-population-" + "-".join(name.split()).lower(),
            "numeric": {
                "question_text": text,
                "correct_answer": int(population),
                "correct_answer_unit": "none",
            },
        }

def get_capital_location_facts():
    for name, data in get_countries():
        try:
            capital = data["government"]["capital"]
            geo = capital["geographic_coordinates"]
            lat = geo["latitude"]["minutes"]
            hemisphere = geo["latitude"]["hemisphere"]
            capital_name = capital["name"]
        except KeyError:
            continue

        if set(";:-") & set(capital_name):
            continue

        hem_name = {
            "N": "northern hemisphere",
            "S": "southern hemisphere",
        }[hemisphere]
        full_name = f"{capital['name']}, {name}"
        question = f"What's the latitude (within the {hem_name}) of {full_name}? [Truncated to an integral minute; between 0 and 90.]"

        yield {
            "key": "cia-capital-latitude-" + "-".join(full_name.split(", ")).lower(),
            "numeric": {
                "question_text": question,
                "correct_answer": lat,
                "correct_answer_unit": "none",
            },
        }

def get_land_area_facts():
    for name, data in get_countries():
        try:
            land_area = data["geography"]["area"]["land"]["value"]
            unit = data["geography"]["area"]["land"]["units"]
            if unit != "sq km":
                continue
        except KeyError:
            continue

        key = "cia-country-land-area-" + "-".join(name.split()).lower()

        text = f"What's the total land area of {name}? [According to the CIA World Factbook, in square kilometers.]"

        yield {
            "key": key,
            "numeric": {
                "question_text": text,
                "correct_answer": land_area,
                "correct_answer_unit": "sq km",
            },
        }

def _keyify(s):
    return "-".join(s.split()).lower()

def get_demographics_facts():
    for name, data in get_countries():
        try:
            ages = data["people"]["age_structure"]
            datestamp = ages["date"]
        except KeyError:
            continue

        for cat, catdata in ages.items():
            if cat.count("_to_") != 1:
                continue

            age0, age1 = cat.split("_to_")

            pct = catdata["percent"]

            question = f"What percentage of the population of {name} is between {age0} and {age1} years old? [According to the CIA World Factbook, as of {datestamp}.]"
            key = f"cia-demo-{_keyify(name)}-ages-{age0}-to-{age1}"

            yield {
                "key": key,
                "numeric": {
                    "question_text": question,
                    "correct_answer": pct,
                    "correct_answer_unit": "percent",
                },
            }


def get_facts():
    yield from get_country_population_facts()
    yield from get_capital_location_facts()
    yield from get_land_area_facts()
    yield from get_demographics_facts()


if __name__ == "__main__":
    json.dump(list(get_facts()), sys.stdout, indent="  ")
