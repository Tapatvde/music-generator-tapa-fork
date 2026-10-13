// Independent opt-in controls for generation, original edits and voice versions.
Object.assign(I18N.de,{
  mix_title:'Pegel und Balance',mix_vocals:'Gesang stabil halten',mix_backing:'Begleitung stabil halten',
  mix_vocal_db:'Gesangspegel',mix_backing_db:'Begleitungspegel',
  mix_hint:'Sanfter, begrenzter Ausgleich nach der Erzeugung. Die zweite Stimme folgt der Hauptstimme. Begleitung und Gesang werden unabhängig geregelt; Pausen und Ausklang bleiben erhalten.',
  mix_cost:'Ohne Stimmumwandlung werden die Spuren zusätzlich getrennt. Das benötigt mehr Zeit und kann Trennartefakte verursachen. Pegelkorrektur repariert keine verlorenen Klangdetails.',
  mix_fixed:'Bei einer gespeicherten Instrumentalgrundlage verändern Begleitungskorrektur und Begleitungspegel die bisher feste Begleitung.'
});
Object.assign(I18N.en,{
  mix_title:'Levels and balance',mix_vocals:'Keep vocals stable',mix_backing:'Keep backing stable',
  mix_vocal_db:'Vocal level',mix_backing_db:'Backing level',
  mix_hint:'Gentle, bounded adjustment after generation. Harmony follows the lead. Backing and vocals are controlled independently; pauses and the ending are preserved.',
  mix_cost:'Without voice conversion, an additional stem separation takes more time and may introduce separation artifacts. Level adjustment cannot repair lost sound details.',
  mix_fixed:'For a saved instrumental template, backing correction and backing level change the previously fixed backing.'
});
document.querySelectorAll('[data-mix-levels]').forEach(host=>{
  const prefix=host.dataset.mixLevels;
  host.innerHTML=`<details class="voice-section mix-level-controls"><summary data-i18n="mix_title">Pegel und Balance</summary>
    <label class="check"><input type="checkbox" id="${prefix}MixVocals"><span data-i18n="mix_vocals"></span></label>
    <label class="check"><input type="checkbox" id="${prefix}MixBacking"><span data-i18n="mix_backing"></span></label>
    <div class="deep-grid">
      <label class="field"><span class="lbl" data-i18n="mix_vocal_db"></span><input id="${prefix}MixVocalDb" type="range" min="-6" max="6" step="0.5" value="0"><output id="${prefix}MixVocalValue">0 dB</output></label>
      <label class="field"><span class="lbl" data-i18n="mix_backing_db"></span><input id="${prefix}MixBackingDb" type="range" min="-6" max="6" step="0.5" value="0"><output id="${prefix}MixBackingValue">0 dB</output></label>
    </div><p class="small" data-i18n="mix_hint"></p><p class="small" data-i18n="mix_cost"></p>
    ${prefix==='voice'?'<p class="small" data-i18n="mix_fixed"></p>':''}</details>`;
  ['Vocal','Backing'].forEach(kind=>{
    $(`#${prefix}Mix${kind}Db`).addEventListener('input',()=>{
      $(`#${prefix}Mix${kind}Value`).textContent=`${Number($(`#${prefix}Mix${kind}Db`).value)>0?'+':''}${$(`#${prefix}Mix${kind}Db`).value} dB`;
    });
  });
});
window.mixLevelRequest=prefix=>({vocals:$(`#${prefix}MixVocals`).checked,backing:$(`#${prefix}MixBacking`).checked,
  vocal_db:Number($(`#${prefix}MixVocalDb`).value),backing_db:Number($(`#${prefix}MixBackingDb`).value)});
window.setMixLevels=(prefix,settings={})=>{
  $(`#${prefix}MixVocals`).checked=!!settings.vocals;$(`#${prefix}MixBacking`).checked=!!settings.backing;
  ['Vocal','Backing'].forEach(kind=>{
    const value=settings[kind==='Vocal'?'vocal_db':'backing_db']||0;
    $(`#${prefix}Mix${kind}Db`).value=value;$(`#${prefix}Mix${kind}Value`).textContent=`${value>0?'+':''}${value} dB`;
  });
};
applyI18n();
