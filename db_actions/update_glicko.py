from datetime import datetime
import sys
from roabet import db_con
from roabet.db.fighters import Fighters

def update_glicko():
    fighters = Fighters(always_update_ratings=True)

    db_con.executemany("UPDATE fighters SET glicko_rating=?, glicko_deviation=? WHERE id=?", 
        ((fighter.provisional_rating.rating, fighter.provisional_rating.dev, fighter.id) for fighter in fighters.fighters.values()))

    last_match = db_con.execute("SELECT id FROM matches ORDER BY id DESC LIMIT 1").fetchone()['id']
    db_con.execute("INSERT INTO rating_cycles (ended_at, last_match) VALUES (?, ?)", (datetime.now(), last_match))
    db_con.commit()

if __name__ == "__main__":
    update_glicko()