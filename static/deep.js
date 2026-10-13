Object.assign(I18N.de,{
  deep_title:'Originalsong bearbeiten',deep_intro:'Hier wird die Originalaufnahme als musikalische Vorlage verwendet. Jede Bearbeitung wird als zusätzliche Fassung gespeichert.',
  deep_simple_hint:'Neue Songs aus Idee, Stil und Text erzeugen.',deep_mode_hint:'Originalaufnahme, Text und Akkorde gemeinsam bearbeiten.',
  deep_source:'Originalaufnahme aus der Bibliothek',deep_import:'Originalaufnahme importieren',deep_refresh:'Auswahl aktualisieren',
  deep_model_default:name=>`Voreinstellung verwenden: ${name}`,deep_model_hint:'Die Auswahl gilt für diesen Auftrag. Die allgemeine Voreinstellung bleibt erhalten.',
  deep_model_active:name=>`Für diesen Auftrag: ${name}`,deep_model_loading:'Klangmodelle werden geprüft …',deep_model_missing:'XL fehlt. Bitte zuerst über den Installer herunterladen oder Standard wählen.',
  deep_summary:(model,length,preview)=>`${preview?'Vorschau':'Vollfassung'} · ${model} · ${length}`,
  deep_action:'Was möchtest Du verändern?',deep_close:'Originalnah neu arrangieren',deep_free:'Freier neu arrangieren',deep_voice_only:'Nur die Stimme austauschen',
  deep_version_title:'Titel der neuen Fassung',deep_changes:'Gewünschte Instrumentierung und Änderungen',deep_lyrics:'Songtext · Abschnittsmarkierungen beibehalten',
  deep_separate:'Text und Akkorde trennen',deep_chords:'Akkorde und Zuordnung zu Abschnitten / Takten',
  deep_chord_hint:'Akkorde werden als Vorgaben für die Begleitung übergeben. Eine taktgenaue Umsetzung wird dadurch nicht garantiert. Für genaue Akkordtreue dient die Originalaufnahme als wichtigste Vorlage.',
  deep_strength:'Nähe zur Originalaufnahme',deep_strength_hint:'Höhere Werte lassen weniger Veränderung zu. Dies ist eine Gewichtung der Vorlage, kein gemessener Ähnlichkeitswert. Melodie, Aufbau und Klang können sich bei einer KI-Neufassung verändern.',
  deep_key:'Tonart',deep_meter:'Taktmaß',deep_metadata_hint:'Tempo und Tonart werden aus vorhandenen Songdaten übernommen, soweit sie bekannt sind. Du kannst sie korrigieren; 0 BPM bedeutet keine zusätzliche Tempoangabe.',
  deep_instrumental:'Neue Fassung ohne Gesang',deep_preview:'Zuerst eine Vorschau erstellen',deep_start:'Vorschau ab Sekunde',deep_seconds:'Länge · 5–30 Sekunden',
  deep_final_voice:'Vollfassung anschließend mit Stimmprofil erstellen',deep_submit:'Vorschau erstellen',deep_full_submit:'Neue Vollfassung erstellen',
  deep_from_preview:'Ganzen Song erstellen',deep_from_preview_hint:'Vollfassung aus der ursprünglichen Vorlage mit den gespeicherten Einstellungen dieser Vorschau erstellen. Die Vorschau bleibt erhalten.',
  deep_voice_submit:'Stimme auswählen und bearbeiten',deep_voice_hint:'Die Begleitung der Vorlage wird beibehalten. Im nächsten Fenster wählst Du das Stimmprofil, den Stimmumfang und gegebenenfalls Harmonien.',
  deep_close_hint:'Die Aufnahme dient direkt als musikalische Vorlage. Ein kurzer Vergleich hilft, die passende Nähe zum Original zu finden.',
  deep_free_hint:'Die Aufnahme bleibt die Ausgangsbasis, das Modell darf die musikalischen Details stärker neu interpretieren.',
  deep_empty:'Bitte zuerst eine Originalaufnahme importieren.',deep_wait:'Auftrag wird vorbereitet …',deep_queued:'Die zusätzliche Fassung wartet in der gemeinsamen Warteschlange.',
  deep_chords_found:n=>`${n} Akkordzeilen erkannt und vom Gesangstext getrennt. Bitte die Zuordnung prüfen.`,deep_chords_none:'Keine eindeutig erkennbaren Akkordzeilen gefunden. Du kannst Akkorde separat eintragen.',
  deep_result:'Originalbearbeitung',deep_result_preview:'Originalbearbeitung · Vorschau',deep_profile_original:'Stimme der neuen Fassung behalten',deep_compare_return:'Zur neuen Fassung wechseln'
});
Object.assign(I18N.en,{
  deep_title:'Edit an original song',deep_intro:'The original recording is used as the musical template. Each edit is saved as an additional version.',
  deep_simple_hint:'Generate new songs from an idea, style and lyrics.',deep_mode_hint:'Work with the original recording, lyrics and chords together.',
  deep_source:'Original recording from the library',deep_import:'Import original recording',deep_refresh:'Refresh selection',
  deep_model_default:name=>`Use default: ${name}`,deep_model_hint:'This choice applies to this request. The general default is retained.',
  deep_model_active:name=>`For this request: ${name}`,deep_model_loading:'Checking sound models …',deep_model_missing:'XL is missing. Download it using the installer first or choose Standard.',
  deep_summary:(model,length,preview)=>`${preview?'Preview':'Full version'} · ${model} · ${length}`,
  deep_action:'What would you like to change?',deep_close:'Arrange close to the original',deep_free:'Arrange more freely',deep_voice_only:'Replace the voice only',
  deep_version_title:'New version title',deep_changes:'Desired instrumentation and changes',deep_lyrics:'Lyrics · retain section markers',
  deep_separate:'Separate lyrics and chords',deep_chords:'Chords and section / bar assignment',
  deep_chord_hint:'Chords are submitted as guidance for the accompaniment. This does not guarantee exact bar-by-bar adherence. The recording is the main template for chord fidelity.',
  deep_strength:'Closeness to the original recording',deep_strength_hint:'Higher values allow less change. This weights the source; it is not a measured similarity score. Melody, structure and sound can change in an AI-generated version.',
  deep_key:'Key',deep_meter:'Time signature',deep_metadata_hint:'Tempo and key are copied from existing song metadata when available. You can correct them; 0 BPM means no additional tempo instruction.',
  deep_instrumental:'New version without vocals',deep_preview:'Create a preview first',deep_start:'Preview starts at second',deep_seconds:'Length · 5–30 seconds',
  deep_final_voice:'Create an additional voice profile version after the full arrangement',deep_submit:'Create preview',deep_full_submit:'Create new full version',
  deep_from_preview:'Create full song',deep_from_preview_hint:'Create a full version from the original source using the saved settings of this preview. The preview is retained.',
  deep_voice_submit:'Choose and edit voice',deep_voice_hint:'The template backing is retained. The next dialog lets you choose the voice profile, singing range and optional harmonies.',
  deep_close_hint:'The recording is used directly as a musical template. A short comparison helps find the right source weighting.',
  deep_free_hint:'The recording remains the starting point while the model can reinterpret musical details more freely.',
  deep_empty:'Import an original recording first.',deep_wait:'Preparing the request …',deep_queued:'The additional version is waiting in the shared queue.',
  deep_chords_found:n=>`${n} chord rows detected and separated from the lyrics. Please check their assignment.`,deep_chords_none:'No unambiguous chord rows found. You can enter chords separately.',
  deep_result:'Original edit',deep_result_preview:'Original edit · preview',deep_profile_original:'Keep the new arrangement voice',deep_compare_return:'Switch to new version'
});

