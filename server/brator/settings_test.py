import os

os.environ["BRATOR_SECRET_KEY"] = "testkey"
os.environ["BRATOR_DEBUG"] = "True"

from .settings import *
