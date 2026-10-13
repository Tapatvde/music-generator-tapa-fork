Object.assign(I18N.de, {
  profiles_manage:'Stimmprofile verwalten', profiles_name:'Name des neuen Stimmprofils',
  profiles_recordings:'Soloaufnahmen · WAV, MP3, FLAC, M4A, OGG', profiles_import:'Aufnahmen einlesen',
  profiles_hint:'Importiere trockene Soloaufnahmen einer einzelnen Stimme. Ab 30 Sekunden, besser mehrere Minuten ohne Musik, Hall und Doppelungen. Verwende eigene oder ausdrücklich freigegebene Stimmen. Das Training läuft lokal auf der NVIDIA-Grafikkarte.',
  profiles_note:'Erst ein erfolgreich trainiertes und technisch geprüftes Profil erscheint im Auswahlmenü. Mehr Trainingsrunden garantieren kein besseres Ergebnis. Die Stimmähnlichkeit und die vorläufigen Umfangsgrenzen bitte anschließend mit einem anderen Song prüfen.',
  profiles_available:'Im Auswahlmenü verfügbar', profiles_none:'Noch kein neues Trainingsprofil angelegt.',
  profiles_train:'Training starten', profiles_rounds:n=>`${n} Trainingsrunden`, profiles_importing:'Aufnahmen werden eingelesen …',
  profiles_draft:'Aufnahmen eingelesen · bereit zum Training', profiles_queued:'Training wartet in der gemeinsamen Warteschlange',
  profiles_running:'Training läuft', profiles_done:'Training fertig · im Auswahlmenü verfügbar',
  profiles_error:'Training fehlgeschlagen', profiles_cancelled:'Training abgebrochen',
  profiles_missing:'Trainingsbestandteile fehlen. Training kann derzeit nicht gestartet werden.',
  profiles_cancel:'Training abbrechen', close:'Schließen',
  profiles_remove:'Entfernen', profiles_restore:'Wiederherstellen', profiles_trash:'Papierkorb', profiles_removed:'Entfernt',
  profiles_trash_note:'Entfernte Einträge verschwinden aus der Verwaltung und dem Auswahlmenü. Dateien bleiben für die Wiederherstellung gespeichert. Bereits erzeugte Songs bleiben erhalten.',
  instrumental_create:'Instrumental erstellen', instrumental_version:'Instrumentalversion', instrumental_voice:'Neue Gesangsversion',
  instrumental_hint:'Der Gesang wird aus genau dieser Songfassung entfernt. Eine zusätzliche Instrumentalversion wird gespeichert; Original und Gesangsvorlage bleiben erhalten. Später kannst Du darauf andere Stimmprofile ausprobieren. Text und Gesangsmelodie bleiben dabei die der Vorlage. Kleine Gesangsreste oder Trennartefakte sind möglich.',
  instrumental_backing_hint:'Die gespeicherte Instrumentalbegleitung bleibt erhalten. Text und Gesangsmelodie stammen aus der ursprünglichen Gesangsvorlage.'
});
Object.assign(I18N.en, {
  profiles_manage:'Manage voice profiles', profiles_name:'New voice profile name',
  profiles_recordings:'Solo recordings · WAV, MP3, FLAC, M4A, OGG', profiles_import:'Import recordings',
  profiles_hint:'Import dry solo recordings of one singer. At least 30 seconds, preferably several minutes without music, reverb or doubling. Use your own voice or voices with explicit permission. Training runs locally on the NVIDIA GPU.',
  profiles_note:'Only successfully trained and technically checked profiles appear in the dropdown. More training epochs do not guarantee a better result. Check voice resemblance and provisional range limits with a different song afterwards.',
  profiles_available:'Available in the dropdown', profiles_none:'No new training profiles yet.',
  profiles_train:'Start training', profiles_rounds:n=>`${n} training epochs`, profiles_importing:'Importing recordings …',
  profiles_draft:'Recordings imported · ready for training', profiles_queued:'Training waiting in the shared queue',
  profiles_running:'Training running', profiles_done:'Training complete · available in the dropdown',
  profiles_error:'Training failed', profiles_cancelled:'Training cancelled',
  profiles_missing:'Training components are missing. Training cannot start yet.', profiles_cancel:'Cancel training', close:'Close',
  profiles_remove:'Remove', profiles_restore:'Restore', profiles_trash:'Trash', profiles_removed:'Removed',
  profiles_trash_note:'Removed entries disappear from the library and dropdown. Files are retained for recovery. Previously generated songs are preserved.',
  instrumental_create:'Create instrumental', instrumental_version:'Instrumental version', instrumental_voice:'New vocal version',
  instrumental_hint:'Vocals are removed from this exact song version. An additional instrumental version is saved; the original and vocal template remain available. You can then try other voice profiles over this backing. Lyrics and vocal melody follow the template. Vocal residue or separation artifacts may remain.',
  instrumental_backing_hint:'The saved instrumental backing is preserved. Lyrics and vocal melody follow the original vocal template.'
});

