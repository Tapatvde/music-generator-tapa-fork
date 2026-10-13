"""Slow, bounded independent layer gain; never sidechain the backing to vocals."""
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d

VERSION = 'independent-levels-v1'


def _envelope(audio, sr, seconds):
    # Stereo energy, without phase cancellation from downmixing.
    x=np.asarray(audio,dtype=np.float64)
    power=x*x if x.ndim==1 else np.mean(x*x,axis=1)
    cumulative=np.r_[0.,np.cumsum(power)]
    step=max(1,round(.05*sr));centers=np.arange(0,len(x),step)
    half=max(1,round(seconds*sr/2))
    left=np.maximum(0,centers-half);right=np.minimum(len(x),centers+half)
    return centers,np.sqrt(np.maximum(0,(cumulative[right]-cumulative[left])/(right-left)))


def _slow_gain(db, speed, step=.05):
    db=gaussian_filter1d(np.asarray(db,dtype=float),4,mode='nearest')
    for i in range(1,len(db)):db[i]=np.clip(db[i],db[i-1]-speed*step,db[i-1]+speed*step)
    for i in range(len(db)-2,-1,-1):db[i]=np.clip(db[i],db[i+1]-speed*step,db[i+1]+speed*step)
    return db


def stabilize_layers(lead, harmony, backing, sr, settings, reference=None):
    """Return processed layers and reproducible gain diagnostics.

    RVC uses the source lead as a local energy reference. Without a reference,
    the median of active vocal windows is used. Gain changes are limited, quiet
    pauses excluded, and backing fades protected. Harmony follows the lead.
    """
    lead=np.asarray(lead,dtype=np.float64);harmony=np.asarray(harmony,dtype=np.float64)
    backing=np.asarray(backing,dtype=np.float64)
    if lead.shape!=harmony.shape or len(lead)!=len(backing) or len(lead)==0:
        raise ValueError('Abweichende Länge der Mischspuren.')
    if sr<=0 or not all(np.isfinite(x).all() for x in (lead,harmony,backing)):
        raise ValueError('Ungültige Mischspuren.')
    if reference is not None:
        reference=np.asarray(reference,dtype=np.float64)
        if len(reference)!=len(lead) or not np.isfinite(reference).all():raise ValueError('Ungültige Gesangsreferenz.')
    positions,energy=_envelope(lead,sr,1.)
    vocal_db=np.zeros(len(positions));gate=np.ones(len(positions))
    if settings.get('vocals'):
        _,ref=_envelope(reference if reference is not None else lead,sr,1.)
        significant=ref[ref>max(1e-5,float(np.max(ref))*.04)]
        target=float(np.median(significant)) if len(significant) else 0.
        active=(ref>max(.001,target*.06)) & (energy>max(.0001,target*.01))
        desired=ref if reference is not None else np.full(len(ref),target)
        # RVC compensation restores losses only; an already present lead should
        # not be pushed back just because the original phrase was softer.
        lower=0. if reference is not None else -4.
        vocal_db[active]=np.clip(20*np.log10(np.maximum(desired[active],1e-9)/np.maximum(energy[active],1e-9)),lower,8.)
        vocal_db=_slow_gain(vocal_db,6.)
        if reference is not None:
            # The source defines real pauses: do not lift RVC's low-level tail.
            _,short=_envelope(reference,sr,.1)
            mask=short>max(.0003,float(np.percentile(short,95))*.015)
            gate=gaussian_filter1d(maximum_filter1d(mask.astype(float),size=13),2,mode='nearest')
    vocal_gain=np.interp(np.arange(len(lead)),positions,10**(vocal_db/20)*gate)
    vocal_gain*=10**(settings.get('vocal_db',0)/20)
    backing_db=np.zeros(len(positions))
    if settings.get('backing'):
        _,bed=_envelope(backing,sr,3.)
        significant=bed[bed>max(1e-5,float(np.max(bed))*.1)]
        target=float(np.median(significant)) if len(significant) else 0.
        active=bed>max(.001,target*.25)
        backing_db[active]=np.clip(20*np.log10(max(target,1e-9)/np.maximum(bed[active],1e-9)),-3.,3.)
        # Retain fade-in/out instead of chasing the tail towards a constant level.
        seconds=positions/sr;duration=len(lead)/sr
        edge=np.clip(np.minimum(seconds/3.,(duration-seconds)/12.),0,1)
        backing_db=_slow_gain(backing_db*edge,.8)
    bed_gain=np.interp(np.arange(len(lead)),positions,10**(backing_db/20))
    bed_gain*=10**(settings.get('backing_db',0)/20)
    processed_backing=backing*bed_gain if backing.ndim==1 else backing*bed_gain[:,None]
    report={'version':VERSION,'settings':dict(settings),'reference_used':reference is not None,
            'vocal_gain_min_db':float(np.min(vocal_db)),'vocal_gain_max_db':float(np.max(vocal_db)),
            'backing_gain_min_db':float(np.min(backing_db)),'backing_gain_max_db':float(np.max(backing_db)),
            'source_pause_gate':bool(settings.get('vocals') and reference is not None)}
    layer_gain=vocal_gain if lead.ndim==1 else vocal_gain[:,None]
    return lead*layer_gain,harmony*layer_gain,processed_backing,report
