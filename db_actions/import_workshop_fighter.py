import configparser
from pathlib import Path
import re
import sqlite3
import sys
import yaml
from roabet import config, db_con

__all__ = ("import_workshop_fighter")

def to_id(s: str):
    s = s.lower()
    s = re.sub(r"[\W_]+", "_", s)
    s = re.sub(r"^_|_$", "", s)
    return s

def import_official_fighters():
    with open('config/fighters.yaml') as f:
        fighter_data = yaml.load(f, yaml.Loader)
    
    con = sqlite3.connect('config/db/roabet.sqlite3')
    cur = con.cursor()

    cur.executemany("""
        INSERT INTO fighters (id, official, name, select_x, select_y) 
        VALUES (?, TRUE, ?, ?, ?)""", ((
            to_id(fighter['name']),
            fighter['name'],
            fighter['coords']['x'],
            fighter['coords']['y'],
        ) for fighter in fighter_data)
    )
    
    con.commit()
    con.close()

def import_workshop_fighters_from_yaml():
    with open('config/workshop_fighters.yaml') as f:
        fighter_data: list[dict] = yaml.load(f, yaml.Loader)
    
    con = sqlite3.connect('config/db/roabet.sqlite3')
    cur = con.cursor()

    i = 1

    for fighter in fighter_data:
        configfile = Path(config['steam_dir']) / config['workshop_path'] / fighter['workshop_id'] / 'config.ini'
        wsconfig = configparser.ConfigParser()
        wsconfig.read(configfile)
        wsdata = wsconfig['general']
        name = fighter.get('name') or wsdata.get('name')
        author = wsdata.get('author')
        cur.execute("""
            INSERT INTO fighters (id, name, steam_id, author, workshop_index, select_x, select_y, matchmaker_banned)
            VALUES (
                ?, ?, ?, ?, ?, 513, 110, ?
            )""", (to_id(name), name, fighter['workshop_id'], author, i, fighter.get('banned', False)))
        i += 1
    
    con.commit()
    con.close()

def import_workshop_fighter(steam_id):
    configfile: Path = Path(config['steam_dir']) / config['workshop_path'] / steam_id / 'config.ini'
    if not configfile.exists():
        raise FileNotFoundError(str(configfile))
    wsconfig = configparser.ConfigParser()
    wsconfig.read(configfile)
    wsdata = wsconfig['general']
    name = wsdata.get('name')
    if name:
        name = re.sub(r'"(.*)"', r'\1', name)
    if not name:
        raise ValueError("That character has no name!")
    author = wsdata.get('author')
    if author:
        author = re.sub(r'"(.*)"', r'\1', author) or None
    
    base_id = id = to_id(name)
    id_extra = 1
    
    cur = db_con.execute("""
        SELECT id FROM fighters
        WHERE id = ?""", (id,))
    while cur.fetchone():
        # prevent conflicts
        id = base_id + "-" + str(id_extra)
        cur = db_con.execute("""
            SELECT id FROM fighters
            WHERE id = ?""", (id,))

    cur = db_con.execute("""
        SELECT workshop_index FROM fighters
        WHERE workshop_index >= 1
        ORDER BY workshop_index DESC
        LIMIT 1""")
    last_index = cur.fetchone()['workshop_index']

    db_con.execute("""
        INSERT INTO fighters (id, name, steam_id, author, workshop_index, select_x, select_y)
        VALUES (?, ?, ?, ?, ?, 513, 110)""",
        (id, name, steam_id, author, last_index + 1)
    )

    print(f"Successfully imported {name}")

    db_con.commit()

if __name__ == "__main__":
    match = re.search(r"id=(\d+)", sys.argv[1])
    if match:
        import_workshop_fighter(match.group(1))
    else:
        import_workshop_fighter(sys.argv[1])