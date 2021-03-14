import sqlite3
import sys
import json
import csv

def list_actors(conn):
    cur = conn.cursor()
    cur.execute("SELECT name_id, primaryName, knownForTitles, primaryProfessions, birthYear, deathYear FROM name_basics WHERE knownForTitles IS NOT NULL AND birthYear IS NOT NULL")
    while True:
        rv = cur.fetchone()
        if rv is None:
            return
        professions = rv[3].split(",")
        if not professions:
            continue
        if professions[0] not in ("actor", "actress"):
            continue
        yield rv

def get_actor_birth_death(conn, name_id):
    cur = conn.cursor()
    cur.execute("SELECT birthYear, deathYear FROM name_basics WHERE name_id = ?", [name_id])
    birth, death = cur.fetchone()
    if birth == "\\N":
        birth = None
    if death == "\\N":
        death = None
    return birth, death

def get_rating(conn, title):
    cur = conn.cursor()
    cur.execute("SELECT averageRating, numVotes FROM title_ratings WHERE title_id = ?", [title])
    return cur.fetchone()

def get_rating_volumes(conn, titles):
    rv = []
    for title in titles:
        resp = get_rating(conn, title)
        if not resp:
            continue
        _, volume = resp
        rv.append(volume)
    return rv

def get_ratings(conn, titles):
    rv = []
    for title in titles:
        resp = get_rating(conn, title)
        if not resp:
            continue
        rating, _ = resp
        rv.append(rating)
    return rv

SUM_RATINGS_1900 = 250_000
SUM_RATINGS_1960 = 2_000_000

def expected_rating(by):
    if by == "\\N":
        return 9_999_999_999
    fame_by = by - 1900
    if fame_by < 0:
        return SUM_RATINGS_1900
    if fame_by > 60:
        return SUM_RATINGS_1960
    return SUM_RATINGS_1900 + (fame_by / 60) * (SUM_RATINGS_1960 - SUM_RATINGS_1900)


def get_top_billings(conn, name_id, ordering_limit=3, votes_limit=1000):
    cur = conn.cursor()
    cur.execute("""
    SELECT title_principals.title_id, title_principals.ordering, title_basics.title_type, title_basics.primary_title, title_ratings.numVotes, title_ratings.averageRating
    FROM title_principals, title_ratings, title_basics
    WHERE title_principals.title_id = title_ratings.title_id
    AND   title_principals.title_id = title_basics.title_id
    AND   title_principals.name_id = ?
    AND   title_principals.category IN ('actor', 'actress')
    AND   title_principals.ordering <= ?
    AND   title_ratings.numVotes > ?
    AND   title_basics.title_type IN ('movie', 'tvSeries')
    ;
    """, [name_id, ordering_limit, votes_limit])
    while True:
        row = cur.fetchone()
        if row is None:
            return
        yield row

def list_famous_actors(conn):
    cur = conn.cursor()
    for uid, name, known_for, profs, by, dy in list_actors(conn):
        title_uids = known_for.split(",")
        #volumes = get_rating_volumes(conn, title_uids)
        #threshold = expected_rating(by)

        billings = list(get_top_billings(conn, uid, ordering_limit=6, votes_limit=10_000))
        big_billings = list(get_top_billings(conn, uid, ordering_limit=3, votes_limit=50_000))
        huge_billings = list(get_top_billings(conn, uid, ordering_limit=10, votes_limit=500_000))

        #if not threshold:
        #    continue
        #if len(volumes) < 4:
        #    continue
        #if sum(volumes) < threshold:
        #    continue
        if len(billings) < 5:
            continue
        if len(big_billings) < 1:
            continue
        if len(huge_billings) < 1:
            continue

        yield uid, name

def list_rating_volumes(conn):
    for uid, name, known_for, profs, by, dy in list_actors(conn):
        title_uids = known_for.split(",")
        if by == "\\N":
            continue
        print(uid, by, sum(get_rating_volumes(conn, title_uids)))

def get_famous_actors(conn):
    cachefile = "famous_actors.cache.csv"
    try:
        with open(cachefile, "r") as f:
            for row in csv.reader(f):
                yield row
        return
    except FileNotFoundError:
        pass
    with open(cachefile, "x") as f:
        w = csv.writer(f)
        for row in list_famous_actors(conn):
            yield row
            w.writerow(list(row))
            f.flush()

def get_actor_birth_death_facts(conn):
    for uid, name in get_famous_actors(conn):
        if len(name.split()) <= 1:
            continue

        birth, death = get_actor_birth_death(conn, uid)
        if birth:
            yield {
                "key": "imdb-birthyear-of-" + uid,
                "category": "imdb-actor-birthdeath",
                "numeric": {
                    "question_text": f"What year was actor {name} born?",
                    "correct_answer": birth,
                    "correct_answer_unit": "none",
                },
            }

        if death:
            yield {
                "key": "imdb-deathyear-of-" + uid,
                "category": "imdb-actor-birthdeath",
                "numeric": {
                    "question_text": f"What year did actor {name} die?",
                    "correct_answer": death,
                    "correct_answer_unit": "none",
                },
            }

def get_facts(conn):
    yield from get_actor_birth_death_facts(conn)

if __name__ == "__main__":
    conn = sqlite3.connect(sys.argv[1])
    json.dump(list(get_facts(conn)), sys.stdout, indent="  ")
