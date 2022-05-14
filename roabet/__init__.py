import sqlite3
import yaml

with open('config/config.yaml') as f:
    config = yaml.load(f, yaml.Loader)

db_con = None
if not config['basic_mode']:
    db_con = sqlite3.connect('config/db/roabet.sqlite3')
    db_con.row_factory = sqlite3.Row
