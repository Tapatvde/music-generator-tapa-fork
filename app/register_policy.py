"""Never silently replace an explicitly requested section register."""
from .chorus import section_catalog
import json
import math
from pathlib import Path


def training_register_center(profile_id):
    """Observed register from this user's trained profile, without personal defaults."""
    from . import db
    row=db.one("SELECT result_meta FROM voice_training WHERE id=? AND status='done'",(profile_id,))
    try:
        value=float(json.loads(row['result_meta'])['range']['register_center_midi']) if row else None
        return value if value is not None and math.isfinite(value) and 32<=value<=84 else None
    except (ValueError,KeyError,TypeError):return None


def section_plan_issues(settings, lyrics, diagnostics):
    if not settings.get('enabled') or not settings.get('strict', True):
        return []
    overrides = {r['section']: r['level'] for r in settings.get('overrides', [])}
    planned = {r['section']: r for r in diagnostics}
    issues = []
    for section in section_catalog(lyrics):
        level = overrides.get(section['section'], settings.get(section['kind'], 'auto'))
        if level == 'auto':
            continue
        label = {'verse':'Strophe', 'chorus':'Refrain'}.get(section['kind'], '['+section['tag']+']')
        label += ' '+str(section['number']) if section['kind'] in ('verse','chorus') else ''
        row = planned.get(section['section'])
        reason = 'Zeitzuordnung oder Gesangsanalyse unsicher' if row is None else (
            'Wunschlage passt nicht zum eingestellten Stimmumfang' if row.get('range_limited') or row.get('range_conflict') else None)
        if reason:
            issues.append({'section':section['section'], 'label':label, 'reason':reason})
    return issues


def require_section_plan(settings, lyrics, diagnostics):
    issues = section_plan_issues(settings, lyrics, diagnostics)
    if issues:
        raise ValueError('Wunschtonlage kann nicht umgesetzt werden: '+
                         '; '.join(r['label']+': '+r['reason'] for r in issues)+
                         '. Keine ersatzweise tiefere Fassung erzeugt. Bitte Stimmumfang bzw. Abschnittsauswahl prüfen.')
