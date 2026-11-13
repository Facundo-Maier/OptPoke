"""Regressions for interpreting AustinJohn LITE statuses and safe imports."""
import hashlib
from app.db import connect
from app.austin_import import _status, _lookup_key, build_austin_plan, apply_austin_plan


def test_not_means_no_ot_not_obtained(monkeypatch, local_data):
    from app import austin_import
    data = {
        'S-LivingFormLITE': [{'H':'Bulbasaur','I':'1','J':'NOT','V':'bulbasaur'}],
        'LivingFormLITE': [
            {'H':'Bulbasaur','I':'1','J':'0','V':'bulbasaur'},
            {'H':'Ivysaur','I':'2','J':'1','V':'ivysaur'},
        ]
    }
    monkeypatch.setattr(austin_import,'read_sheets',lambda _bytes,_wanted:data)
    monkeypatch.setattr(austin_import,'list_sheet_names',lambda _bytes:set(data))
    # Our guard rejects a forged sheet with fewer than 100 mapped rows.
    data['S-LivingFormLITE'] += [
        {'H':f['species'],'I':str(f['dex_number']),'J':'1','V':f['form_key'],
         'L':f['form_name'] or ''}
        for f in _first_forms(150)
        if f['form_key'] != 'bulbasaur'
    ]
    with connect() as db:
        shiny=db.execute("SELECT id,in_home FROM goals WHERE form_key='bulbasaur' AND shiny=1").fetchone()
        normal=db.execute("SELECT id,in_home FROM goals WHERE form_key='bulbasaur' AND shiny=0").fetchone()
        second=db.execute("SELECT id FROM goals WHERE form_key='ivysaur' AND shiny=0").fetchone()
        db.execute("UPDATE goals SET in_home=1 WHERE id=?",(second['id'],))
    plan=build_austin_plan(b'valid-byte-fixture',mode='merge')
    austin=next(x for x in plan['changes'] if x['goal_id']==shiny['id'])
    assert austin['updates']=={'ot_exception':1}
    assert not any(x['goal_id']==second['id'] for x in plan['changes'])
    apply_austin_plan(plan)
    with connect() as db:
        a=db.execute('SELECT in_home,ot_exception FROM goals WHERE id=?',(shiny['id'],)).fetchone()
        b=db.execute('SELECT in_home FROM goals WHERE id=?',(normal['id'],)).fetchone()
        c=db.execute('SELECT in_home FROM goals WHERE id=?',(second['id'],)).fetchone()
    assert (a['in_home'],a['ot_exception'])==(0,1)
    assert b['in_home']==1 and c['in_home']==1


def _first_forms(n):
    from app.db import connect
    with connect() as db:
        return [dict(f) for f in db.execute("SELECT * FROM pokemon_forms ORDER BY dex_number,form_key LIMIT ?",(n,))]


def test_not_does_not_reset_home_in_replace_mode(monkeypatch,local_data):
    from app import austin_import
    records=[{'H':f['species'],'I':str(f['dex_number']),'J':'1','V':f['form_key'],
              'L':f['form_name'] or ''} for f in _first_forms(110)]
    records[0]['J']='NOT'
    monkeypatch.setattr(austin_import,'read_sheets',lambda _bytes,_wanted:
                        {'S-LivingFormLITE':records, 'LivingFormLITE':records[:1]})
    monkeypatch.setattr(austin_import,'list_sheet_names',lambda _bytes:{'S-LivingFormLITE','LivingFormLITE'})
    goal_id=next(g['id'] for g in _fetch_goals('shiny') if g['form_key']=='bulbasaur')
    with connect() as db:db.execute('UPDATE goals SET in_home=1 WHERE id=?',(goal_id,))
    p=build_austin_plan(b'fixture',mode='replace')
    a=next(x for x in p['changes'] if x['goal_id']==goal_id)
    assert a['updates']=={'ot_exception':1}
    apply_austin_plan(p)
    with connect() as db:
        assert tuple(db.execute('SELECT in_home,ot_exception FROM goals WHERE id=?',(goal_id,)).fetchone()) == (1,1)


def _fetch_goals(kind):
    with connect() as db:
        return [dict(g) for g in db.execute('SELECT * FROM goals WHERE shiny=?',(int(kind=='shiny'),))]


def test_status_recognizes_numeric_and_not():
    assert [_status(x) for x in ('0.0','1','NOT','Not','1.0','0')] == ['0','1','NOT','NOT','1','0']
    assert _status('unknown') is None


def test_pumpkaboo_suffix_drift_does_not_corrupt_forms(local_data):
    from app.db import connect
    with connect() as db:forms={r['form_key']:dict(r) for r in db.execute('SELECT * FROM pokemon_forms')}
    # Austin's shiny sheet labels keyword '-2' Large, while the catalog key -3 is Large.
    row={'H':'Pumpkaboo','I':'710','L':'Large','V':'pumpkaboo-2'}
    assert _lookup_key(row,forms)=='pumpkaboo-3'


def test_austin_api_requires_matching_preview_digest(client, monkeypatch):
    from app import main
    # Test HTTP behavior independently from workbook contents.
    def make_plan(content, mode, source=None):
        return {'digest':hashlib.sha256(content).hexdigest(),'mode':mode,
                'counts':{'matched':2496,'changed':0},'changes':[],'warnings':[],'warnings_total':0}
    monkeypatch.setattr(main,'build_austin_plan',make_plan)
    response=client.post('/api/austin/preview',content=b'demo')
    assert response.status_code==200
    assert client.post('/api/austin/apply?digest=bad',content=b'demo').status_code==409
    assert client.post('/api/austin/apply?digest='+response.json()['digest'],content=b'demo').status_code==200


def test_austin_zero_adds_only_one_copy_even_when_target_is_three(monkeypatch,local_data):
    from app import austin_import
    rows=[{'H':f['species'],'I':str(f['dex_number']),'J':'1','V':f['form_key'],
           'L':f['form_name'] or ''} for f in _first_forms(150)]
    rows[0]['J']='0'
    monkeypatch.setattr(austin_import,'read_sheets',lambda _bytes,_wanted:
                        {'S-LivingFormLITE':rows,'LivingFormLITE':[]})
    monkeypatch.setattr(austin_import,'list_sheet_names',lambda _bytes:{'S-LivingFormLITE','LivingFormLITE'})
    with connect() as db:
        g=db.execute("SELECT id FROM goals WHERE shiny=1 AND form_key='bulbasaur'").fetchone()
        db.execute('UPDATE goals SET target=3 WHERE id=?',(g['id'],))
    plan=build_austin_plan(b'fake',mode='merge')
    change=next(x for x in plan['changes'] if x['goal_id']==g['id'])
    assert change['updates']=={'in_home':1}
    apply_austin_plan(plan)
    with connect() as db:
        rec=db.execute('SELECT target,in_home FROM goals WHERE id=?',(g['id'],)).fetchone()
    assert (rec['target'],rec['in_home'])==(3,1)
