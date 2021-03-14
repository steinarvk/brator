import requests
import json
import os
import sys

if __name__ == "__main__":
    sess = requests.Session()
    sess.auth = (os.environ["BRATOR_FACTS_USER"], os.environ["BRATOR_FACTS_PW"])
    endpoint = os.environ.get("BRATOR_FACTS_URL") or sys.argv[1]
    for fact in json.load(sys.stdin):
        resp = sess.post(endpoint, json=fact)
        resp.raise_for_status()
        print(fact["key"])

