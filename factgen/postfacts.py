import requests
import json
import os
import sys

if __name__ == "__main__":
    sess = requests.Session()
    sess.auth = (os.environ["BRATOR_FACTS_USER"], os.environ["BRATOR_FACTS_PW"])
    endpoint = os.environ.get("BRATOR_FACTS_URL") or sys.argv[1]
    chunk = []
    def flush():
        resp = sess.post(endpoint, json=fact, allow_redirects=False)
        resp.raise_for_status()
        print(chunk[-1]["key"], len(chunk), resp.status_code, len(resp.content), resp.history)
        chunk.clear()
    for fact in json.load(sys.stdin):
        chunk.append(fact)
        if len(chunk) == 100:
            flush()
    if chunk:
        flush()
