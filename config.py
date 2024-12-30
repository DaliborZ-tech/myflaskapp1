# config.py
import os

# MySQL připojovací URL pro SQLAlchemy
# "mysql://uzivatel:heslo@host/databaze"
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Dalibor654X@localhost/webusers"

# Když je True, tak SQLAlchemy vypisuje spoustu logů, pro produkci se dává False
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key pro Flask session
SECRET_KEY = os.urandom(24)  # nebo zadejte nějaký vlastní bezpečný řetězec
