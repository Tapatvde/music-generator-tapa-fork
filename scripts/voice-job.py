"""One offline GPU job. Models/caches stay within the fork; progress is machine readable."""
import gc
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

spec_path = Path(sys.argv[1]).resolve()
spec = json.loads(spec_path.read_text(encoding="utf-8"))
ROOT = Path(spec["root"]).resolve()
RUN = Path(spec["run"]).resolve()
RVC = ROOT / "engine/rvc"
req = spec["request"]
sys.argv = [sys.argv[0]]  # RVC's Config owns argv parsing.
sys.path.insert(0, str(RVC))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from app.review import listening_regions
from voice_layers import harmony_contour, harmony_envelope
from app.chorus import ALIGNMENT_VERSION, validate_auto_lyrics, chorus_regions, section_kind
from app.register_policy import require_section_plan, training_register_center
os.chdir(RVC)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def progress(message):
    print("VOICE_PROGRESS " + json.dumps({"message":message}, ensure_ascii=False), flush=True)


def command(args):
    subprocess.run([str(a) for a in args], check=True, creationflags=0x08000000 if os.name == "nt" else 0)


def valid_stems(cache):
    marker=cache/'complete.json'
    if not marker.is_file():return False
    saved=json.loads(marker.read_text(encoding='utf-8'))
    return all((cache/name).is_file() and sha(cache/name)==saved.get('hashes',{}).get(name) for name in ('vocals.wav','instrumental.wav'))


def separate_to_cache(cache, job_run, job_spec):
    cache.mkdir(parents=True,exist_ok=True)
    path=job_run/'separation-request.json';path.write_text(json.dumps(job_spec,ensure_ascii=False,indent=2),encoding='utf-8')
    command([RVC/'.venv/Scripts/python.exe','-u',ROOT/'scripts/voice-separate.py',path])
    for name in ('vocals','instrumental'):
        matches=list((job_run/'stems').glob(f'*_{name}.wav'))
        if len(matches)!=1:raise ValueError(f'Gesangstrennung: {name} fehlt oder ist mehrdeutig.')
        tmp=cache/f'{name}.tmp';shutil.copyfile(matches[0],tmp);tmp.replace(cache/f'{name}.wav')
    marker=cache/'complete.json';tmp=marker.with_suffix('.tmp')
    tmp.write_text(json.dumps({'recipe':spec['recipe'],'quality':req['quality'],
        'hashes':{name:sha(cache/name) for name in ('vocals.wav','instrumental.wav')}},indent=2),encoding='utf-8');tmp.replace(marker)


