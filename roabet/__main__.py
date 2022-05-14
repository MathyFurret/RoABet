import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
from roabet import config, db_con
from roabet.controller import Controllers
from roabet.db import Fighters, Stages

async def main():
    print("Loading data...")
    all_fighters = Fighters()
    all_stages = Stages()

    print("Starting game...")
    os.startfile(Path(config['steam_dir']) / config['game_path'])

    print("Starting controllers...")
    controllers = Controllers(2)
    controllers.set_workshop_length(len([f for f in all_fighters.fighters.values() if not f.official]))
    await asyncio.sleep(30)
    await controllers.init_local_play()
    await controllers.init_com_players()
    await controllers.each_player(lambda p: p.set_difficulty(9))
    await controllers.change_settings(stock=3, time=5)

    while True:
        fighters = all_fighters.choose_fighters()
        stage = all_stages.select_stage()

        print(f"Next match: {fighters[0].name} ({fighters[0].provisional_rating.rating})"
            f" vs {fighters[1].name} ({fighters[1].provisional_rating.rating}) on {stage.name}")

        await controllers.select_fighters(*fighters)
        await controllers.confirm_fighters()
        await controllers.select_stage(stage)

        win_detection_process = await asyncio.create_subprocess_exec(
            'env/Scripts/python', '-m', 'roabet.screenreader.win_detection_process', 
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        print("Game started. Awaiting result...")
        stdout, stderr = await win_detection_process.communicate()
        if win_detection_process.returncode:
            print("Win detector crashed!")
            print(stderr.decode())
            break
        else:
            winner = json.loads(stdout.decode())['winner']
            print(f"Result: {fighters[winner - 1].name} wins!")
            db_con.execute("""INSERT INTO matches
            (time, player1, player2, winner, stage)
            VALUES (?, ?, ?, ?, ?)""", (datetime.now(), fighters[0].id, fighters[1].id, winner, stage.id))
            db_con.commit()

        await asyncio.sleep(10)

        controllers.reset_cursor_pos()

        print("Refreshing fighters")
        all_fighters.load_fighters()

        # await controllers.quit()
        # break

asyncio.run(main())
