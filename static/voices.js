// Voice conversion uses the original song and the same server queue as generation.
Object.assign(I18N.de, {
  voice_section_strict:"Gewählte Tonlage verbindlich · bei Konflikten anhalten",
  voice_register_anchor:note=>`Referenz für „Mittel“ aus Deinen Aufnahmen: etwa ${note}.`,
  voice_plan_blocked:"Diese Wunschlage ist mit den aktuellen Einstellungen nicht umsetzbar. Es wird keine ersatzweise tiefere Fassung erstellt. Prüfe Stimmumfang und die genannten Abschnitte.",
  voice_play_original:"Original zum Vergleich abspielen", voice_original_short:"Original",
  voice_new:"Mit meiner Stimme singen", voice_new_hint:"Das Original bleibt erhalten. Anschließend entsteht eine zusätzliche Stimmversion.",
  voice_original:"Originalstimme", voice_profile:"Stimmprofil", voice_low:"Tiefster Ton", voice_high:"Höchster Ton",
  voice_range:"Stimmumfang berücksichtigen · natürliche Melodie priorisieren", voice_quality:"Verarbeitung",
  voice_standard:"Standard", voice_best:"Beste Qualität – Zeit zweitrangig", voice_best_short:"Qualitätsmodus",
  voice_convert:"Mit anderer Stimme erstellen", voice_button:"Stimme", voice_version:"Stimmversion", voice_preview_short:"Vorschau",
  voice_import:"Fertigen Song importieren", voice_hint:"Text, Melodie und Begleitung stammen aus dem Original. Die neue Fassung wird zusätzlich gespeichert. Stimmumfangskorrekturen können die Tonlage verändern.",
  voice_save_range:"Als Profilvorgabe speichern", voice_saved:"Profilvorgabe gespeichert.",
  voice_preview:"Zunächst eine Vorschau erstellen", voice_preview_start:"Vorschau ab Sekunde", voice_start:"STIMMVERSION ERSTELLEN",
  voice_estimate_note:"Schätzung ohne Wartezeit. Andere GPU-Aufgaben können die Dauer verändern. Mehr Rechenzeit garantiert kein besseres Ergebnis.",
  voice_best_hint:"Zusätzliche Trennungsdurchläufe und größere Überlappung. Starke lokale Gesangseinbrüche werden in kurzen Abschnitten mit gleicher Tonlage erneut umgewandelt. Deine Abschnittsauswahl gilt weiterhin.",
  voice_standard_hint:"Bewährte Gesangstrennung und Stimmumwandlung; verlustfreier WAV-Export.",
  voice_from_original:"Vom ursprünglichen Song abgeleitet", voice_solo:"Umgewandelte Gesangsspur herunterladen",
  voice_loading:"Laufzeit wird geschätzt …", voice_time:(a,b)=>`Geschätzte Verarbeitung: ${a}–${b}`,
  voice_initial:" · zunächst grobe Schätzung", voice_measured:" · anhand bisheriger Laufzeiten", voice_cached:" · Gesangstrennung vorhanden",
  voice_missing:"Kein einsatzbereites Stimmprofil gefunden.", voice_uploading:"Song wird importiert …", voice_imported:"Song in der Bibliothek gespeichert.",
  voice_generation_time:(a,b)=>`Stimmumwandlung etwa ${a}–${b}, zusätzlich zur Songgenerierung.`,
  voice_needs_vocals:"Für die Stimmumwandlung bitte Gesang aktivieren.",
  voice_role_final:"Endfassung", voice_role_test:"Entwicklungstest", voice_role_original:"Original", voice_role_import:"Importierter Song",
  voice_mark_final:"Als Endfassung markieren",
  voice_review_count:n=>`${n} Prüfstellen zum Anhören`, voice_review_range:"Stimmumfang prüfen", voice_review_pitch:"Tonhöhe prüfen",
  voice_source_time:time=>`Original ${time}`, voice_compare_return:"Zur Stimmversion wechseln", voice_compare_original:"Zum Original wechseln",
  voice_section:"Abschnitt bearbeiten", voice_apply_section:"In Vollfassung übernehmen", voice_preview_length:"Länge des Ausschnitts in Sekunden (5–30)",
  voice_section_preview:"Abschnittsvorschau", voice_section_start:"ABSCHNITTSVORSCHAU ERSTELLEN",
  voice_section_hint:"Bearbeite zunächst einen Ausschnitt. Nach dem Anhören kannst Du ihn in eine neue Vollfassung übernehmen. Die vorhandene Fassung bleibt erhalten.",
  voice_apply_confirm:"Diesen Ausschnitt mit weichen Übergängen in eine neue Vollfassung übernehmen?",
  voice_sections_applied:n=>`${n} Abschnitt${n===1?"":"e"} überarbeitet`,
  voice_octave:"Hauptgesang eine Oktave höher (+12)", voice_octave_hint:"Wunschtonlage vor der Stimmumwandlung. Bei aktivem Stimmumfang werden zu hohe Phrasen wieder abgesenkt; Begleitung und Tempo bleiben gleich.",
  voice_stable:"Tonlage über ganze Gesangszeilen stabil halten",
  voice_harmony:"Zweite Stimme in den Refrains", voice_harmony_interval:"Tonabstand zur Hauptstimme",
  voice_octave_down:"Oktave darunter (−12)", voice_octave_up:"Oktave darüber (+12)",
  voice_fifth_down:"Quinte darunter (−7)", voice_fifth_up:"Quinte darüber (+7)",
  voice_harmony_level:"Lautstärke der zweiten Stimme (dB)", voice_chorus_times:"Refrainbereiche im Originalsong",
  voice_chorus_hint:"Je Zeile Start–Ende, z. B. 00:45–01:10 oder 45–70. Zeiten gelten auch in Vorschauen für den Originalsong.",
  voice_harmony_hint:"Die zweite Stimme folgt der Hauptmelodie im festen Tonabstand. Oktaven passen zur Tonart; Quinten bitte mit den Akkorden abhören. Bei aktivem Stimmumfang werden unpassende Harmoniephrasen ausgelassen.",
  voice_chorus_add:"20 Sekunden ab Abspielposition hinzufügen", voice_chorus_invalid:"Refrainzeiten bitte als Start–Ende pro Zeile angeben (Sekunden oder mm:ss).", voice_chorus_play:"Bitte zuerst den Originalsong oder seine Stimmversion abspielen.",
  voice_harmony_short:"Harmonie", voice_lead_short:"Hauptstimme",
  voice_chorus_mode:"Refrainbereiche festlegen", voice_chorus_auto:"Automatisch aus Lyrics mit [chorus]", voice_chorus_manual:"Zeiten manuell",
  voice_chorus_auto_hint:"[chorus]-Text wird nach der Songgenerierung lokal dem Gesang zugeordnet. Unsichere Abschnitte werden ausgelassen. Die erkannten Zeiten bitte anhören; danach kannst Du sie manuell korrigieren.",
  voice_chorus_found:n=>`${n} Refrainmarkierung${n===1?"":"en"} mit Text vorhanden.`, voice_chorus_none:"Keine [chorus]-Abschnitte mit Text vorhanden. Für diesen Song bitte manuelle Zeiten verwenden.",
  voice_chorus_cached:n=>`${n} Refrainbereich${n===1?"":"e"} bereits automatisch zugeordnet.`,voice_chorus_use:"Erkannte Zeiten zur manuellen Korrektur übernehmen",
  voice_chorus_analysis:"Refrainabgleich wird beim Erstellen durchgeführt; auch Vorschauen benötigen dafür den vollständigen Song.",
  voice_section_pitch:"Oktavkorrektur je Abschnitt",voice_section_pitch_hint:"Wähle die Wunschlage innerhalb Deines Stimmumfangs. Ganze Gesangsphrasen werden in Oktaven versetzt; Melodie und Tonart bleiben erhalten. Breite Melodien erlauben möglicherweise nur eine passende Lage. Diese Auswahl hat in den gewählten Abschnitten Vorrang vor dem globalen +12-Schalter.",
  voice_verse_default:"Vorgabe für Strophen",voice_chorus_default:"Vorgabe für Refrains",voice_register_low:"Tief",voice_register_middle:"Mittel",voice_register_high:"Hoch",voice_register_auto:"Bisherige Tonhöhensteuerung",
  voice_register_inherit:"Vorgabe verwenden",voice_verse_name:n=>`Strophe ${n}`,voice_chorus_name:n=>`Refrain ${n}`,
  voice_sections_pending:"Einzelne Abschnitte erscheinen hier, sobald markierte Lyrics vorliegen. Bei automatisch geschriebenen Lyrics gelten zunächst die Vorgaben für Strophen und Refrains.",
  voice_section_unaligned:"Zeitzuordnung folgt beim Erstellen",voice_section_uncertain:"Unsicher zugeordnet – bisherige Steuerung",voice_section_range_required:"Für tief/mittel/hoch bitte den Stimmumfang aktivieren.",
  voice_octave_correct:"Oktavkorrektur",
});
Object.assign(I18N.en, {
  voice_section_strict:"Require selected register · stop on conflicts",
  voice_register_anchor:note=>`Middle register reference from your recordings: around ${note}.`,
  voice_plan_blocked:"The requested register cannot be met with these settings. No lower substitute will be created. Check the vocal range and listed sections.",
  voice_play_original:"Play original for comparison", voice_original_short:"Original",
  voice_new:"Sing with my voice", voice_new_hint:"Keep the original and create an additional voice version.",
  voice_original:"Original voice", voice_profile:"Voice profile", voice_low:"Lowest note", voice_high:"Highest note",
  voice_range:"Respect singing range · prioritize natural melody", voice_quality:"Processing",
  voice_standard:"Standard", voice_best:"Best quality – time is secondary", voice_best_short:"Quality mode",
  voice_convert:"Create with another voice", voice_button:"Voice", voice_version:"Voice version", voice_preview_short:"Preview",
  voice_import:"Import finished song", voice_hint:"Lyrics, melody and accompaniment come from the original. Save the new version separately. Range adjustments can change pitch.",
  voice_save_range:"Save as profile defaults", voice_saved:"Profile defaults saved.", voice_preview:"Create a preview first",
  voice_preview_start:"Start preview at second", voice_start:"CREATE VOICE VERSION",
  voice_estimate_note:"Estimate excludes queue time. Other GPU tasks can change runtime. More processing does not guarantee better quality.",
  voice_best_hint:"Additional separation passes and increased overlap. Severe local vocal dropouts are retried in short sections at the same pitch. Your section settings still apply.",
  voice_standard_hint:"Established separation and voice conversion; lossless WAV export.", voice_from_original:"Derived from the original song", voice_solo:"Download converted vocal stem",
  voice_loading:"Estimating runtime …", voice_time:(a,b)=>`Estimated processing: ${a}–${b}`,
  voice_initial:" · rough initial estimate", voice_measured:" · based on previous runtimes", voice_cached:" · separated vocals available",
  voice_missing:"No ready voice profile found.", voice_uploading:"Importing song …", voice_imported:"Song saved in library.",
  voice_generation_time:(a,b)=>`Voice conversion about ${a}–${b}, in addition to song generation.`,
  voice_needs_vocals:"Enable vocals for voice conversion.",
  voice_role_final:"Final version", voice_role_test:"Development test", voice_role_original:"Original", voice_role_import:"Imported song",
  voice_mark_final:"Mark as final",
  voice_review_count:n=>`${n} listening checkpoints`, voice_review_range:"Check singing range", voice_review_pitch:"Check pitch",
  voice_source_time:time=>`Original ${time}`, voice_compare_return:"Switch to voice version", voice_compare_original:"Switch to original",
  voice_section:"Edit section", voice_apply_section:"Insert into full version", voice_preview_length:"Excerpt length in seconds (5–30)",
  voice_section_preview:"Section preview", voice_section_start:"CREATE SECTION PREVIEW",
  voice_section_hint:"Process an excerpt first. After listening, insert it into a new full version. Keep the existing version.",
  voice_apply_confirm:"Insert this excerpt with crossfades into a new full version?",
  voice_sections_applied:n=>`${n} edited section${n===1?"":"s"}`,
  voice_octave:"Lead vocal one octave higher (+12)", voice_octave_hint:"Requested register before conversion. With range enabled, high phrases may be lowered again. Keep accompaniment and tempo unchanged.",
  voice_stable:"Keep a stable register throughout vocal lines",
  voice_harmony:"Second voice in choruses", voice_harmony_interval:"Interval from lead vocal",
  voice_octave_down:"Octave below (−12)", voice_octave_up:"Octave above (+12)", voice_fifth_down:"Fifth below (−7)", voice_fifth_up:"Fifth above (+7)",
  voice_harmony_level:"Second voice level (dB)", voice_chorus_times:"Chorus regions in original song",
  voice_chorus_hint:"Start–end per line, e.g. 00:45–01:10 or 45–70. Preview regions use original song times.",
  voice_harmony_hint:"Follow the lead at a fixed interval. Octaves fit the key; check fifths against chords. With range enabled, omit harmony phrases outside the range.",
  voice_chorus_add:"Add 20 seconds from playback position", voice_chorus_invalid:"Enter start–end per line (seconds or mm:ss).", voice_chorus_play:"Play the original song or its voice version first.",
  voice_harmony_short:"Harmony", voice_lead_short:"Lead",
  voice_chorus_mode:"Set chorus regions",voice_chorus_auto:"Automatically from lyrics with [chorus]",voice_chorus_manual:"Manual times",
  voice_chorus_auto_hint:"Align [chorus] text to the vocals locally after generation. Omit uncertain sections. Listen to detected regions, then adjust their times manually if needed.",
  voice_chorus_found:n=>`${n} chorus tag${n===1?"":"s"} with lyrics available.`,voice_chorus_none:"No [chorus] sections with lyrics. Use manual times for this song.",
  voice_chorus_cached:n=>`${n} chorus region${n===1?"":"s"} already aligned.`,voice_chorus_use:"Use detected times for manual correction",
  voice_chorus_analysis:"Align choruses while processing. Previews also need the full song for alignment.",
  voice_section_pitch:"Octave correction by section",voice_section_pitch_hint:"Choose a target register within your vocal range. Shift entire vocal phrases by octaves, keeping melody and key. Wide melodies may allow only one register. These choices override the global +12 switch in selected sections.",
  voice_verse_default:"Default for verses",voice_chorus_default:"Default for choruses",voice_register_low:"Low",voice_register_middle:"Middle",voice_register_high:"High",voice_register_auto:"Previous pitch settings",
  voice_register_inherit:"Use default",voice_verse_name:n=>`Verse ${n}`,voice_chorus_name:n=>`Chorus ${n}`,
  voice_sections_pending:"Individual sections appear when tagged lyrics are available. For automatically written lyrics, use verse and chorus defaults initially.",
  voice_section_unaligned:"Align timing while processing",voice_section_uncertain:"Uncertain alignment – previous pitch settings",voice_section_range_required:"Enable vocal range for low/middle/high.",
  voice_octave_correct:"Octave correction",
});
Object.assign(I18N.de, {
  voice_plan_pending:"Die tatsächliche Oktave ist noch nicht geprüft. Tief/Mittel/Hoch sind Wünsche; der Stimmumfang kann sie begrenzen. Prüfung erst nach vorhandener vollständiger Gesangsanalyse möglich.",
  voice_plan_limited:"Achtung: Die gewählte Wunschlage wird durch den Stimmumfang begrenzt. Die Angaben bei den Abschnitten zeigen die tatsächlich geplante Oktave. Mehr Rechenzeit ändert diese Begrenzung nicht.",
  voice_plan_ready:"Die geplanten Oktaven sind geprüft. Unsicher zugeordnete Abschnitte werden weiterhin mit der bisherigen Steuerung verarbeitet.",
  voice_plan_rejected:"Keine Abschnittskorrektur: Zeitzuordnung unsicher; bisherige Tonhöhensteuerung bleibt aktiv.",
  voice_plan_row:(level,semitones,note,limited)=>`${level}${limited?' eingeschränkt':''} · tatsächlich ${semitones>0?'+':''}${semitones} Halbtöne gegenüber dem Original · mittlere Tonhöhe etwa ${note}`,
});
Object.assign(I18N.en, {
  voice_plan_pending:"Actual octave not checked yet. Low/Middle/High are targets; vocal range can limit them. Requires an existing full-song vocal analysis.",
  voice_plan_limited:"Warning: vocal range limits the requested register. Each section shows its actual planned octave. More processing time does not change this limit.",
  voice_plan_ready:"Planned octaves checked. Uncertain sections still use the previous pitch settings.",
  voice_plan_rejected:"No section correction: uncertain timing; keep the previous pitch settings.",
  voice_plan_row:(level,semitones,note,limited)=>`${level}${limited?' limited':''} · actual ${semitones>0?'+':''}${semitones} semitones from the original · median pitch around ${note}`,
});
for (const prefix of ["genVoice", "voice"]) {
  $(`#${prefix}Layers`).innerHTML=`
    <button type="button" class="sek" id="${prefix}Octave" aria-pressed="false" data-i18n="voice_octave"></button>
    <p class="small" data-i18n="voice_octave_hint"></p>
    <label class="check"><input id="${prefix}Stable" type="checkbox" checked><span data-i18n="voice_stable"></span></label>
    <button type="button" class="sek" id="${prefix}Sections" aria-pressed="false" data-i18n="voice_section_pitch"></button>
    <div id="${prefix}SectionOptions" hidden>
      <p class="small" data-i18n="voice_section_pitch_hint"></p>
      <label class="check"><input id="${prefix}SectionStrict" type="checkbox" checked><span data-i18n="voice_section_strict"></span></label>
      <div class="row">
        <label class="field"><span class="lbl" data-i18n="voice_verse_default"></span><select id="${prefix}VerseRegister">${registerOptions('middle')}</select></label>
        <label class="field"><span class="lbl" data-i18n="voice_chorus_default"></span><select id="${prefix}ChorusRegister">${registerOptions('high')}</select></label>
      </div>
      <div id="${prefix}SectionList" class="voice-section-list"></div>
      <p id="${prefix}SectionPlan" class="voice-estimate" role="status" aria-live="polite"></p>
    </div>
    <label class="check"><input id="${prefix}Harmony" type="checkbox"><span data-i18n="voice_harmony"></span></label>
    <div id="${prefix}HarmonyOptions" hidden>
      <label class="field"><span class="lbl" data-i18n="voice_chorus_mode"></span><select id="${prefix}ChorusMode"><option value="lyrics" data-i18n="voice_chorus_auto"></option><option value="manual" data-i18n="voice_chorus_manual"></option></select></label>
      <p class="small" id="${prefix}AutoHint" data-i18n="voice_chorus_auto_hint"></p>
      ${prefix==="voice"?'<p class="small" id="voiceChorusStatus"></p><button type="button" class="sek mini" id="voiceChorusUse" hidden data-i18n="voice_chorus_use"></button>':''}
      <label class="field"><span class="lbl" data-i18n="voice_harmony_interval"></span><select id="${prefix}Interval">
        <option value="-12" data-i18n="voice_octave_down"></option><option value="12" data-i18n="voice_octave_up"></option>
        <option value="-7" data-i18n="voice_fifth_down"></option><option value="7" data-i18n="voice_fifth_up"></option>
      </select></label>
      <label class="field"><span class="lbl" data-i18n="voice_harmony_level"></span><input type="number" id="${prefix}HarmonyDb" min="-24" max="0" step="1" value="-12"></label>
      <label class="field" id="${prefix}TimesField" hidden><span class="lbl" data-i18n="voice_chorus_times"></span><textarea id="${prefix}Choruses" rows="3" placeholder="00:45–01:10&#10;02:00–02:25"></textarea></label>
      ${prefix==="voice"?'<button type="button" class="sek mini" id="voiceChorusAdd" data-i18n="voice_chorus_add"></button>':''}
      <p class="small" id="${prefix}ManualHint" hidden data-i18n="voice_chorus_hint"></p><p class="small" data-i18n="voice_harmony_hint"></p>
    </div>`;
  $(`#${prefix}Octave`).addEventListener("click",()=>{
    const button=$(`#${prefix}Octave`);button.setAttribute("aria-pressed",button.getAttribute("aria-pressed")==="true"?"false":"true");
    prefix==="voice"?updateVoiceEstimate():generationVoiceEstimate();
  });
  $(`#${prefix}Harmony`).addEventListener("change",()=>{
    $(`#${prefix}HarmonyOptions`).hidden=!$(`#${prefix}Harmony`).checked;
  });
  $(`#${prefix}Sections`).addEventListener('click',()=>{
    const button=$(`#${prefix}Sections`);button.setAttribute('aria-pressed',button.getAttribute('aria-pressed')==='true'?'false':'true');
    paintSectionChoices(prefix);
    syncVoiceLayerRange(prefix);prefix==='voice'?updateVoiceEstimate():generationVoiceEstimate();
  });
}
applyI18n();