let profilePoll, profileSignature='', instrumentalSong=null;
const epochSelections=new Map();
async function refreshProfileLibrary() {
  const data=await api('/api/voice-training');
  const available=await window.refreshVoiceProfiles();
  const signature=JSON.stringify([data,available.profiles]);
  if(signature===profileSignature)return;
  profileSignature=signature;
  $('#profileLibraryStatus').textContent=data.ready?'':t('profiles_missing');
  $('#profileLibraryItems').innerHTML=`<div class="profile-card"><strong>${t('profiles_available')}</strong><p class="small">${available.profiles.map(p=>esc(p.name)).join(' · ')||'—'}</p></div>`+
    (data.items.length?data.items.map(p=>`<article class="profile-card" data-profile="${esc(p.id)}">
      <strong>${esc(p.name)}</strong><p class="small">${t('profiles_'+p.status)} · ${fmt(p.seconds)}${p.epochs?' · '+t('profiles_rounds',p.epochs):''}</p>
      <p class="small">${p.files.map(f=>`${esc(f.name)} (${fmt(f.seconds)})`).join(' · ')}</p>
      ${p.message?`<p class="small" role="status">${esc(p.message)}</p>`:''}
      ${p.status==='draft'?`<div class="profile-actions"><select aria-label="${t('profiles_rounds','')}">${[100,200,400].map(n=>`<option value="${n}" ${n===(epochSelections.get(p.id)||200)?'selected':''}>${t('profiles_rounds',n)}</option>`).join('')}</select><button type="button" class="aktion" data-training="start" ${data.ready?'':'disabled'}>${t('profiles_train')}</button></div>`:''}
      ${['queued','running'].includes(p.status)?`<button type="button" class="sek" data-training="cancel">${t('profiles_cancel')}</button>`:''}
      ${!['queued','running'].includes(p.status)?`<div class="profile-actions"><button type="button" class="sek" data-training="remove">${t('profiles_remove')}</button></div>`:''}
    </article>`).join(''):`<p class="small">${t('profiles_none')}</p>`);
  const removed=data.removed||[];
  $('#profileTrash').hidden=!removed.length;
  $('#profileTrashItems').innerHTML=removed.map(p=>`<article class="profile-card" data-profile="${esc(p.id)}"><strong>${esc(p.name)}</strong><p class="small">${t('profiles_removed')} · ${fmt(p.seconds)}</p><button type="button" class="sek" data-training="restore">${t('profiles_restore')}</button></article>`).join('');
}
async function openProfileLibrary() {
  profileSignature='';$('#profileLibraryStatus').textContent='';
  $('#profileLibraryDlg').showModal();
  try {await refreshProfileLibrary();}catch(e){$('#profileLibraryStatus').textContent=e.message;}
  clearInterval(profilePoll);
  profilePoll=setInterval(()=>refreshProfileLibrary().catch(e=>{$('#profileLibraryStatus').textContent=e.message;}),3000);
}
document.querySelectorAll('[data-profile-library]').forEach(b=>b.addEventListener('click',openProfileLibrary));
$('#profileLibraryClose').addEventListener('click',()=>$('#profileLibraryDlg').close());
$('#profileLibraryDlg').addEventListener('close',()=>clearInterval(profilePoll));
$('#profileImportForm').addEventListener('submit',async e=>{
  e.preventDefault();const button=$('#profileImport');if(button.disabled)return;button.disabled=true;
  $('#profileLibraryStatus').textContent=t('profiles_importing');
  try {
    const body=new FormData();body.append('name',$('#profileName').value.trim());
    for(const file of $('#profileFiles').files)body.append('files',file);
    await api('/api/voice-training/import',{method:'POST',body});
    $('#profileImportForm').reset();profileSignature='';await refreshProfileLibrary();
  }catch(error){$('#profileLibraryStatus').textContent=error.message;}finally{button.disabled=false;}
});
$('#profileLibraryItems').addEventListener('change',e=>{
  const card=e.target.closest('[data-profile]');if(card&&e.target.matches('select'))epochSelections.set(card.dataset.profile,Number(e.target.value));
});
$('#profileLibraryDlg').addEventListener('click',async e=>{
  const button=e.target.closest('[data-training]');if(!button||button.disabled)return;button.disabled=true;
  const card=button.closest('[data-profile]'), action=button.dataset.training;
  try {
    const path=`/api/voice-training/${card.dataset.profile}`+(action==='remove'?'':`/${action}`);
    await api(path,{method:action==='remove'?'DELETE':'POST',...(action==='start'?{body:JSON.stringify({epochs:Number(card.querySelector('select').value)})}:{})});
    profileSignature='';await refreshProfileLibrary();refresh();
  }catch(error){$('#profileLibraryStatus').textContent=error.message;button.disabled=false;}
});
window.openInstrumentalDialog=song=>{
  instrumentalSong=song;$('#instrumentalSongTitle').textContent=song.title||song.caption;
  $('#instrumentalStatus').textContent='';$('#instrumentalStart').disabled=false;$('#instrumentalDlg').showModal();
};
$('#instrumentalClose').addEventListener('click',()=>$('#instrumentalDlg').close());
$('#instrumentalForm').addEventListener('submit',async e=>{
  e.preventDefault();const button=$('#instrumentalStart');if(button.disabled)return;button.disabled=true;
  try {
    await api(`/api/songs/${instrumentalSong.id}/instrumental`,{method:'POST',body:JSON.stringify({quality:$('#instrumentalQuality').value})});
    $('#instrumentalDlg').close();refresh();
  }catch(error){$('#instrumentalStatus').textContent=error.message;button.disabled=false;}
});
// These strings are loaded after the common language initialization.
applyI18n();
document.addEventListener('langchange',()=>{profileSignature='';if($('#profileLibraryDlg').open)refreshProfileLibrary().catch(()=>{});});
