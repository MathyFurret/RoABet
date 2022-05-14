import random
from roabet import db_con
from roabet.util import glicko

from typing import Optional

class Character:
    def __init__(self, data):
        self.id: str = data['id']
        self.official = bool(data['official'])
        self.name: str = data['name']
        self.steam_id: str = data['steam_id']
        self.select_x: int = data['select_x']
        self.select_y: int = data['select_y']
        self.banned = bool(data['matchmaker_banned'])
        self.uber = bool(data['is_uber'])
        self.potato = bool(data['is_potato'])
        self.load_time: int = data['load_time']
        self.workshop_index: int = data['workshop_index']
        self.rating = glicko.Rating(data['glicko_rating'], data['glicko_deviation'])
        self.provisional_rating: glicko.Rating = self.rating
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Character) and other.id == self.id
    
    def exclude_from_rating(self) -> bool:
        return self.uber or self.potato
    
    def get_steam_url(self) -> Optional[str]:
        return self.steam_id and f"https://steamcommunity.com/sharedfiles/filedetails/?id={self.steam_id}"


def ok_matchup(fighter1: Character, fighter2: Character, dev_range: float) -> bool:
    if fighter1 == fighter2: return False
    max_diff = max(fighter1.provisional_rating.dev, fighter2.provisional_rating.dev) * dev_range
    return abs(fighter1.provisional_rating.rating - fighter2.provisional_rating.rating) <= max_diff

class Fighters:
    def __init__(self, *, always_update_ratings: bool=False):
        self.always_update_ratings = always_update_ratings
        self.load_fighters()
    
    def load_fighters(self):
        cur = db_con.execute('SELECT * FROM fighters')
        self.fighters = {row['id']: Character(row) for row in cur}
        self.matchmaker_pool = [fighter for fighter in self.fighters.values() if not fighter.banned 
            and not fighter.uber and not fighter.potato]
        self.calc_provisional_ratings()
    
    def calc_provisional_ratings(self):
        last_period = db_con.execute("SELECT last_match FROM rating_cycles ORDER BY id DESC LIMIT 1").fetchone()['last_match']

        old_ratings: dict[str, glicko.Rating] = {}

        # Step 1
        for fighter in self.fighters.values():
            if fighter.exclude_from_rating():
                continue
            old_ratings[fighter.id] = glicko.tick_rating(fighter.rating)
        
        # Step 2
        for fighter in old_ratings:
            cur = db_con.execute("""
                SELECT player1, player2, winner FROM matches
                WHERE (player1=:fighter OR player2=:fighter)
                AND id > :start""", {'fighter': fighter, 'start': last_period})
            
            matches = []
            for row in cur:
                if row['winner'] not in {1, 2}: continue
                if (row['player1'] == fighter and row['winner'] == 1) or (row['player2'] == fighter and row['winner'] == 2):
                    score = 1.0
                else:
                    score = 0.0
                if row['player1'] == fighter:
                    opponent = row['player2']
                else:
                    opponent = row['player1']
                
                if opponent not in old_ratings:
                    continue
                
                matches.append((old_ratings[opponent], score))
            
            if self.always_update_ratings or len(matches) > 0:
                # should only give a provisional rating if we've completed at least 1 match this cycle
                self.fighters[fighter].provisional_rating = glicko.update_rating(old_ratings[fighter], matches)

    
    def choose_fighters(self):
        dev_range = 2.0
        # if random.random() > 0.7:
        #     dev_range = 2
        
        while True:
            fighter1 = random.choice(self.matchmaker_pool)
            possible_opponents = [fighter for fighter in self.matchmaker_pool if ok_matchup(fighter1, fighter, dev_range)]
            if not possible_opponents:
                print(f"Couldn't find a matchup for {fighter1.name} ({fighter1.provisional_rating})")
                continue
            fighter2 = random.choice(possible_opponents)
            result = [fighter1, fighter2]
            random.shuffle(result)
            return result