let deepSongs=[],deepProfiles=[],deepActive=false,deepModelSettings=null,deepSubmitting=false;
function selectedDeepModel(){
  const choice=$('#deepSoundModel').value;
  return choice==='default'?(deepModelSettings?.dit||null):choice;
}
function deepModelLabel(model){return model==='xl'?t('dit_xl'):t('dit_standard');}
function deepSourceLabel(song){
  const title=song.title||song.caption.split(',').slice(0,3).join(',').slice(0,90);
  const kind=song.params.job_type==='voice'?(song.result_meta?.voice_profile||t('voice_version')):
    song.params.job_type==='instrumental'?t('instrumental_version'):song.params.job_type==='deep'?t('deep_result'):t('voice_role_original');
  return `${title}${song.letter?' '+song.letter:''} · ${kind} · ${fmt(song.result_meta?.duration||song.params.duration||0)}`;
}
function syncDeepControls(){
  const voice=$('#deepAction').value==='voice',preview=$('#deepPreview').checked;
  $('#deepRemixOptions').hidden=voice;$('#deepPreviewFields').hidden=!preview;
  $('#deepRemixOptions').querySelectorAll('input,select,textarea,button').forEach(el=>{el.disabled=voice;});
  $('#deepStart').disabled=voice||!preview;$('#deepSeconds').disabled=voice||!preview;
  $('#deepVoiceField').hidden=preview||$('#deepInstrumental').checked;
  $('#deepLyrics').disabled=voice||$('#deepInstrumental').checked;
  $('#deepActionHint').textContent=t(voice?'deep_voice_hint':$('#deepAction').value==='cover'?'deep_free_hint':'deep_close_hint');
  $('#deepSubmit').textContent=t(voice?'deep_voice_submit':preview?'deep_submit':'deep_full_submit');
  $('#deepStrengthValue').textContent=(Number($('#deepStrength').value)/100).toFixed(2);
  const model=selectedDeepModel(),missing=model==='xl'&&!deepModelSettings?.dit_xl_available;
  $('#deepSoundModel').querySelector('option[value="default"]').textContent=deepModelSettings?t('deep_model_default',deepModelLabel(deepModelSettings.dit)):t('deep_model_loading');
  $('#deepSoundModel').querySelector('option[value="xl"]').disabled=!deepModelSettings?.dit_xl_available;
  $('#deepSoundModel').disabled=voice||!deepModelSettings;
  $('#deepModelStatus').textContent=!deepModelSettings?t('deep_model_loading'):missing?t('deep_model_missing'):t('deep_model_active',deepModelLabel(model));
  const source=deepSongs.find(s=>s.id===$('#deepSource').value);
  const seconds=preview?Number($('#deepSeconds').value):(source?.result_meta?.duration||source?.params.duration||0);
  $('#deepRequestSummary').textContent=voice||!model||missing||!source?'':t('deep_summary',deepModelLabel(model),fmt(seconds),preview);
  $('#deepSubmit').disabled=deepSubmitting||(!voice&&(!deepModelSettings||missing));
}
function fillDeepSource(){
  const song=deepSongs.find(s=>s.id===$('#deepSource').value);if(!song)return;
  const meta=song.result_meta||{},params=song.params||{};
  $('#deepTitle').value=song.title||'';$('#deepLyrics').value=meta.lyrics||song.lyrics||'';
  $('#deepChords').value=params.chords||'';$('#deepBpm').value=meta.bpm||params.bpm||0;$('#deepKey').value=meta.keyscale||params.keyscale||'';
  $('#deepMeter').value=String(meta.timesignature||params.timesignature||'4');
  if(!$('#deepMeter').value)$('#deepMeter').value='4';
  $('#deepSourceInfo').textContent=deepSourceLabel(song);
  $('#deepInstrumental').checked=$('#deepLyrics').value==='[Instrumental]';syncDeepControls();
}
async function loadDeepData(wanted){
  const [data,voices,settings]=await Promise.all([api('/api/songs'),api('/api/voices'),api('/api/settings')]);
  deepModelSettings=settings;
  deepSongs=data.filter(s=>s.status==='done'&&!s.params.voice?.preview&&!s.params.deep?.preview);
  deepProfiles=voices.profiles;
  const previous=$('#deepSource').value,selected=wanted||previous;
  $('#deepSource').innerHTML=deepSongs.map(s=>`<option value="${esc(s.id)}">${esc(deepSourceLabel(s))}</option>`).join('');
  if(deepSongs.some(s=>s.id===selected))$('#deepSource').value=selected;
  const voice=$('#deepVoice').value;
  $('#deepVoice').innerHTML=`<option value="">${t('deep_profile_original')}</option>`+deepProfiles.map(p=>`<option value="${esc(p.id)}">${esc(p.name)}</option>`).join('');
  if(deepProfiles.some(p=>p.id===voice))$('#deepVoice').value=voice;
  if(wanted||previous!==$('#deepSource').value)fillDeepSource();
  syncDeepControls();
  if(!deepSongs.length)$('#deepStatus').textContent=t('deep_empty');
}
async function setDeepMode(enabled){
  deepActive=enabled;$('#deepPanel').hidden=!enabled;$('#simplePanel').hidden=enabled;
  document.body.classList.toggle('deep-mode',enabled);
  $('#modeName').textContent=enabled?'Deep Mode':'Simple Mode';$('#modeSwitch').textContent=enabled?'Simple Mode':'Deep Mode';
  $('#modeSwitch').setAttribute('aria-pressed',String(enabled));
  $('#modeDescription').textContent=t(enabled?'deep_mode_hint':'deep_simple_hint');
  try{localStorage.setItem('music_generator_mode',enabled?'deep':'simple');}catch{}
  if(enabled){try{await loadDeepData();}catch(e){$('#deepStatus').textContent=e.message;}}
}
window.openDeepSong=async song=>{await setDeepMode(true);await loadDeepData(song.id);$('#deepPanel').scrollIntoView({block:'start',behavior:'smooth'});};
const pendingDeepFull=new Set();
window.deepFullPending=id=>pendingDeepFull.has(id);
window.createDeepFullSong=async song=>{
  const saved=song.params?.deep;
  if(song.status!=='done'||!saved?.preview||!saved.source_song_id||pendingDeepFull.has(song.id))return;
  pendingDeepFull.add(song.id);render();
  try{
    // Use the complete original, never the short preview or the current form.
    const body={...saved,preview:false,preview_start:0};
    await api('/api/deep/generate',{method:'POST',body:JSON.stringify(body)});
    $('#deepStatus').textContent=t('deep_queued');
    await refresh();
  }catch(e){alert(e.message);}
  finally{pendingDeepFull.delete(song.id);render();}
};
$('#modeSwitch').addEventListener('click',()=>setDeepMode(!deepActive));
$('#deepSource').addEventListener('change',fillDeepSource);
$('#deepRefresh').addEventListener('click',()=>loadDeepData().catch(e=>{$('#deepStatus').textContent=e.message;}));
$('#deepImport').addEventListener('click',()=>$('#deepImportFile').click());
$('#deepImportFile').addEventListener('change',async()=>{
  const file=$('#deepImportFile').files[0];if(!file)return;
  $('#deepImport').disabled=true;$('#deepStatus').textContent=t('deep_wait');
  try{const body=new FormData();body.append('audio',file);const song=await api('/api/library/import',{method:'POST',body});
    await loadDeepData(song.id);$('#deepStatus').textContent='';refresh();
  }catch(e){$('#deepStatus').textContent=e.message;}finally{$('#deepImport').disabled=false;$('#deepImportFile').value='';}
});
$('#deepAction').addEventListener('change',()=>{$('#deepStrength').value=$('#deepAction').value==='cover'?15:80;syncDeepControls();});
$('#deepForm').addEventListener('change',syncDeepControls);
$('#deepSeconds').addEventListener('input',syncDeepControls);
$('#deepStrength').addEventListener('input',syncDeepControls);
$('#deepSeparate').addEventListener('click',async()=>{
  try{const result=await api('/api/deep/separate-chords',{method:'POST',body:JSON.stringify({text:$('#deepLyrics').value})});
    $('#deepLyrics').value=result.lyrics;if(result.chords)$('#deepChords').value=[$('#deepChords').value,result.chords].filter(Boolean).join('\n');
    $('#deepStatus').textContent=result.rows.length?t('deep_chords_found',result.rows.length):t('deep_chords_none');
  }catch(e){$('#deepStatus').textContent=e.message;}
});
$('#deepForm').addEventListener('submit',async e=>{
  e.preventDefault();const source=deepSongs.find(s=>s.id===$('#deepSource').value);if(!source)return;
  if($('#deepAction').value==='voice'){
    await window.openVoiceDialog(source);window.setMixLevels('voice',window.mixLevelRequest('deep'));return;
  }
  const button=$('#deepSubmit');if(button.disabled)return;deepSubmitting=true;syncDeepControls();$('#deepStatus').textContent=t('deep_wait');
  try{
    const profile=deepProfiles.find(p=>p.id===$('#deepVoice').value);
    const body={source_song_id:source.id,mode:$('#deepAction').value,title:$('#deepTitle').value,caption:$('#deepCaption').value,
      lyrics:$('#deepLyrics').value,chords:$('#deepChords').value,instrumental:$('#deepInstrumental').checked,
      source_strength:Number($('#deepStrength').value)/100,bpm:Number($('#deepBpm').value),keyscale:$('#deepKey').value,timesignature:$('#deepMeter').value,
      preview:$('#deepPreview').checked,preview_start:$('#deepPreview').checked?Number($('#deepStart').value):0,preview_seconds:$('#deepPreview').checked?Number($('#deepSeconds').value):20,
      mix_levels:window.mixLevelRequest('deep'),sound_model:selectedDeepModel(),
      voice_after:profile&&!$('#deepPreview').checked&&!$('#deepInstrumental').checked?{profile_id:profile.id,enabled:profile.enabled,min_note:profile.min_note,max_note:profile.max_note}:null};
    await api('/api/deep/generate',{method:'POST',body:JSON.stringify(body)});$('#deepStatus').textContent=t('deep_queued');refresh();
  }catch(e){$('#deepStatus').textContent=e.message;}finally{deepSubmitting=false;syncDeepControls();}
});
$('#deepCaption').value='Preserve the original vocal melody, chord movement, rhythm and song structure. Refresh the instrumentation with a warm natural sound.';
document.addEventListener('langchange',()=>{syncDeepControls();$('#modeDescription').textContent=t(deepActive?'deep_mode_hint':'deep_simple_hint');if(deepActive)loadDeepData().catch(()=>{});});
document.addEventListener('settingschange',()=>{if(deepActive)loadDeepData().catch(e=>{$('#deepStatus').textContent=e.message;});});
applyI18n();syncDeepControls();render();
let savedDeepMode=false;try{savedDeepMode=localStorage.getItem('music_generator_mode')==='deep';}catch{}
setDeepMode(savedDeepMode);
