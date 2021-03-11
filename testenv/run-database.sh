#!/bin/bash

POSTGRES_IMAGE=postgres:12
BRATOR_TEST_DIR=/tmp/brator_test_data

docker run -e POSTGRES_USER=${BRATOR_DB_USER} -e POSTGRES_PASSWORD=${BRATOR_DB_PASSWORD} -p 5432:5432 -v ${BRATOR_TEST_DIR}:/var/lib/postgresql/data ${POSTGRES_IMAGE}
