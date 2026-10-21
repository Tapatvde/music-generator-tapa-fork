// Check the real click handler without enqueuing GPU work in the user library.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const script=fs.readFileSync(require('node:path').join(__dirname,'../static/deep.js'),'utf8');
const handler=script.slice(script.indexOf('const pendingDeepFull='),script.indexOf("$('#modeSwitch').addEventListener"));
const status={textContent:''},calls=[];let release,refreshes=0,error='';
const context={window:{},Set,JSON,render(){},t:key=>key,
  $:selector=>{assert.equal(selector,'#deepStatus');return status;},
  api:async(url,options)=>{calls.push({url,body:JSON.parse(options.body)});await new Promise(resolve=>release=resolve);},
  refresh:async()=>{refreshes++;},alert:message=>{error=message;}};
vm.runInNewContext(handler,context);
const saved={source_song_id:'original-full',caption:'Warm arrangement',lyrics:'[verse]\nHello',chords:'Am F',preview:true,preview_start:12,preview_seconds:20,source_strength:.9,sound_model:'xl',seed:1234,mix_levels:{vocals:true,backing:false}};
const song={id:'short-preview',status:'done',params:{deep:saved}},before=JSON.stringify(song);
(async()=>{
  const first=context.window.createDeepFullSong(song);
  assert.equal(context.window.deepFullPending(song.id),true);
  await context.window.createDeepFullSong(song);assert.equal(calls.length,1);
  assert.equal(calls[0].url,'/api/deep/generate');
  assert.deepEqual(calls[0].body,{...saved,preview:false,preview_start:0});
  release();await first;assert.equal(refreshes,1);assert.equal(status.textContent,'deep_queued');
  assert.equal(JSON.stringify(song),before);assert.equal(context.window.deepFullPending(song.id),false);
  context.api=async()=>{throw new Error('Original missing');};
  await context.window.createDeepFullSong(song);assert.equal(error,'Original missing');assert.equal(context.window.deepFullPending(song.id),false);
  await context.window.createDeepFullSong({...song,status:'running'});assert.equal(calls.length,1);
  console.log('PASS: full original, stored model/settings, preview retained, duplicate click blocked, error recovery, unfinished preview rejected.');
})().catch(error=>{console.error(error);process.exitCode=1;});