let voiceProfiles = [], voiceSong = null, estimateSequence = 0, sectionBaseId = null, voiceSourceDuration = 0, chorusData=null;
function registerOptions(selected,inherit=false) {
  return (inherit?['inherit','auto','low','middle','high']:['auto','low','middle','high']).map(value=>`<option value="${value}" ${value===selected?'selected':''}>${esc(t(value==='inherit'?'voice_register_inherit':'voice_register_'+value))}</option>`).join('');
}
function generationSections() {
  const sections=[];let current={tag:'untagged',lines:[]};
  for(const part of form.lyrics.value.split(/(\[[^\]\n]+\])/)) {
    if(part.startsWith('[')&&part.endsWith(']')) {if(current.lines.length)sections.push(current);current={tag:part.slice(1,-1).trim().toLowerCase(),lines:[]};}
    else current.lines.push(...part.split(/\r?\n/).map(line=>line.trim()).filter(Boolean));
  }
  if(current.lines.length)sections.push(current);
  const counts={};return sections.map((s,index)=>{
    const kind=/^(?:verse|strophe)(?:\b|$)/.test(s.tag)?'verse':/^(?:final\s+)?(?:chorus|refrain)(?:\b|$)/.test(s.tag)?'chorus':'other';
    counts[kind]=(counts[kind]||0)+1;return {section:index,tag:s.tag,kind,number:counts[kind],first_line:s.lines[0]};
  });
}
function sectionLabel(s) {return s.kind==='verse'?t('voice_verse_name',s.number):s.kind==='chorus'?t('voice_chorus_name',s.number):`[${s.tag}]`;}
function paintSectionChoices(prefix,saved=null) {
  const catalog=prefix==='voice'?(chorusData?.sections||[]):generationSections();
  const container=$(`#${prefix}SectionList`);
  const previous=saved||{overrides:[...container.querySelectorAll('select[data-section]')].filter(el=>el.value!=='inherit').map(el=>({section:Number(el.dataset.section),tag:el.dataset.tag,level:el.value}))};
  const aligned=prefix==='voice'?chorusData?.results[$('#voiceQuality').value]:null;
  container.innerHTML=catalog.length?catalog.map(s=>{
    const value=previous.overrides?.find(r=>r.section===s.section&&r.tag===s.tag)?.level||'inherit';
    const region=aligned?.sections?.find(r=>r.section===s.section),rejected=aligned?.sections_rejected?.some(r=>r.section===s.section);
    const timing=region?`${reviewTime(region.start)}–${reviewTime(region.end)}`:t(rejected?'voice_section_uncertain':'voice_section_unaligned');
    return `<label class="field voice-section-choice"><span class="lbl">${esc(sectionLabel(s))} · ${esc(timing)}</span><span class="small">${esc(s.first_line)}</span><select data-section="${s.section}" data-tag="${esc(s.tag)}" data-kind="${s.kind}" aria-label="${esc(sectionLabel(s))}">${registerOptions(value,true)}</select><span class="small" data-section-plan="${s.section}"></span></label>`;
  }).join(''):`<p class="small">${esc(t('voice_sections_pending'))}</p>`;
  refreshSectionDefaults(prefix);
  showSectionPlan(prefix);
}
function refreshSectionDefaults(prefix) {
  for(const el of $(`#${prefix}SectionList`).querySelectorAll('select[data-section]')) {
    const inherited=el.dataset.kind==='verse'?$(`#${prefix}VerseRegister`).value:el.dataset.kind==='chorus'?$(`#${prefix}ChorusRegister`).value:'auto';
    el.querySelector('option[value="inherit"]').textContent=`${t('voice_register_inherit')}: ${t('voice_register_'+inherited)}`;
  }
}
function sectionPitchRequest(prefix) {
  return {enabled:$(`#${prefix}Sections`).getAttribute('aria-pressed')==='true',strict:$(`#${prefix}SectionStrict`).checked,verse:$(`#${prefix}VerseRegister`).value,chorus:$(`#${prefix}ChorusRegister`).value,
    overrides:[...$(`#${prefix}SectionList`).querySelectorAll('select[data-section]')].filter(el=>el.value!=='inherit').map(el=>({section:Number(el.dataset.section),tag:el.dataset.tag,level:el.value}))};
}
function showSectionPlan(prefix, plan=null) {
  const enabled=$(`#${prefix}Sections`).getAttribute('aria-pressed')==='true';
  const box=$(`#${prefix}SectionPlan`);box.hidden=!enabled;
  const warning=!!plan?.available && plan.sections.some(r=>r.range_limited || r.range_conflict);
  box.textContent=t(!plan?.available?'voice_plan_pending':plan.blocked?'voice_plan_blocked':warning?'voice_plan_limited':'voice_plan_ready')+
    (plan?.training_center_note?' '+t('voice_register_anchor',plan.training_center_note):'')+
    (plan?.blocked?' '+plan.issues.map(r=>`${r.label}: ${r.reason}`).join('; '):'');
  for(const span of $(`#${prefix}SectionList`).querySelectorAll('[data-section-plan]')) {
    const id=Number(span.dataset.sectionPlan), row=plan?.sections?.find(r=>r.section===id);
    const rejected=plan?.rejected?.some(r=>r.section===id);
    span.textContent=!enabled?'':row?t('voice_plan_row',t('voice_register_'+row.level),row.octave_shift*12,row.output_median_note,row.range_limited || row.range_conflict):
      (rejected?t('voice_plan_rejected'):'');
  }
}
window.voiceProfileName = id => voiceProfiles.find(p=>p.id===id)?.name || id;
function chorusRegions(text) {
  const clock=value=>{
    const parts=value.trim().split(":");
    if(parts.length>2 || parts.some(p=>!/^\d+(?:\.\d+)?$/.test(p)) || (parts.length===2 && Number(parts[1])>=60))throw new Error(t("voice_chorus_invalid"));
    return parts.length===2?Number(parts[0])*60+Number(parts[1]):Number(parts[0]);
  };
  return text.trim()?text.trim().split(/\r?\n/).filter(line=>line.trim()).map(line=>{
    const parts=line.trim().split(/\s*[-–—]\s*/);if(parts.length!==2)throw new Error(t("voice_chorus_invalid"));
    return {start:clock(parts[0]),end:clock(parts[1])};
  }):[];
}
function setVoiceLayers(prefix, request={}) {
  if(prefix==='voice')window.setMixLevels?.('voice',request.mix_levels||{});
  $(`#${prefix}Octave`).setAttribute("aria-pressed",request.lead_octave===12?"true":"false");
  $(`#${prefix}Stable`).checked=request.stable_register!==false;
  const harmony=request.harmony||{};
  $(`#${prefix}Harmony`).checked=!!harmony.enabled;$(`#${prefix}HarmonyOptions`).hidden=!harmony.enabled;
  $(`#${prefix}Interval`).value=String(harmony.interval??-12);$(`#${prefix}HarmonyDb`).value=harmony.gain_db??-12;
  $(`#${prefix}Choruses`).value=(harmony.regions||[]).map(r=>`${r.start}–${r.end}`).join("\n");
  $(`#${prefix}ChorusMode`).value=harmony.mode||(harmony.regions?.length?'manual':'lyrics');
  const sections=request.section_pitch||{};
  $(`#${prefix}SectionStrict`).checked=sections.strict!==false;
  $(`#${prefix}Sections`).setAttribute('aria-pressed',sections.enabled?'true':'false');
  $(`#${prefix}VerseRegister`).value=sections.verse||'middle';$(`#${prefix}ChorusRegister`).value=sections.chorus||'high';
  paintSectionChoices(prefix,sections);
  syncVoiceLayerRange(prefix);
}
function syncVoiceLayerRange(prefix) {
  $(`#${prefix}Stable`).disabled=!$(`#${prefix}Range`).checked;
  const automatic=$(`#${prefix}ChorusMode`).value==='lyrics';
  $(`#${prefix}TimesField`).hidden=automatic;$(`#${prefix}ManualHint`).hidden=automatic;$(`#${prefix}AutoHint`).hidden=!automatic;
  if(prefix==='voice')$("#voiceChorusAdd").hidden=automatic;
  $(`#${prefix}Sections`).disabled=!$(`#${prefix}Range`).checked;
  $(`#${prefix}SectionOptions`).hidden=$(`#${prefix}Sections`).getAttribute('aria-pressed')!=='true';
  refreshSectionDefaults(prefix);
}
function voiceRequest(prefix) {
  const mode=$(`#${prefix}ChorusMode`).value;
  const regions=$(`#${prefix}Harmony`).checked && mode==='manual'?chorusRegions($(`#${prefix}Choruses`).value):[];
  if($(`#${prefix}Harmony`).checked && mode==='manual' && !regions.length)throw new Error(t("voice_chorus_invalid"));
  return {profile_id:$(`#${prefix}Profile`).value, enabled:$(`#${prefix}Range`).checked,
    min_note:$(`#${prefix}Low`).value.trim(), max_note:$(`#${prefix}High`).value.trim(),
    quality:$(`#${prefix}Quality`).value, preview:prefix==="voice" && $("#voicePreview").checked,
    preview_start:prefix==="voice" ? Number($("#voicePreviewStart").value) : 0,
    preview_seconds:prefix==="voice" ? Number($("#voicePreviewLength").value) : 20,
    base_song_id:prefix==="voice" ? sectionBaseId : null,
    instrumental_song_id:prefix==="voice" ? (voiceSong.params.job_type==='instrumental'?voiceSong.id:voiceSong.params.backing_song_id||null) : null,
    lead_octave:$(`#${prefix}Octave`).getAttribute("aria-pressed")==="true"?12:0,
    stable_register:$(`#${prefix}Range`).checked && $(`#${prefix}Stable`).checked,
    section_pitch:sectionPitchRequest(prefix),
    mix_levels:window.mixLevelRequest?.(prefix==='voice'?'voice':'gen')||{},
    harmony:{enabled:$(`#${prefix}Harmony`).checked,interval:Number($(`#${prefix}Interval`).value),gain_db:Number($(`#${prefix}HarmonyDb`).value),
      regions,mode}};
}
window.voiceGenerationRequest = () => {
  if (!$("#genVoiceProfile").value) return null;
  if (form.instrumental.checked) throw new Error(t("voice_needs_vocals"));
  return voiceRequest("genVoice");
};
function selectVoiceDefaults(prefix) {
  const p = voiceProfiles.find(p=>p.id===$(`#${prefix}Profile`).value);
  if(p) { $(`#${prefix}Low`).value=p.min_note; $(`#${prefix}High`).value=p.max_note; $(`#${prefix}Range`).checked=p.enabled; syncVoiceLayerRange(prefix); }
}
async function loadVoiceProfiles() {
  const data = await api("/api/voices"); voiceProfiles=data.profiles;
  const options=voiceProfiles.map(p=>`<option value="${esc(p.id)}">${esc(p.name)}</option>`).join("");
  const conversionSelected=$("#voiceProfile").value;
  $("#voiceProfile").innerHTML=options;
  if(voiceProfiles.some(p=>p.id===conversionSelected))$("#voiceProfile").value=conversionSelected;
  else if(conversionSelected){selectVoiceDefaults('voice');if($('#voiceDlg').open)updateVoiceEstimate();}
  const selected=$("#genVoiceProfile").value;
  $("#genVoiceProfile").innerHTML=`<option value="">${t("voice_original")}</option>`+options;
  $("#genVoiceProfile").value=voiceProfiles.some(p=>p.id===selected)?selected:"";
  if(selected && !$('#genVoiceProfile').value)generationVoiceEstimate();
  return data;
}
window.refreshVoiceProfiles=loadVoiceProfiles;
let generationEstimateSequence=0;
async function generationVoiceEstimate() {
  const selected=!!$("#genVoiceProfile").value;
  $("#genVoiceOptions").hidden=!selected;
  if(!selected) return;
  showSectionPlan('genVoice');
  const sequence=++generationEstimateSequence;
  try {
    const request=voiceRequest("genVoice");
    syncVoiceLayerRange('genVoice');
    const result=await api("/api/voice-plan",{method:"POST",body:JSON.stringify({seconds:Number(form.duration.value),quality:$("#genVoiceQuality").value,harmony:request.harmony.enabled,auto_chorus:request.harmony.mode==='lyrics',section_pitch:request.section_pitch.enabled})});
    if(sequence===generationEstimateSequence)$("#genVoiceEstimate").textContent=t("voice_generation_time",fmt(result.seconds_low),fmt(result.seconds_high))+t(result.basis==="measured"?"voice_measured":"voice_initial");
  }catch(e){if(sequence===generationEstimateSequence)$("#genVoiceEstimate").textContent=e.message;}
}
async function updateVoiceEstimate() {
  if(!voiceSong) return;
  const sequence=++estimateSequence;
  syncVoiceLayerRange('voice');updateChorusStatus();
  showSectionPlan('voice');
  $("#voicePreviewField").hidden=!$("#voicePreview").checked;
  $("#voicePreviewLengthField").hidden=!$("#voicePreview").checked;
  $("#voiceQualityHint").textContent=t($("#voiceQuality").value==="best"?"voice_best_hint":"voice_standard_hint");
  $("#voiceEstimate").textContent=t("voice_loading"); $("#voiceStart").disabled=true;
  try {
    const e=await api(`/api/songs/${voiceSong.id}/voice-estimate`, {method:"POST",body:JSON.stringify(voiceRequest("voice"))});
    if(sequence!==estimateSequence) return;
    $("#voiceEstimate").textContent=t("voice_time",fmt(e.seconds_low),fmt(e.seconds_high))+t(e.basis==="initial"?"voice_initial":"voice_measured")+(e.cached_stems?t("voice_cached"):"");
    showSectionPlan('voice',e.section_plan);
    $("#voiceStart").disabled=!!e.section_plan?.blocked;
  } catch(e) { if(sequence===estimateSequence) $("#voiceEstimate").textContent=e.message; }
}
window.openVoiceDialog=async (song, section=false, octaveCorrection=false) => {
  try {
    const data=await loadVoiceProfiles();
    if(!data.ready || !voiceProfiles.length) throw new Error(t("voice_missing"));
    voiceSong=song; $("#voiceSongTitle").textContent=song.title||song.caption.slice(0,100);
    $('#voiceBackingHint').hidden=!(song.params.job_type==='instrumental'||song.params.backing_song_id);
    const sourceSong=song.params.source_song_id?await api(`/api/songs/${song.params.source_song_id}`):song;
    voiceSourceDuration=sourceSong.result_meta?.duration||sourceSong.params.duration;
    chorusData=await api(`/api/songs/${song.id}/choruses`);
    sectionBaseId=section?song.id:null;
    $("#voiceDlgTitle").textContent=t(section?"voice_section":octaveCorrection?"voice_octave_correct":"voice_convert");
    $("#voiceStart").textContent=t(section?"voice_section_start":"voice_start");
    $("#voiceSectionHint").hidden=!section;
    $("#voicePreview").disabled=section;
    $("#voicePreview").checked=section;
    $("#voicePreviewLength").value=20;
    setVoiceLayers("voice", song.params.voice||{});
    if(song.result_meta?.harmony?.regions?.length)$("#voiceChoruses").value=song.result_meta.harmony.regions.map(r=>`${r.start}–${r.end}`).join('\n');
    selectVoiceDefaults("voice"); $("#voicePreviewStart").value=Math.min(30,Math.max(0,(voiceSourceDuration||60)-20));
    if(song.params.voice) {
      if(voiceProfiles.some(p=>p.id===song.params.voice.profile_id)){
        $("#voiceProfile").value=song.params.voice.profile_id;
        $("#voiceLow").value=song.params.voice.min_note;$("#voiceHigh").value=song.params.voice.max_note;
        $("#voiceRange").checked=song.params.voice.enabled;
      }
      $("#voiceQuality").value=song.params.voice.quality;
      syncVoiceLayerRange("voice");
      if(section && currentId===song.id && ws)$("#voicePreviewStart").value=Math.max(0,Math.min(ws.getCurrentTime(),song.result_meta.duration-5)).toFixed(1);
    }
    if(octaveCorrection){$('#voiceRange').checked=true;$('#voiceSections').setAttribute('aria-pressed','true');syncVoiceLayerRange('voice');}
    paintSectionChoices('voice',song.params.voice?.section_pitch||{});
    $("#voiceDlg").showModal(); updateVoiceEstimate();
  }catch(e){alert(e.message);}
};
function updateChorusStatus() {
  if(!chorusData)return;
  const existing=chorusData.results[$('#voiceQuality').value];
  $('#voiceChorusStatus').textContent=existing?t('voice_chorus_cached',existing.regions.length)+(existing.regions.length?' '+existing.regions.map(r=>`${reviewTime(r.start)}–${reviewTime(r.end)}`).join(' · '):''):
    (chorusData.tagged_count?t('voice_chorus_found',chorusData.tagged_count)+' '+t('voice_chorus_analysis'):t('voice_chorus_none'));
  $('#voiceChorusUse').hidden=!existing?.regions?.length;
}
$('#voiceChorusUse').addEventListener('click',()=>{
  const result=chorusData?.results[$('#voiceQuality').value];if(!result?.regions?.length)return;
  $('#voiceChoruses').value=result.regions.map(r=>`${r.start}–${r.end}`).join('\n');$('#voiceChorusMode').value='manual';updateVoiceEstimate();
});
$("#voiceClose").addEventListener("click",()=>{estimateSequence++;$("#voiceDlg").close();});
$("#voiceForm").addEventListener("change",e=>{if(e.target.id==="voiceProfile")selectVoiceDefaults("voice");if(e.target.id==='voiceQuality')paintSectionChoices('voice');syncVoiceLayerRange("voice");updateVoiceEstimate();});
let voiceInputTimer, generationInputTimer;
$("#voiceForm").addEventListener("input",()=>{clearTimeout(voiceInputTimer);voiceInputTimer=setTimeout(updateVoiceEstimate,300);});
$("#genVoiceLayers").addEventListener("input",()=>{clearTimeout(generationInputTimer);generationInputTimer=setTimeout(generationVoiceEstimate,300);});
$("#voiceForm").addEventListener("submit",async e=>{
  e.preventDefault(); const button=$("#voiceStart"); if(button.disabled)return;button.disabled=true;
  try {await api(`/api/songs/${voiceSong.id}/voice`,{method:"POST",body:JSON.stringify(voiceRequest("voice"))});$("#voiceDlg").close();refresh();}
  catch(err){$("#voiceEstimate").textContent=err.message;button.disabled=false;}
});

