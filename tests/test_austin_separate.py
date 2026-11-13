"""Importer regressions for AustinJohn's two standalone spreadsheet exports."""
from pathlib import Path
import os

import pytest

from app import austin_import
from app.austin_import import build_austin_plan, _lookup_key
from app.db import connect


def rows_for_forms(n, shiny=False):
    with connect() as db:
        return [{'H': r['species'], 'I': str(r['dex_number']),
                 'V': r['form_key'], 'L': r['form_name'] or '', 'J': '1'}
                for r in db.execute('SELECT f.* FROM pokemon_forms AS f JOIN goals AS g ON g.form_key=f.form_key AND g.shiny=? ORDER BY f.dex_number,f.form_key LIMIT ?', (int(shiny), n))]


def test_separate_shiny_workbook_only_changes_shiny(monkeypatch, local_data):
    rows = rows_for_forms(150, shiny=True)
    rows[0]['J'] = '0'
    rows[1]['J'] = 'NOT'
    rows[2]['J'] = 'EVO'  # unknown: must not assume obtained/pending
    rows.insert(4, {'H': 'Gen', 'V': 'gen', 'J': '1'})  # grouping row
    monkeypatch.setattr(austin_import, 'list_sheet_names', lambda _: {'S-LivingFormLITE'})
    monkeypatch.setattr(austin_import, 'read_sheets', lambda _, want: {'S-LivingFormLITE': rows})
    plan = build_austin_plan(b'standalone-shiny', source='shiny')
    assert plan['sheets'] == ['S-LivingFormLITE']
    assert plan['counts']['matched'] >= 100
    assert plan['counts']['obtained'] == 1
    assert plan['counts']['not_ot'] == 1
    assert plan['counts']['evo_unresolved'] == 1
    assert plan['warnings_total'] == 1
    assert all(change['shiny'] for change in plan['changes'])
    with pytest.raises(ValueError, match='LivingFormLITE'):
        build_austin_plan(b'standalone-shiny', source='normal')


def test_separate_living_workbook_only_changes_normal(monkeypatch, local_data):
    rows = rows_for_forms(130)
    rows[0]['J'] = '0'
    monkeypatch.setattr(austin_import, 'list_sheet_names', lambda _: {'LivingFormLITE'})
    monkeypatch.setattr(austin_import, 'read_sheets', lambda _, want: {'LivingFormLITE': rows})
    plan = build_austin_plan(b'standalone-living', source='normal')
    assert plan['counts']['normal'] == 130
    assert all(change['shiny'] is False for change in plan['changes'])
    with pytest.raises(ValueError, match='S-LivingFormLITE'):
        build_austin_plan(b'standalone-living', source='shiny')


def test_floette_eternal_flower_is_in_new_catalog(local_data):
    with connect() as db:
        forms = {r['form_key']: dict(r) for r in db.execute('SELECT * FROM pokemon_forms')}
        assert _lookup_key({'H': 'Floette', 'I': '670', 'L': 'Eternal Flower', 'V': 'floette-5'}, forms) == 'floette-5'
        assert db.execute("SELECT COUNT(*) FROM goals WHERE form_key='floette-5'").fetchone()[0] == 2


