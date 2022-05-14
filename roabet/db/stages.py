import random
from roabet import db_con

class Stage:
    def __init__(self, data):
        self.id: str = data['id']
        self.name: str = data['name']
        self.official = bool(data['official'])
        self.select_x: int = data['select_x']
        self.select_y: int = data['select_y']

class Stages:
    def __init__(self):
        self.load_stages()
    
    def load_stages(self):
        cur = db_con.execute('SELECT * FROM stages')
        self.stages = [Stage(row) for row in cur]
    
    def select_stage(self):
        return random.choice(self.stages)