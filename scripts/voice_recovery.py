"""Detect local RVC energy collapses and retry with short, pitch-locked context."""
import numpy as np
from scipy.ndimage import binary_closing
from scipy.signal import resample_poly
import soundfile as sf


def envelopes(reference,converted,sr):
    step=max(1,round(.1*sr));centers=np.arange(0,len(reference),step)
    half=round(.5*sr);left=np.maximum(0,centers-half);right=np.minimum(len(reference),centers+half)
    result=[]
    for audio in (reference,converted):
        cumulative=np.r_[0.,np.cumsum(np.asarray(audio,dtype=float)**2)]
        result.append(np.sqrt(np.maximum(0,(cumulative[right]-cumulative[left])/(right-left))))
    return centers,*result


def detect_dropouts(reference,converted,sr):
    if reference.shape!=converted.shape or reference.ndim!=1 or not len(reference):raise ValueError('Abweichende Gesangsspuren.')
    if not all(np.isfinite(x).all() for x in (reference,converted)):raise ValueError('Ungültige Gesangsspuren.')
    centers,ref,new=envelopes(reference,converted,sr)
    active=ref>max(.003,float(np.percentile(ref,95))*.08)
    if np.sum(active)<15:return [],0.
    loss=20*np.log10(np.maximum(ref,1e-9)/np.maximum(new,1e-9))
    baseline=float(np.median(loss[active]))
    bad=binary_closing(active & (loss>baseline+9.),structure=np.ones(5,dtype=bool))
    edges=np.diff(np.r_[False,bad,False].astype(int));regions=[]
    for begin,end in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):
        if end-begin<12:continue
        start=max(0.,centers[begin]/sr-.4)
        finish=min(len(reference)/sr,centers[min(end,len(centers)-1)]/sr+.4)
        if regions and start-regions[-1]['end']<1.:
            regions[-1]['end']=finish
        else:regions.append({'start':start,'end':finish})
    # Keep each retry within 30 seconds including three seconds of context.
    bounded=[]
    for region in regions:
        cursor=region['start']
        while cursor<region['end']:
            end=min(cursor+24.,region['end'])
            bounded.append({'start':round(cursor,2),'end':round(end,2)})
            cursor=end
    return bounded[:3],baseline


def recover_dropouts(reference,converted,sr,pitch,pad,run,convert,progress):
    regions,baseline=detect_dropouts(reference,converted,sr)
    output=converted.copy();reports=[]
    for number,region in enumerate(regions):
        start,end=region['start'],region['end']
        left=max(0.,round(start-3.,2));right=min(np.floor(len(reference)/sr*100)/100,round(end+3.,2))
        a,b=round(left*sr),round(right*sr)
        expected=round((right-left+2*pad)*100)
        contour=np.asarray(pitch[round(left*100):round(left*100)+expected],dtype=np.float32).copy()
        if len(contour)!=expected:
            reports.append({**region,'accepted':False,'reason':'Tonhöhenkontext unvollständig.'});continue
        progress(f'Gesangseinbruch bei {int(start)//60}:{int(start)%60:02d} in kurzem Abschnitt neu umwandeln')
        source=run/f'recovery-{number}-input.wav';sf.write(source,reference[a:b],sr,subtype='FLOAT')
        rate,audio,actual_pitch=convert(source,contour)
        if not np.allclose(actual_pitch,contour,rtol=1e-6,atol=1e-6) or not np.array_equal(actual_pitch==0,contour==0):
            raise ValueError('Nachbearbeitung hat die vorgegebene Gesangsmelodie verändert.')
        if np.issubdtype(audio.dtype,np.integer):audio=audio.astype(float)/32768.
        sf.write(run/f'recovery-{number}-raw.wav',audio,rate,subtype='PCM_24')
        audio=resample_poly(audio,sr//np.gcd(sr,rate),rate//np.gcd(sr,rate))
        if abs(len(audio)-(b-a))>sr//20:raise ValueError('Nachbearbeitung hat abweichende Länge.')
        audio=np.pad(audio[:b-a],(0,max(0,b-a-len(audio))))
        x,y=round(start*sr),round(end*sr)
        _,ref,old=envelopes(reference[x:y],converted[x:y],sr)
        _,_,new=envelopes(reference[x:y],audio[x-a:y-a],sr)
        active=ref>max(.003,float(np.percentile(ref,95))*.08)
        old_loss=float(np.median(20*np.log10(np.maximum(ref[active],1e-9)/np.maximum(old[active],1e-9))))
        new_loss=float(np.median(20*np.log10(np.maximum(ref[active],1e-9)/np.maximum(new[active],1e-9))))
        accepted=bool(new_loss<old_loss-3 and np.isfinite(audio).all())
        gain=float(np.clip(10**((new_loss-baseline)/20),.5,2.))
        reports.append({**region,'context_start':left,'context_end':right,'accepted':accepted,
            'old_loss_db':old_loss,'retry_loss_db':new_loss,'match_gain':gain,'pitch_unchanged':True})
        if accepted:
            replacement=audio[x-a:y-a]*gain
            fade=min(round(.15*sr),len(replacement)//2)
            envelope=np.ones(len(replacement))
            if fade:
                envelope[:fade]=.5-.5*np.cos(np.linspace(0,np.pi,fade))
                envelope[-fade:]=.5+.5*np.cos(np.linspace(0,np.pi,fade))
            output[x:y]=converted[x:y]*(1-envelope)+replacement*envelope
    return output,{'version':'short-context-recovery-v1','baseline_loss_db':baseline,'attempts':reports,
                   'accepted_count':sum(r['accepted'] for r in reports),'melody_preserved':True}
