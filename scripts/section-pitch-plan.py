"""Read cached analysis and run the same octave planner used by synthesis.

No GPU, downloads, cache writes or conversion. Input/output are JSON on stdio.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'engine/rvc'))
sys.path.insert(0, str(ROOT))
import numpy as np
from app.chorus import chorus_regions, lyric_sections, section_kind
from app.register_policy import section_plan_issues, training_register_center
from infer.voice_range import apply_section_registers, midi_note


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def plan(spec):
    paths = {key: Path(spec[key]).resolve() for key in ('alignment', 'cache')}
    if any(not path.is_relative_to(ROOT) for path in paths.values()):
        raise ValueError('Analyse außerhalb des Forks.')
    cache = paths['cache']
    pitch = cache / 'section-f0-rmvpe-v1.npy'
    marker = json.loads(pitch.with_suffix('.json').read_text(encoding='utf-8'))
    stems = json.loads((cache / 'complete.json').read_text(encoding='utf-8'))
    vocals_hash = digest(cache / 'vocals.wav')
    if (marker.get('vocals') != vocals_hash or
        stems.get('hashes', {}).get('vocals.wav') != vocals_hash or
        marker.get('model') != digest(ROOT / 'engine/rvc/assets/rmvpe/rmvpe.pt') or
        marker.get('sha256') != digest(pitch)):
        return {'available': False, 'reason': 'stale_analysis'}
    aligned = json.loads(paths['alignment'].read_text(encoding='utf-8'))
    regions, rejected = chorus_regions(lyric_sections(spec['lyrics']), aligned['lines'], aligned['duration'], all_sections=True)
    settings = spec['request']['section_pitch']
    overrides = {r['section']: r['level'] for r in settings['overrides']}
    selected = [{**r, 'level': overrides.get(r['section'], settings.get(section_kind(r['tag']), 'auto'))} for r in regions]
    selected = [r for r in selected if r['level'] != 'auto']
    profile = {**spec['request'], 'mode': 'melody_phrases', 'boundary_margin_semitones': 1.}
    center = training_register_center(spec['request']['profile_id'])
    if center is not None:
        profile['register_center_midi'] = center
    source = np.load(pitch, allow_pickle=False)
    _, diagnostics, _ = apply_section_registers(source, source, profile, selected)
    for row in diagnostics:
        row['output_median_note'] = midi_note(round(row['output_median_midi']))
    issues = section_plan_issues(settings, spec['lyrics'], diagnostics)
    return {'available': True, 'sections': diagnostics, 'rejected': rejected, 'blocked':bool(issues), 'issues':issues,
            'training_center_note':midi_note(round(center)) if center is not None else None}


if __name__ == '__main__':
    try:
        print(json.dumps(plan(json.load(sys.stdin)), ensure_ascii=True))
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({'available': False, 'reason': 'analysis_unavailable'}))
