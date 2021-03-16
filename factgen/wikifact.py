import sys
import hashlib
import json
import re
from bs4 import BeautifulSoup

EN_DASH = "–"

REMOVE = re.compile(" [(][^()]*(pictured|depicted)[)]")

def get_facts_from_anniversaries_page(filename):
    with open(filename) as f:
        lines = BeautifulSoup(f, features="html.parser").text.splitlines()
    for line in lines:
        if EN_DASH not in line:
            continue
        year, desc = line.split(EN_DASH, 1)

        year = year.strip()

        try:
            int(year)
        except ValueError:
            continue

        if year in desc:
            continue
        
        desc = REMOVE.sub("", desc)

        text = f"{desc.strip()} What year did this happen?"
        shorthash = hashlib.sha256(desc.encode()).hexdigest()[:8]
        yield {
            "key": f"wikipedia-history-{year}-{shorthash}",
            "category": "wikipedia-history",
            "numeric": {
                "question_text": text,
                "correct_answer": int(year),
                "correct_answer_unit": "none",
            },
        }

if __name__ == "__main__":
    facts = get_facts_from_anniversaries_page(sys.argv[1])
    json.dump(list(facts), sys.stdout, indent="  ")