const voiceReviewOpen=new Set();
const reviewTime=seconds=>{const cents=Math.round(seconds*100);return `${fmt(cents/100)}.${String(cents%100).padStart(2,"0")}`;};
$("#library").addEventListener("toggle",event=>{
  if(event.target.matches(".voice-review") && event.target.isConnected){
    const id=event.target.closest(".song").dataset.id;
    event.target.open?voiceReviewOpen.add(id):voiceReviewOpen.delete(id);
  }
},true);
window.voiceReviewMarkup=song=>{
  const regions=song.result_meta?.review_regions||[];
  if(!regions.length)return "";
  return `<details class="voice-review" ${voiceReviewOpen.has(song.id)?"open":""}><summary>${esc(t("voice_review_count",regions.length))}</summary><div class="voice-review-items">`+
    regions.map(r=>`<button class="sek mini" data-a="review" data-time="${r.start}">${reviewTime(r.start)}–${reviewTime(r.end)} · ${esc(t(r.kind==="pitch"?"voice_review_pitch":"voice_review_range"))}${song.result_meta.preview?` · ${esc(t("voice_source_time",reviewTime(r.source_start)))}`:""}</button>`).join("")+`</div></details>`;
};
let comparisonVoice=null, playbackSong=null;
window.onSongPlayback=song=>{
  playbackSong=song;
  if(['voice','deep'].includes(song.params.job_type))comparisonVoice=song;
  else if(comparisonVoice?.params.source_song_id!==song.id)comparisonVoice=null;
  const button=$("#compareBtn");button.hidden=!comparisonVoice;
  const editing=['voice','deep'].includes(song.params.job_type);
  button.textContent=t(editing?'voice_compare_original':comparisonVoice?.params.job_type==='deep'?'deep_compare_return':'voice_compare_return');
  button.title=comparisonVoice?.result_meta?.preview ? `${fmt(comparisonVoice.result_meta.preview_start)}–${fmt(comparisonVoice.result_meta.preview_start+comparisonVoice.result_meta.duration)}` : "";
};
window.compareVoice=async song=>{
  try{
    const version=['voice','deep'].includes(song?.params.job_type)?song:comparisonVoice;
    if(!version)return;
    const offset=version.result_meta?.preview?version.result_meta.preview_start:0;
    if(currentId===version.params.source_song_id){
      const position=ws.getCurrentTime()-offset;
      await play(version,Math.max(0,Math.min(position,(version.result_meta?.duration||20)-.01)));
    }else{
      const position=(currentId===version.id?ws.getCurrentTime():0)+offset;
      comparisonVoice=version;
      await play(await api(`/api/songs/${version.params.source_song_id}`),position);
    }
  }catch(e){alert(e.message);}
};
$("#compareBtn").addEventListener("click",()=>window.compareVoice(playbackSong));
window.applyVoiceSection=async song=>{
  try{
    await api(`/api/songs/${song.params.voice.base_song_id}/apply-section`,{method:"POST",body:JSON.stringify({preview_song_id:song.id})});
    refresh();
  }catch(e){alert(e.message);}
};
$("#voiceSaveRange").addEventListener("click",async()=>{
  const r={profile_id:$("#voiceProfile").value,enabled:$("#voiceRange").checked,min_note:$("#voiceLow").value.trim(),max_note:$("#voiceHigh").value.trim()};
  try {await api(`/api/voices/${r.profile_id}`,{method:"PUT",body:JSON.stringify({enabled:r.enabled,min_note:r.min_note,max_note:r.max_note})});
    const selected=r.profile_id;await loadVoiceProfiles();$("#voiceProfile").value=selected;$("#voiceEstimate").textContent=t("voice_saved");}
  catch(e){$("#voiceEstimate").textContent=e.message;}
});
$("#genVoiceProfile").addEventListener("change",()=>{
  selectVoiceDefaults("genVoice");
  if($("#genVoiceProfile").value && form.instrumental.checked){form.instrumental.checked=false;syncLyrics();$("#lyricsBox").open=true;}
  generationVoiceEstimate();
});
$("#genVoiceQuality").addEventListener("change",generationVoiceEstimate);
form.lyrics.addEventListener('input',()=>{paintSectionChoices('genVoice');generationVoiceEstimate();});
$("#genVoiceLayers").addEventListener("change",generationVoiceEstimate);
$("#genVoiceRange").addEventListener("change",()=>{syncVoiceLayerRange("genVoice");generationVoiceEstimate();});
$("#voiceChorusAdd").addEventListener("click",()=>{
  const root=voiceSong.params.source_song_id||voiceSong.id;
  if(!ws || !playbackSong || (playbackSong.params.source_song_id||playbackSong.id)!==root)return alert(t("voice_chorus_play"));
  const offset=playbackSong.result_meta?.preview?playbackSong.result_meta.preview_start:0;
  const start=Math.max(0,ws.getCurrentTime()+offset), end=Math.min(start+20,voiceSourceDuration);
  const field=$("#voiceChoruses");field.value+=(field.value.trim()?"\n":"")+`${start.toFixed(2)}–${end.toFixed(2)}`;updateVoiceEstimate();
});
form.duration.addEventListener("input",generationVoiceEstimate);
$("#libraryImportBtn").addEventListener("click",()=>$("#libraryImportFile").click());
$("#libraryImportFile").addEventListener("change",async()=>{
  const f=$("#libraryImportFile").files[0];if(!f)return;
  const button=$("#libraryImportBtn");button.disabled=true;$("#libraryImportStatus").textContent=t("voice_uploading");
  try {const data=new FormData();data.append("audio",f);await api("/api/library/import",{method:"POST",body:data});setFolder("",false);$("#search").value="";onlyFav=false;$("#onlyFav").setAttribute("aria-pressed","false");$("#libraryImportStatus").textContent=t("voice_imported");refresh();}
  catch(e){$("#libraryImportStatus").textContent=e.message;}
  finally{button.disabled=false;$("#libraryImportFile").value="";}
});
document.addEventListener("langchange",()=>{$("#genVoiceProfile").options[0].textContent=t("voice_original");paintSectionChoices('genVoice');generationVoiceEstimate();if($("#voiceDlg").open){paintSectionChoices('voice');updateVoiceEstimate();}});
loadVoiceProfiles().then(()=>{generationVoiceEstimate();render();}).catch(e=>{$("#libraryImportStatus").textContent=e.message;});
