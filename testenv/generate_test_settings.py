#!/usr/bin/env python3
import secrets

print(f"export BRATOR_DB_PASSWORD={secrets.token_hex(40)}")
print(f"export BRATOR_SECRET_KEY={secrets.token_hex(40)}")
print(f"export BRATOR_DEBUG=True")
print(f"export BRATOR_DB_USER=brator_test")
