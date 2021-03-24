import requests
import json
import sys
import functools
import collections
from bs4 import BeautifulSoup

URI = "https://nssdc.gsfc.nasa.gov/planetary/factsheet/"
CACHE = "nasafactsheet.cache.html"
META = {
    "source": "Dr. David R. Williams, NASA Goddard Space Flight Center",
    "source_link": "https://nssdc.gsfc.nasa.gov/planetary/factsheet/",
}

REMAP_NAMES = {"MOON": "the Moon"}

def get_factsheet_data():
    try:
        with open(CACHE, "r") as f:
            return f.read()
    except FileNotFoundError:
        pass

    resp = requests.get(URI)
    resp.raise_for_status()
    return resp.content

def get_factsheet_soup():
    return BeautifulSoup(get_factsheet_data(), features="html.parser")

def capitalize(s):
    return s[0].upper() + s[1:].lower()

@functools.lru_cache
def get_planets_table():
    soup = get_factsheet_soup()
    table = [[td.text.strip("\xa0") for td in tr.find_all("td")] for tr in soup.table.find_all("tr")][:-1]
    planets = [REMAP_NAMES.get(s, capitalize(s)) for s in table[0][1:]]
    rv = collections.defaultdict(dict)
    for row in table[1:]:
        prop = row[0]
        for planet, value in zip(planets, row[1:]):
            if planet == "the Moon":
                continue
            rv[planet][prop] = value.replace(",", "")
    return dict(rv)

def get_diameter_facts():
    for planet, props in get_planets_table().items():
        value = float(props["Diameter (km)"])
        yield {
            "key": f"nasa-planet-diameter-{planet.lower()}",
            "category": "nasa-planet-diameter",
            "numeric": {
                "question_text": f"What's the equatorial diameter of {planet}, in kilometers?",
                "correct_answer": value,
                "correct_answer_unit": "km",
            },
            **META,
        }

def get_mass_facts():
    for planet, props in get_planets_table().items():
        value = float(props["Mass (1024kg)"])
        yield {
            "key": f"nasa-planet-mass-{planet.lower()}",
            "category": "nasa-planet-mass",
            "numeric": {
                "question_text": f"What's the mass of {planet}, in septillions of kilograms (10^24 kg)?",
                "correct_answer": value,
                "correct_answer_unit": "1E24 kg",
            },
            **META,
        }

def get_relative_mass_facts():
    planets = dict(get_planets_table())
    for planetA, propsA in planets.items():
        for planetB, propsB in planets.items():
            if planetA == planetB:
                continue
            a_bigger = float(propsA["Mass (1024kg)"]) > float(propsB["Mass (1024kg)"])
            yield {
                "key": f"nasa-planet-mass-relative-{planetA.lower()}-{planetB.lower()}",
                "category": "nasa-planet-mass-relative",
                "boolean": {
                    "question_text": f"{planetA} is a more massive planet than {planetB}.",
                    "correct_answer": a_bigger,
                },
                **META,
            }

def get_aphelion_perihelion_facts():
    for planet, props in get_planets_table().items():
        value = float(props["Aphelion (106 km)"])
        yield {
            "key": f"nasa-planet-aphelion-{planet.lower()}",
            "category": "nasa-planet-aphelion-perihelion",
            "numeric": {
                "question_text": f"What's the aphelion of {planet}, i.e. its maximal distance from the sun, in millions of km?",
                "correct_answer": value,
                "correct_answer_unit": "1E6 km",
            },
            **META,
        }

        value = float(props["Perihelion (106 km)"])
        yield {
            "key": f"nasa-planet-perihelion-{planet.lower()}",
            "category": "nasa-planet-aphelion-perihelion",
            "numeric": {
                "question_text": f"What's the perihelion of {planet}, i.e. its minimal distance from the sun, in millions of km?",
                "correct_answer": value,
                "correct_answer_unit": "1E6 km",
            },
            **META,
        }

def get_gravity_facts():
    for planet, props in get_planets_table().items():
        value = float(props["Gravity (m/s2)"])
        yield {
            "key": f"nasa-planet-gravity-{planet.lower()}",
            "category": "nasa-planet-gravity",
            "numeric": {
                "question_text": f"What's the gravitational acceleration on {planet}, in m/s²?",
                "correct_answer": value,
                "correct_answer_unit": "m/s²",
            },
            **META,
        }

def get_escape_velocity_facts():
    for planet, props in get_planets_table().items():
        value = float(props["Escape Velocity (km/s)"])
        yield {
            "key": f"nasa-planet-escapevelocity-{planet.lower()}",
            "category": "nasa-planet-escapevelocity",
            "numeric": {
                "question_text": f"What's the escape velocity on {planet}, in km/s?",
                "correct_answer": value,
                "correct_answer_unit": "km/s",
            },
            **META,
        }

def get_length_of_day_facts():
    for planet, props in get_planets_table().items():
        value = float(props["Length of Day (hours)"])
        yield {
            "key": f"nasa-planet-lengthofday-{planet.lower()}",
            "category": "nasa-planet-lengthofday",
            "numeric": {
                "question_text": f"What's the length of a solar day on {planet}, in hours?",
                "correct_answer": value,
                "correct_answer_unit": "hours",
            },
            **META,
        }

def get_orbital_period_facts():
    for planet, props in get_planets_table().items():
        value = float(props["Orbital Period (days)"])
        yield {
            "key": f"nasa-planet-lengthoforbit-{planet.lower()}",
            "category": "nasa-planet-lengthofday",
            "numeric": {
                "question_text": f"What's the orbital period of {planet}, i.e. the time it takes to complete one orbit around the sun, in Earth days?",
                "correct_answer": value,
                "correct_answer_unit": "days",
            },
            **META,
        }

def get_facts():
    yield from get_mass_facts()
    yield from get_diameter_facts()
    yield from get_aphelion_perihelion_facts()
    yield from get_gravity_facts()
    yield from get_escape_velocity_facts()
    yield from get_length_of_day_facts()
    yield from get_orbital_period_facts()
    yield from get_relative_mass_facts()

if __name__ == "__main__":
    json.dump(list(get_facts()), sys.stdout, indent="  ")
