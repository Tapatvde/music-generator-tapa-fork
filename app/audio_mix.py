"""Keep a saved instrumental unchanged when adding a new mono vocal layer."""
def fixed_backing_gain(backing, vocals, ceiling=.95):
    import numpy as np
    if not np.isfinite(backing).all() or not np.isfinite(vocals).all():
        raise ValueError('Ungültige Audiowerte.')
    if np.max(np.abs(backing)) > ceiling:
        raise ValueError('Instrumentalbegleitung hat zu wenig Pegelreserve.')
    positive = vocals > 0
    negative = vocals < 0
    gain = 1.
    if positive.any():
        gain = min(gain, float(np.min((ceiling-backing[positive])/vocals[positive,None])))
    if negative.any():
        gain = min(gain, float(np.min((-ceiling-backing[negative])/vocals[negative,None])))
    gain = min(gain, ceiling/max(ceiling,float(np.max(np.abs(vocals)))))
    return max(0., gain)
