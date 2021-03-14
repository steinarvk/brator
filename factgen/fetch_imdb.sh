#!/bin/bash
set -e
set -x

for ds in title.ratings name.basics title.principals title.basics; do
	wget --no-clobber "https://datasets.imdbws.com/${ds}.tsv.gz"
	if [[ ! -f "${ds}.tsv" ]]; then 
		gzip -d --keep ${ds}.tsv.gz
	fi
	if [[ ! -f "${ds}.nohdr.tsv" ]]; then 
		tail +2 ${ds}.tsv > ${ds}.nohdr.tsv
	fi
done

rm -f imdb.sqlite3


sqlite3 imdb.sqlite3 <<EOF
CREATE TABLE title_ratings (
	title_id TEXT PRIMARY KEY,
	averageRating REAL NOT NULL,
	numVotes INTEGER NOT NULL
);
CREATE TABLE name_basics (
	name_id TEXT PRIMARY KEY,
	primaryName TEXT NOT NULL,
	birthYear INTEGER,
	deathYear INTEGER,
	primaryProfessions TEXT,
	knownForTitles TEXT
);
CREATE TABLE title_principals (
	title_id TEXT NOT NULL,
	ordering INTEGER NOT NULL,
	name_id TEXT NOT NULL,
	category TEXT NOT NULL,
	job TEXT,
	characters TEXT
);
CREATE TABLE title_basics (
	title_id TEXT PRIMARY KEY,
	title_type TEXT NOT NULL,
	primary_title TEXT NOT NULL,
	original_title TEXT NOT NULL,
	is_adult INTEGER NOT NULL,
	release_year INTEGER NOT NULL,
	end_year INTEGER NULL,
	runtime_minutes INTEGER NULL,
	genres TEXT NULL
);
.mode ascii
.separator "\t" "\n"
.import title.ratings.nohdr.tsv title_ratings
.import name.basics.nohdr.tsv name_basics
.import title.principals.nohdr.tsv title_principals
.import title.basics.nohdr.tsv title_basics

CREATE INDEX title_principals_idx_name ON title_principals ( name_id );
CREATE INDEX title_principals_idx_title ON title_principals ( title_id );
EOF
