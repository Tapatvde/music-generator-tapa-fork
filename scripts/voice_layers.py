"""Offline vocal layers: explicit song-time regions, smooth edges, fixed intervals."""
import numpy as np


def region_envelope(length, rate, regions, offset=0, edge=.12):
    envelope = np.zeros(length, dtype=np.float64)
    for region in regions:
        start, end = float(region['start'])-offset, float(region['end'])-offset
        a, b = max(0, int(round(start*rate))), min(length, int(round(end*rate)))
        if b <= a:
            continue
        times = np.arange(a, b)/rate
        # Fade only at the actual region boundaries, not at a preview cut.
        weights = np.minimum(np.clip((times-start)/edge, 0, 1), np.clip((end-times)/edge, 0, 1))
        envelope[a:b] = np.maximum(envelope[a:b], .5-.5*np.cos(np.pi*weights))
    return envelope


def harmony_contour(lead, interval, regions, offset, padding, low=None, high=None):
    target = np.asarray(lead, dtype=np.float32).copy() * np.exp2(interval/12)
    times = np.arange(len(target))*.01-padding+offset
    active = np.zeros(len(target), dtype=bool)
    for region in regions:
        active |= (times >= region['start']) & (times < region['end'])
    suppressed = []
    voiced = np.flatnonzero(target > 0)
    groups = np.split(voiced, np.flatnonzero(np.diff(voiced)>45)+1) if len(voiced) else []
    if low is not None and high is not None:
        for group in groups:
            if not active[group].any():
                continue
            notes = 69+12*np.log2(target[group]/440)
            bottom, top = np.percentile(notes, [1, 99])
            if bottom < low-1 or top > high+1:
                # Omit the entire harmony phrase instead of octave-folding it
                # into unison or changing its interval halfway through a line.
                a, b = times[group[0]], times[group[-1]]+.01
                suppressed.append({'start':max(0., float(a)-.12), 'end':float(b)+.12})
                active[(times >= a-.12) & (times < b+.12)] = False
    target[~active] = 0
    return target, suppressed


def harmony_envelope(length, rate, regions, suppressed, offset=0):
    envelope = region_envelope(length, rate, regions, offset)
    for region in suppressed:
        envelope *= 1-region_envelope(length, rate, [region], offset, .08)
    return envelope
