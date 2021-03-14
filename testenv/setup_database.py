#!/usr/bin/env python3
import secrets
import os
import sys

def setup_env(name):
    db_user = name
    db_name = name
    db_password = secrets.token_hex(40)
    secret_key = secrets.token_hex(40)
    db_host = os.environ["BRATOR_DB_HOST"]
    facts_user = f"{name}_facts"
    facts_pw = secrets.token_hex(20)

    with open(f"brator.{name}.generated.env.sh", "x") as f:
        print(f"""
export BRATOR_ENV_NAME={name}
export BRATOR_SECRET_KEY={secret_key}
export BRATOR_DB_PASSWORD={db_password}
export BRATOR_DB_USER={db_user}
export BRATOR_DB_NAME={db_name}
export BRATOR_DB_HOST={db_host}

export BRATOR_FACTS_USER={facts_user}
export BRATOR_FACTS_PW={facts_pw}
""", file=f)

    print(f"""
CREATE DATABASE {db_name};
CREATE USER {db_user} WITH ENCRYPTED PASSWORD '{db_password}';
GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};
""")

if __name__ == "__main__":
    setup_env(sys.argv[1])
