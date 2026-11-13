from app.db import connect
from app import importers


def test_bank_import_synthetic(local_data, monkeypatch, tmp_path):
    path = tmp_path / 'fixture.xlsx'
    path.write_bytes(b'synthetic bank')
    rows = [{}, {'A':'Crystal','B':'Pikachu','D':'NS;NOT','E':'2','G':'Crystal','H':'si','I':'si'}]
    monkeypatch.setattr(importers, 'read_sheets', lambda *args: {'Juegos':rows})
    assert importers.import_bank(path)['tasks'] == 1
    assert importers.import_bank(path)['imported'] is False
    with connect() as db:
        row = db.execute('SELECT required,shiny,ot_exception FROM bank_tasks').fetchone()
        assert tuple(row) == (2,0,1)


def test_hunts_import_synthetic(local_data, monkeypatch, tmp_path):
    path = tmp_path / 'fixture.xlsm'
    path.write_bytes(b'synthetic hunts')
    data = {'Resets':[{}, {'B':'Pikachu','C':'0.01','D':'12'}],
            'DynaAdv.':[{}, {'B':'Eevee','C':'10','D':'0.1','E':'3','F':'2,5,?','G':'1'}]}
    monkeypatch.setattr(importers, 'read_sheets', lambda *args: data)
    assert importers.import_hunts(path)['hunts'] == 2
    assert importers.import_hunts(path)['imported'] is False
    with connect() as db:
        assert db.execute('SELECT count(*) FROM hunt_phases').fetchone()[0] == 2
        assert db.execute("SELECT unknown_phases FROM hunts WHERE pokemon='Eevee'").fetchone()[0] == 1
