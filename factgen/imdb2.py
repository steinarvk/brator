import sqlite3
import sys
import json
import csv

def list_famous_movies(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT title_basics.title_id,
               title_basics.primary_title,
               title_basics.release_year,
               title_basics.runtime_minutes,
               name_basics.primaryName,
               title_ratings.numVotes,
               title_ratings.averageRating,
               (SELECT COUNT(*) FROM title_principals WHERE title_principals.title_id = title_basics.title_id AND title_principals.category = "director") AS number_of_directors
        FROM title_basics
        LEFT JOIN title_ratings ON title_basics.title_id = title_ratings.title_id
        LEFT JOIN title_principals ON (title_principals.title_id = title_basics.title_id
                                       AND title_principals.category = "director")
        LEFT JOIN name_basics ON (name_basics.name_id = title_principals.name_id)
        WHERE title_ratings.numVotes > 100000
        AND   title_ratings.averageRating > 8.0
        AND   title_basics.is_adult = 0
        AND   title_basics.title_type = "movie"
        AND   name_basics.primaryName IS NOT NULL
        AND   title_basics.release_year IS NOT NULL
        AND   title_basics.runtime_minutes IS NOT NULL
        AND   number_of_directors = 1
    """)
    while True:
        rv = cur.fetchone()
        if not rv:
            return
        yield {
            "title_id": rv[0],
            "title": rv[1],
            "release_year": int(rv[2]),
            "runtime_minutes": int(rv[3]),
            "director": rv[4],
            "votes": int(rv[5]),
            "rating": float(rv[6]),
        }

def get_movie_runtime_facts(conn):
    for movie in list_famous_movies(conn):
        name = f"{repr(movie['title'])} (directed by {movie['director']})"
        yield {
            "key": "imdb-movie-runtime-" + movie["title_id"],
            "category": "imdb-movie-runtime",
            "source": "IMDb",
            "source_link": "https://www.imdb.com/interfaces/",
            "fine_print": "Runtime in minutes as recorded by IMDb.",
            "numeric": {
                "question_text": f"What's the runtime (in minutes) of the movie {name}?",
                "correct_answer": movie["runtime_minutes"],
                "correct_answer_unit": "minutes",
            },
        }

def get_movie_release_year_facts(conn):
    for movie in list_famous_movies(conn):
        name = f"{repr(movie['title'])} (directed by {movie['director']})"
        yield {
            "key": "imdb-movie-release-year-" + movie["title_id"],
            "category": "imdb-movie-release-year",
            "source": "IMDb",
            "source_link": "https://www.imdb.com/interfaces/",
            "fine_print": "Initial release year as recorded by IMDb.",
            "numeric": {
                "question_text": f"What year was the movie {name} released?",
                "correct_answer": movie["release_year"],
                "correct_answer_unit": "none",
            },
        }

def get_facts(conn):
    yield from get_movie_runtime_facts(conn)
    yield from get_movie_release_year_facts(conn)

if __name__ == "__main__":
    conn = sqlite3.connect(sys.argv[1] if len(sys.argv) > 1 else "imdb.sqlite3")
    json.dump(list(get_facts(conn)), sys.stdout, indent="  ")