def main():
    import numpy as np
    import soundfile as sf
    import torch
    from scipy.signal import resample_poly

    source = Path(spec["source"])
    model = Path(spec["profile"]["model"])
    index = Path(spec["profile"]["index"])
    for path in (RUN, source, model, index):
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError("Dateipfad außerhalb des Forks.")
    protected = {str(p):sha(p) for p in (source, model, index)}
    source_hash = protected[str(source)]
    harmony_settings = dict(req.get('harmony',{}))
    automatic = harmony_settings.get('enabled') and harmony_settings.get('mode')=='lyrics'
    pitch_settings=req.get('section_pitch',{})
    section_control=pitch_settings.get('enabled',False)
    align_sections=automatic or section_control
    if align_sections:sections=validate_auto_lyrics(spec.get('lyrics',''),require_chorus=automatic)
    scope = f"preview-{req['preview_start']:.3f}-{req['preview_seconds']:.3f}" if req['preview'] else "full"
    cache = ROOT / "data/voice-cache" / source_hash / f"{spec['recipe']}-{req['quality']}-{scope}"
    cache.mkdir(parents=True, exist_ok=True)
    clock = time.perf_counter()
    progress("Audio vorbereiten")
    input_wav = RUN / "input.wav"
    args = [RVC / "ffmpeg.exe", "-nostdin", "-y", "-hide_banner", "-loglevel", "error"]
    if req["preview"]:
        args += ["-ss", req["preview_start"]]
    args += ["-i", source]
    if req["preview"]:
        args += ["-t", req["preview_seconds"]]
    command(args + ["-ar", "44100", "-ac", "2", "-c:a", "pcm_f32le", input_wav])
    info = sf.info(input_wav)
    if info.duration < 1:
        raise ValueError("Vorschau zu kurz oder hinter dem Songende.")
    times = {}
    cached = valid_stems(cache)
    if not cached:
        progress("Gesang trennen" + (" · zusätzliche Qualitätsdurchläufe" if req["quality"] == "best" else ""))
        start = time.perf_counter()
        # A separate process releases all separator CUDA allocations before RVC.
        separate_to_cache(cache,RUN,spec)
        times["separation"] = time.perf_counter() - start
    else:
        progress("Vorhandene Gesangstrennung verwenden")
        times["separation"] = 0

    alignment=None
    full_cache=cache.parent/f"{spec['recipe']}-{req['quality']}-full"
    section_regions=[];section_rejected=[]
    if align_sections:
        lyrics=spec['lyrics'];text_hash=hashlib.sha256(lyrics.encode('utf-8')).hexdigest()
        alignment_path=ROOT/'data/chorus-cache'/source_hash/f"{ALIGNMENT_VERSION}-{spec['recipe']}-{req['quality']}-{text_hash}.json"
        alignment_path.parent.mkdir(parents=True,exist_ok=True)
        if alignment_path.is_file():alignment=json.loads(alignment_path.read_text(encoding='utf-8'))
        if alignment and (not section_control or alignment.get('lines')):
            times['alignment']=0
        else:
            full_cache=cache.parent/f"{spec['recipe']}-{req['quality']}-full"
            if not valid_stems(full_cache):
                progress('Gesang trennen · vollständiger Song für Refrainabgleich')
                full_run=RUN/'chorus-source';full_run.mkdir(exist_ok=True)
                command([RVC/'ffmpeg.exe','-nostdin','-y','-hide_banner','-loglevel','error','-i',source,'-ar','44100','-ac','2','-c:a','pcm_f32le',full_run/'input.wav'])
                start=time.perf_counter()
                full_spec={**spec,'run':str(full_run),'request':{**req,'preview':False}}
                separate_to_cache(full_cache,full_run,full_spec)
                times['separation']+=time.perf_counter()-start
            progress('Refrains aus [chorus] im Gesang zuordnen')
            alignment_spec={**spec,'source_hash':source_hash,'require_chorus':automatic,'alignment_audio':str(full_cache/'vocals.wav'),'alignment_output':str(alignment_path)}
            path=RUN/'alignment-request.json';path.write_text(json.dumps(alignment_spec,ensure_ascii=False,indent=2),encoding='utf-8')
            start=time.perf_counter()
            command([RVC/'.venv/Scripts/python.exe','-u',ROOT/'scripts/align-choruses.py',path])
            times['alignment']=time.perf_counter()-start
            alignment=json.loads(alignment_path.read_text(encoding='utf-8'))
        if automatic and not alignment.get('regions'):
            raise ValueError('Die [chorus]-Abschnitte konnten dem Gesang nicht zuverlässig zugeordnet werden. Bitte Refrainzeiten manuell festlegen.')
        if automatic:harmony_settings['regions']=[{k:r[k] for k in ('start','end')} for r in alignment['regions']]
        if section_control:
            detected,section_rejected=chorus_regions(sections,alignment['lines'],alignment['duration'],all_sections=True)
            overrides={r['section']:r for r in pitch_settings.get('overrides',[])}
            for region in detected:
                override=overrides.get(region['section'])
                if override and override['tag']!=region['tag']:raise ValueError('Textabschnitt für Tonlage wurde verändert.')
                level=override['level'] if override else pitch_settings.get(section_kind(region['tag']),'auto')
                if level!='auto':section_regions.append({**region,'level':level})
            if not section_regions:raise ValueError('Kein steuerbarer Abschnitt wurde zuverlässig zugeordnet. Bitte Lyrics und Auswahl prüfen.')
        (RUN/'chorus-alignment.json').write_text(json.dumps(alignment,ensure_ascii=False,indent=2),encoding='utf-8')

    vocals, sr = sf.read(cache / "vocals.wav", always_2d=True)
    backing, br = sf.read(cache / "instrumental.wav", always_2d=True)
    locked_backing = bool(spec.get('backing_override'))
    if locked_backing:
        saved_backing = Path(spec['backing_override']).resolve()
        if not saved_backing.is_relative_to(ROOT):
            raise ValueError('Instrumentaldatei liegt außerhalb des Projekts.')
        protected[str(saved_backing)] = sha(saved_backing)
        arguments = [RVC/'ffmpeg.exe', '-nostdin', '-y', '-hide_banner', '-loglevel', 'error']
        if req['preview']:
            arguments += ['-ss', str(req['preview_start'])]
        arguments += ['-i', saved_backing]
        if req['preview']:
            arguments += ['-t', str(req['preview_seconds'])]
        command(arguments + ['-ac', '2', '-ar', '44100', '-c:a', 'pcm_f32le', RUN/'backing-input.wav'])
        backing, br = sf.read(RUN/'backing-input.wav', always_2d=True)
    if sr != 44100 or br != sr or len(vocals) != len(backing) or abs(len(vocals)/sr-info.duration) > .05:
        raise ValueError("Gesangstrennung hat abweichende Länge oder Abtastrate.")
    mono = vocals.mean(axis=1)
    if not np.isfinite(vocals).all() or not np.isfinite(backing).all() or np.sqrt(np.mean(mono**2)) < 1e-5:
        raise ValueError("Keine nutzbare Gesangsspur gefunden.")
    sf.write(RUN / "vocals-input.wav", mono, sr, subtype="FLOAT")
    trial = RUN / "voice.pth"
    if not trial.exists():
        try:
            os.link(model, trial)
        except OSError:
            shutil.copyfile(model, trial)
    profile = {"schema_version":1, "enabled":req["enabled"], "name":spec["profile"]["name"],
               "min_note":req["min_note"], "max_note":req["max_note"], "mode":"melody_phrases",
               "boundary_margin_semitones":1., "preserve_unvoiced":True, "raise_low_phrases":False,
               "stable_register":req.get("stable_register", True)}
    center = training_register_center(req['profile_id']) if section_control else None
    if center is not None:
        profile['register_center_midi'] = center
    trial.with_suffix(".voice.json").write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
    # Reference pitch is diagnostic only: the previous test showed false octave corrections.
    warnings = []
    if automatic:
        warnings.append(alignment['warning'])
        if alignment['rejected']:warnings.append(f"{len(alignment['rejected'])} Refrainabschnitt(e) wurden wegen unsicherer Textzuordnung ausgelassen.")
    if section_control:
        warnings.append('Abschnittstonlagen und automatisch zugeordnete Zeiten bitte anhören.')
        if section_rejected:warnings.append(f'{len(section_rejected)} Textabschnitt(e) konnten nicht sicher zugeordnet werden; dort bleibt die bisherige Tonhöhensteuerung aktiv.')
    reference_disagreements = 0
    reference_times = []
    conversion_start = time.perf_counter()
    section_plan=[]
    if section_control:
        progress('Tonlagen der vollständigen Textabschnitte prüfen')
        if not valid_stems(full_cache):
            progress('Gesang trennen · vollständiger Song für Abschnittstonlagen')
            full_run=RUN/'chorus-source';full_run.mkdir(exist_ok=True)
            command([RVC/'ffmpeg.exe','-nostdin','-y','-hide_banner','-loglevel','error','-i',source,'-ar','44100','-ac','2','-c:a','pcm_f32le',full_run/'input.wav'])
            start=time.perf_counter()
            separate_to_cache(full_cache,full_run,{**spec,'run':str(full_run),'request':{**req,'preview':False}})
            times['separation']+=time.perf_counter()-start
        pitch_cache=full_cache/'section-f0-rmvpe-v1.npy';pitch_marker=pitch_cache.with_suffix('.json')
        fingerprint={'vocals':sha(full_cache/'vocals.wav'),'model':sha(RVC/'assets/rmvpe/rmvpe.pt')}
        saved=json.loads(pitch_marker.read_text()) if pitch_marker.is_file() else {}
        if pitch_cache.is_file() and all(saved.get(k)==v for k,v in fingerprint.items()) and saved.get('sha256')==sha(pitch_cache):
            full_pitch=np.load(pitch_cache)
        else:
            from infer.rmvpe import RMVPE
            full_vocals,full_sr=sf.read(full_cache/'vocals.wav',always_2d=True)
            full_mono=resample_poly(full_vocals.mean(axis=1),160,441).astype(np.float32)
            tracker=RMVPE(str(RVC/'assets/rmvpe/rmvpe.pt'),is_half=True,device='cuda:0')
            full_pitch=tracker.infer_from_audio(full_mono,thred=.03)
            np.save(pitch_cache,full_pitch)
            pitch_marker.write_text(json.dumps({**fingerprint,'sha256':sha(pitch_cache)}),encoding='utf-8')
            from tools.cuda_graph import clear_cuda_graph_cache
            clear_cuda_graph_cache(tracker.model);clear_cuda_graph_cache(tracker.mel_extractor)
            del tracker,full_vocals,full_mono;gc.collect();torch.cuda.empty_cache()
        from infer.voice_range import apply_section_registers
        _,section_plan,_=apply_section_registers(full_pitch,full_pitch,profile,section_regions)
        require_section_plan(pitch_settings, spec['lyrics'], section_plan)
        shifts={r['section']:r['octave_shift'] for r in section_plan}
        section_regions=[{**r,'octave_shift':shifts[r['section']]} for r in section_regions if r['section'] in shifts]
        if not section_regions:raise ValueError('In den zugeordneten Abschnitten wurde kein verwertbarer Gesang gefunden.')
    if req["quality"] == "best":
        progress("Tonhöhen auffälliger Passagen prüfen")
        import parselmouth
        from infer.rmvpe import RMVPE
        reference = parselmouth.Sound(mono, sr).to_pitch_ac(time_step=.01, pitch_floor=65, pitch_ceiling=800)
        tracker = RMVPE(str(RVC / "assets/rmvpe/rmvpe.pt"), is_half=True, device="cuda:0")
        pitched = tracker.infer_from_audio(resample_poly(mono, 160, 441).astype(np.float32), thred=.03)
        t = np.arange(len(pitched))*.01
        idx = np.clip(np.rint((t-reference.xs()[0])/.01).astype(int), 0, len(reference.selected_array)-1)
        ref = reference.selected_array["frequency"][idx]
        confidence = reference.selected_array["strength"][idx]
        valid = (pitched>0)&(ref>0)&(confidence>=.85)
        delta = np.zeros(len(pitched)); delta[valid] = np.abs(12*np.log2(pitched[valid]/ref[valid]))
        flagged = valid & (delta>=11)&(delta<=25)
        reference_disagreements = int(flagged.sum())
        reference_times = t[flagged].tolist()
        if reference_disagreements:
            warnings.append("Zusätzliche Tonhöhenmessungen widersprechen sich an einigen Stellen; bitte abhören. Die gewählte Tonhöhensteuerung bleibt aktiv; aus dieser Vergleichsmessung wird keine zusätzliche Oktavkorrektur abgeleitet.")
        np.savez(RUN / "pitch-diagnostics.npz", times=t, rmvpe=pitched, reference=ref, confidence=confidence, flagged=flagged)
        from tools.cuda_graph import clear_cuda_graph_cache
        clear_cuda_graph_cache(tracker.model)
        clear_cuda_graph_cache(tracker.mel_extractor)
        del tracker
        gc.collect(); torch.cuda.empty_cache()

    progress("Stimme umwandeln")
    start = time.perf_counter()
    from infer.cli import create_config
    from infer.vc.modules import VC
    config = create_config()
    config.weight_root = str(RUN)
    os.environ["weight_root"] = str(RUN)
    vc = VC(config)
    vc.get_vc(trial.name)
    if section_control:
        vc.pipeline.section_registers=section_regions
        vc.pipeline.section_source_offset=req['preview_start'] if req['preview'] else 0
    status, result = vc.vc_single(0, str(RUN / "vocals-input.wav"), req.get("lead_octave", 0), "rmvpe", str(index), .5, 0, 1., .33)
    if not result or result[0] is None:
        raise ValueError(status)
    rate, audio = result
    sf.write(RUN / "converted-raw.wav", audio, rate, subtype="PCM_16")
    audio, _ = sf.read(RUN / "converted-raw.wav")
    converted = resample_poly(audio, 44100 // np.gcd(rate, 44100), rate // np.gcd(rate, 44100))
    range_stats = vc.pipeline.last_range_stats
    section_stats=getattr(vc.pipeline,'last_section_register_stats',None)
    if section_control:
        # The local preview tracker must also honour the validated full-song plan.
        if pitch_settings.get('strict',True) and any(r.get('range_limited') or r.get('range_conflict') for r in section_stats or []):
            raise ValueError('Tonlage im tatsächlichen Gesangsausschnitt weicht vom geprüften Plan ab. Keine ersatzweise tiefere Fassung exportiert.')
    if section_stats and any(r.get('range_conflict') for r in section_stats):
        warnings.append('Einige Abschnitte passen in keiner Oktave vollständig in den Stimmumfang; die Wunschlage wurde zugunsten der Melodie und Obergrenze eingeschränkt.')
    elif section_stats and any(r.get('range_limited') for r in section_stats):
        warnings.append('Die gewünschte Abschnittstonlage wurde an den Stimmumfang angepasst; tief/mittel/hoch können dadurch dieselbe Oktavlage ergeben.')
    lead_f0 = vc.pipeline.last_synthesis_f0.copy()
    np.save(RUN / "lead-pitch.npy", lead_f0)
    if section_control:np.save(RUN/'section-source-pitch.npy',vc.pipeline.last_section_source_f0)
    recovery = None
    if req['quality']=='best':
        if abs(len(mono)-len(converted))>sr//4:raise ValueError('Stimmumwandlung hat eine abweichende Länge.')
        converted=np.pad(converted[:len(mono)],(0,max(0,len(mono)-len(converted))))
        from voice_recovery import recover_dropouts
        # Retry only measured local collapses. Keep the full-song contour and
        # diagnostics for harmony/range processing after each short VC call.
        saved_state={name:getattr(vc.pipeline,name,None) for name in
            ('last_p_len','last_synthesis_f0','last_range_stats','last_section_register_stats','last_section_source_f0')}
        original_forced=getattr(vc.pipeline,'forced_f0',None)
        def retry(source_path,contour):
            # Full-song graph buffers can exhaust VRAM when adding a new short
            # shape. Release cached calls while keeping the loaded models.
            from tools.cuda_graph import clear_cuda_graph_cache
            if vc.hubert_model is not None:clear_cuda_graph_cache(vc.hubert_model)
            clear_cuda_graph_cache(vc.net_g)
            gc.collect();torch.cuda.empty_cache()
            vc.pipeline.forced_f0=contour
            status,retry_result=vc.vc_single(0,str(source_path),0,'rmvpe',str(index),.5,0,1.,.33)
            if not retry_result or retry_result[0] is None:raise ValueError(status)
            return *retry_result,vc.pipeline.last_synthesis_f0.copy()
        try:
            converted,recovery=recover_dropouts(mono,converted,sr,lead_f0,config.x_pad,RUN,retry,progress)
            if recovery['accepted_count']:
                sf.write(RUN/'converted-repaired.wav',converted,sr,subtype='FLOAT')
                warnings.append(f"{recovery['accepted_count']} Gesangsabschnitt(e) nach Pegelverlust mit unveränderter Tonlage neu umgewandelt; bitte anhören.")
            if any(not r['accepted'] for r in recovery['attempts']):
                warnings.append('Ein Gesangseinbruch ließ sich im kurzen Abschnitt nicht ausreichend verbessern; bitte anhören.')
        except Exception as error:
            recovery={'version':'short-context-recovery-v1','accepted_count':0,'error':str(error)}
            warnings.append('Zusätzliche Abschnittsumwandlung fehlgeschlagen; bisherige Umwandlung beibehalten.')
        finally:
            vc.pipeline.forced_f0=original_forced
            for name,value in saved_state.items():setattr(vc.pipeline,name,value)
            if recovery and recovery.get('attempts'):
                from tools.cuda_graph import clear_cuda_graph_cache
                if vc.hubert_model is not None:clear_cuda_graph_cache(vc.hubert_model)
                clear_cuda_graph_cache(vc.net_g)
                gc.collect();torch.cuda.empty_cache()
    harmony_audio = np.zeros(len(backing))
    suppressed = []
    if harmony_settings.get("enabled"):
        from infer.voice_range import note_midi
        progress("Stimme umwandeln · zweite Refrainstimme")
        offset = req["preview_start"] if req["preview"] else 0
        contour, suppressed = harmony_contour(lead_f0[:vc.pipeline.last_p_len], harmony_settings["interval"],
            harmony_settings["regions"], offset, config.x_pad,
            note_midi(req["min_note"]) if req["enabled"] else None,
            note_midi(req["max_note"]) if req["enabled"] else None)
        if contour.any():
            vc.pipeline.forced_f0 = contour
            try:
                status, harmony_result = vc.vc_single(0, str(RUN / "vocals-input.wav"), 0, "rmvpe", str(index), .5, 0, 1., .33)
            finally:
                vc.pipeline.forced_f0 = None
            if not harmony_result or harmony_result[0] is None:
                raise ValueError(status)
            np.save(RUN / "harmony-pitch.npy", vc.pipeline.last_synthesis_f0)
            harmony_rate, harmony_raw = harmony_result
            sf.write(RUN / "harmony-raw.wav", harmony_raw, harmony_rate, subtype="PCM_16")
            harmony_raw, _ = sf.read(RUN / "harmony-raw.wav")
            harmony_audio = resample_poly(harmony_raw, 44100//np.gcd(harmony_rate, 44100), harmony_rate//np.gcd(harmony_rate, 44100))
            if abs(len(harmony_audio)-len(backing))>sr//4:
                raise ValueError("Zweite Stimme hat eine abweichende Länge.")
            harmony_audio = np.pad(harmony_audio[:len(backing)], (0, max(0, len(backing)-len(harmony_audio))))
            envelope = harmony_envelope(len(backing), sr, harmony_settings["regions"], suppressed, offset)
            # Loudness follows the lead on the same active regions; do not
            # compensate silence or omission by excessively boosting the layer.
            active = envelope > .5
            if active.any():
                reference = converted[:len(backing)]
                measured = min(len(reference), len(active))
                valid = active[:measured]
                layer_gain = min(2., np.sqrt(np.mean(reference[:measured][valid]**2))/max(1e-9, np.sqrt(np.mean(harmony_audio[:measured][valid]**2))))
                harmony_audio *= layer_gain
            harmony_audio *= envelope * np.power(10., harmony_settings["gain_db"]/20)
        else:
            warnings.append("Im gewählten Ausschnitt ist keine zweite Stimme innerhalb der markierten Refrains und des Stimmumfangs möglich.")
        if suppressed:
            warnings.append("Die zweite Stimme wurde bei zu hohen oder tiefen Gesangsphrasen ausgelassen, damit der feste Tonabstand und der Stimmumfang erhalten bleiben.")
    times["conversion"] = time.perf_counter()-conversion_start
    progress("Song zusammenfügen und Export prüfen")
    start = time.perf_counter()
    difference = len(backing)-len(converted)
    if abs(difference)>sr//4:
        raise ValueError("Stimmumwandlung hat eine abweichende Länge.")
    converted = np.pad(converted[:len(backing)], (0,max(0,difference)))
    gain = min(2., np.sqrt(np.mean(mono**2))/max(1e-9,np.sqrt(np.mean(converted**2))))
    converted *= gain; harmony_audio *= gain
    lead = converted.copy()
    level_report = None
    level_settings = req.get('mix_levels', {})
    if any(level_settings.get(k, False) for k in ('vocals','backing','vocal_db','backing_db')):
        from app.level_dsp import stabilize_layers
        lead, harmony_audio, backing, level_report = stabilize_layers(lead,harmony_audio,backing,sr,level_settings,reference=mono)
        converted = lead.copy()
        if locked_backing and (level_settings.get('backing') or level_settings.get('backing_db')):
            warnings.append('Instrumentalgrundlage durch die gewählte Pegelkorrektur angepasst.')
    converted += harmony_audio
    vocal_mix_gain = 1.
    preserve_backing = locked_backing and not (level_settings.get('backing') or level_settings.get('backing_db'))
    if preserve_backing:
        from app.audio_mix import fixed_backing_gain
        vocal_mix_gain = fixed_backing_gain(backing, converted)
        converted *= vocal_mix_gain; lead *= vocal_mix_gain; harmony_audio *= vocal_mix_gain
        if vocal_mix_gain < .99:
            warnings.append('Gesangspegel zum Schutz vor Übersteuerung reduziert; Instrumentalbegleitung unverändert.')
    mix = backing+converted[:,None]
    common = 1. if preserve_backing else min(1., .95/max(1e-9,float(np.max(np.abs(mix))),float(np.max(np.abs(converted)))))
    mix *= common; converted *= common; lead *= common; harmony_audio *= common
    if level_report is not None:
        level_report.update(common_gain=common,vocal_headroom_gain=vocal_mix_gain)
        if common < .8 or vocal_mix_gain < .8:
            warnings.append('Wenig Pegelreserve: gewünschte Lautstärke durch Übersteuerungsschutz begrenzt.')
    # Keep unfaded material for insertion into a full version. Playback previews
    # have short edge fades, but those must not create holes in a repaired song.
    if req.get("base_song_id"):
        sf.write(RUN / "patch-mix.wav", mix, sr, subtype="PCM_24")
        sf.write(RUN / "patch-vocals.wav", converted, sr, subtype="PCM_24")
    if req["preview"]:
        fade = np.ones(len(converted)); edge=min(int(.02*sr),len(fade)//2)
        fade[:edge]=np.linspace(0,1,edge); fade[-edge:]=np.linspace(1,0,edge)
        converted *= fade; mix *= fade[:,None]; lead *= fade; harmony_audio *= fade
    if not np.isfinite(mix).all():
        raise ValueError("Ungültige Audiowerte im Export.")
    sf.write(RUN / "mix.wav", mix, sr, subtype="PCM_24")
    sf.write(RUN / "vocals.wav", converted, sr, subtype="PCM_24")
    sf.write(RUN / "lead.wav", lead, sr, subtype="PCM_24")
    if harmony_settings.get("enabled"):
        sf.write(RUN / "harmony.wav", harmony_audio, sr, subtype="PCM_24")
    command([RVC / "ffmpeg.exe", "-nostdin", "-y", "-hide_banner", "-loglevel", "error", "-i", RUN / "mix.wav", "-af", "volume=-1.5dB", "-codec:a", "libmp3lame", "-b:a", "320k", RUN / "mix.mp3"])
    check, cs = sf.read(RUN / "mix.wav", always_2d=True)
    if cs != sr or len(check)!=len(backing) or not np.isfinite(check).all() or np.max(np.abs(check))> .951:
        raise ValueError("Exportprüfung fehlgeschlagen.")
    for name, h in protected.items():
        if sha(name) != h:
            raise ValueError("Original oder Stimmmodell wurde verändert.")
    times["mix"] = time.perf_counter()-start
    conflicts = (range_stats or {}).get("phrases_exceeding_range", [])
    if not section_control and req.get("lead_octave") == 12 and any(int(k)<0 and v for k,v in (range_stats or {}).get("shift_octaves_counts", {}).items()):
        warnings.append("Die gewünschte höhere Oktave wurde bei einigen Phrasen durch den eingestellten Stimmumfang begrenzt.")
    if conflicts:
        warnings.append("Einige Melodien passen nicht vollständig in den Stimmumfang; bitte abhören.")
    result = {"voice_profile":spec["profile"]["name"], "profile_id":req["profile_id"], "quality":req["quality"],
              "backing_locked":preserve_backing, "backing_song_id":spec.get('backing_song_id'), "vocal_mix_gain":vocal_mix_gain,
              "mix_levels":level_report,
              "voice_recovery":recovery,
              "separation_settings":{"chunk_size":352800, "overlap_size":308700 if req["quality"]=="best" else 264600,"tta_passes":3 if req["quality"]=="best" else 1},
              "preview":req["preview"], "preview_start":req["preview_start"] if req["preview"] else 0,
              "duration":len(mix)/sr, "source_seconds":info.duration, "source_hash":source_hash,
              "cached_stems":cached, "stage_seconds":times, "elapsed_seconds":time.perf_counter()-clock,
              "lead_octave":req.get("lead_octave", 0), "stable_register":req.get("stable_register", True),
              "harmony":{**harmony_settings, "suppressed_phrases":suppressed},
              "chorus_alignment":{k:alignment[k] for k in ('version','regions','rejected','lyrics_sha256')} if alignment else None,
              "section_pitch":{**pitch_settings,'regions':section_regions,'rejected':section_rejected,'plan':section_plan,'diagnostics':section_stats or []},
              "range":profile, "range_diagnostics":range_stats, "reference_disagreements":reference_disagreements,
              "range_padding_seconds":config.x_pad,
              "review_regions":listening_regions(range_stats, len(mix)/sr, config.x_pad, reference_times, req["preview_start"] if req["preview"] else 0),
              "warnings":warnings, "protected_unchanged":True, "sha256":sha(RUN / "mix.wav"),
              "recipe":spec["recipe"], "model_sha256":protected[str(model)]}
    (RUN / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    progress("Fertig")


try:
    main()
except Exception as error:
    (RUN / "error.json").write_text(json.dumps({"error":str(error) or type(error).__name__}, ensure_ascii=False), encoding="utf-8")
    raise
