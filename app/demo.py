"""Disposable fictional demo. Never opens an existing user database."""
import os
import tempfile
from pathlib import Path
from .db import initialize, connect


def seed_demo():
    initialize()
    with connect() as db:
        db.execute("UPDATE goals SET in_home=1 WHERE form_key IN ('bulbasaur','charmander','squirtle') AND shiny=0")
        db.execute("UPDATE goals SET in_home=1 WHERE form_key='pikachu' AND shiny=1")
        db.execute("INSERT INTO bank_game_status(game,started,prepared) VALUES ('Crystal',1,1)")
        db.execute("INSERT INTO bank_tasks(game,pokemon,required,caught,comments) VALUES ('Crystal','Celebi',1,0,'Ejemplo ficticio')")
        db.execute("INSERT INTO hunts(pokemon,game,method,probability,attempts,status,source,created_at) VALUES ('Magikarp','Ejemplo','Encuentros ficticios',0.000244140625,123,'active','demo','2000-01-01 00:00:00')")


def main():
    import uvicorn
    # Ignore any inherited data directory; each run starts from fictional data.
    with tempfile.TemporaryDirectory(prefix='optpoke-demo-') as directory:
        os.environ['OPTPOKE_DATA_DIR'] = directory
        os.environ['OPTPOKE_DEMO'] = '1'
        seed_demo()
        print('DEMO: datos ficticios temporales. http://127.0.0.1:8001')
        uvicorn.run('app.main:app', host='127.0.0.1', port=8001)


if __name__ == '__main__':
    main()
