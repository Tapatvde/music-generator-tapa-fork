// Synthetic audio and browser API doubles only: this suite never opens a microphone.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const measurement=source.slice(source.indexOf('const REC_MAX ='),source.indexOf('const recBtn ='));
const music=vm.createContext({Float32Array,Math});vm.runInContext(measurement,music);
const tone=new Float32Array(32000);for(let i=0;i<tone.length;i++)tone[i]=.2*Math.sin(2*Math.PI*220*i/16000);
const measured=music.measureMelody(tone,16000);
assert.ok(measured && measured.range<.5 && measured.legato>.9 && measured.rate<2);
assert.equal(music.measureMelody(new Float32Array(32000),16000),null);
const description=music.describeIdea(measured,'Warm nostalgic glockenspiel, humming and whistles','A minor');
assert.match(description,/lullaby/);assert.match(description,/warm/);assert.doesNotMatch(description,/glockenspiel|humming|whistles/);

const controls={title:{value:'Keep title'},prompt:{value:'Old prompt'},style:{value:'country'},lyrics:{value:'Keep my lyrics'},
 instrumental:{checked:false},vocal_language:{value:'de',options:[{value:'en'},{value:'de'}]},bpm:{value:84},duration:{value:240,min:10,max:300},keyscale:{},timesignature:{}};
const states=[];
const analysis=vm.createContext({form:controls,FormData:class{append(){}},
 api:async()=>({caption:'Warm guitar',lyrics:'Detected text',bpm:99,duration:8,keyscale:'A minor',timesignature:3,vocal_language:'en'}),
 describeIdea:music.describeIdea,randomTitle:()=> 'Random title',syncLyrics(){},styleParts:()=>['country'],
 extractStyleTags:()=>['guitar'],syncStyleChips(){},showDur(){},setSelect:(node,value)=>node.value=value,
 $:()=>({}),t:key=>key,dzState:(...args)=>states.push(args),window:{scrollTo(){}},Math,Set});
vm.runInContext(source.slice(source.indexOf('async function analyzeFile('),source.indexOf('dz.addEventListener("click"')),analysis);

function capture(options={}){
 const classes=new Set(),attrs={},handlers={},timers=[],errors=[];let requests=0,stops=0,starts=0,now=0,modeSwitches=0;
 const stream={getTracks:()=>[{stop(){stops++;}}]};
 class Recorder{
  constructor(){if(options.constructorFails)throw Error('constructor');this.state='inactive';this.mimeType='audio/webm';this.handlers={};}
  addEventListener(type,fn){this.handlers[type]=fn;}
  start(){if(options.startFails)throw Error('start');starts++;this.state='recording';}
  stop(){this.state='inactive';}
 }
 const button={classList:{contains:x=>classes.has(x),add:x=>classes.add(x),remove:(...xs)=>xs.forEach(x=>classes.delete(x))},
 style:{setProperty(){},removeProperty(){}},setAttribute:(key,value)=>attrs[key]=value,addEventListener:(type,fn)=>handlers[type]=fn};
 const panel={hidden:!options.deep};
 const context=vm.createContext({$:id=>id==='#recBtn'?button:id==='#recTime'?{}:id==='#deepPanel'?panel:{click(){panel.hidden=true;modeSwitches++;}},
 navigator:{mediaDevices:{getUserMedia:()=>{requests++;return options.permission?options.permission(stream):Promise.resolve(stream);}}},
 window:{MediaRecorder:Recorder,addEventListener(){}},MediaRecorder:Recorder,performance:{now:()=>now},
 setTimeout(fn){timers.push(fn);return timers.length;},clearTimeout(){},setInterval(){return 1;},clearInterval(){},
 dzState:(...args)=>errors.push(args),t:key=>key,announce(){},Blob,File:class{},Float32Array,DataView,ArrayBuffer,Math});
 vm.runInContext(measurement+source.slice(source.indexOf('const recBtn ='),source.indexOf('dz.addEventListener("keydown"')),context);
 return {context,classes,attrs,handlers,timers,stream,errors,setNow:t=>now=t,stats:()=>({requests,stops,starts,modeSwitches})};
}

(async()=>{
 const original={title:controls.title.value,style:controls.style.value,lyrics:controls.lyrics.value,duration:controls.duration.value,instrumental:controls.instrumental.checked,language:controls.vocal_language.value};
 await analysis.analyzeFile({},measured);
 assert.deepEqual({title:controls.title.value,style:controls.style.value,lyrics:controls.lyrics.value,duration:controls.duration.value,instrumental:controls.instrumental.checked,language:controls.vocal_language.value},original);
 assert.equal(controls.bpm.value,99);assert.equal(controls.keyscale.value,'A minor');assert.equal(controls.timesignature.value,'3');
 await analysis.analyzeFile({});assert.equal(controls.title.value,'Random title');assert.equal(controls.duration.value,10);assert.equal(controls.style.value,'country, guitar');

 let permission;const delayed=capture({permission:()=>new Promise(resolve=>permission=resolve)});
 delayed.classes.add('held');const pending=delayed.context.recStart();await delayed.context.recStart();
 assert.equal(delayed.stats().requests,1);delayed.context.recStop();permission(delayed.stream);await pending;
 assert.equal(delayed.stats().starts,0);assert.equal(delayed.stats().stops,1);

 const denied=capture({permission:()=>Promise.reject(Error('permission'))});denied.classes.add('held');await denied.context.recStart();
 assert.equal(denied.errors.at(-1)[1],'rec_denied');assert.equal(denied.classes.has('held'),false);
 for(const options of [{constructorFails:true},{startFails:true}]){
  const failed=capture(options);failed.classes.add('held');await failed.context.recStart();assert.equal(failed.stats().stops,1);assert.equal(failed.attrs['aria-pressed'],undefined);
 }

 const keyboard=capture({deep:true});keyboard.classes.add('held');await keyboard.context.recStart();
 assert.equal(keyboard.stats().modeSwitches,1);assert.equal(keyboard.attrs['aria-pressed'],'true');
 keyboard.setNow(1000);keyboard.handlers.keyup({key:'Enter',preventDefault(){}});await keyboard.context.recFinish();
 keyboard.handlers.click({detail:0});assert.equal(keyboard.timers.length,0);assert.equal(keyboard.stats().requests,1);assert.equal(keyboard.stats().stops,1);

 const toggle=capture();toggle.handlers.click({detail:0});toggle.handlers.click({detail:0});toggle.timers[0]();
 assert.equal(toggle.stats().requests,0);

 let closed=0;class BrokenAudio{async decodeAudioData(){throw Error('decode');}async close(){closed++;}}
 const encoding=capture();encoding.context.window.AudioContext=BrokenAudio;
 await assert.rejects(encoding.context.toWav({arrayBuffer:async()=>new ArrayBuffer(1)}),/decode/);assert.equal(closed,1);
 class Audio{constructor(){this.sampleRate=48000;}async decodeAudioData(){return {length:4,numberOfChannels:2,sampleRate:48000,getChannelData:()=>new Float32Array([.1,-.2,.3,0])};}async close(){closed++;}}
 encoding.context.window.AudioContext=Audio;const encoded=await encoding.context.toWav({arrayBuffer:async()=>new ArrayBuffer(1)});
 const header=new DataView(encoded.wav);assert.equal(header.getUint16(22,true),1);assert.equal(header.getUint32(24,true),48000);assert.equal(encoded.wav.byteLength,52);assert.equal(closed,2);
 console.log('PASS: synthetic melody measurement; idea import preserves title/lyrics/style/duration; file analysis retained; pending permission cancellation and duplicate prevention; denial/start failures release tracks; keyboard stop does not restart; screenreader toggle cancels; Deep mode switches visibly; audio contexts always close; mono WAV encoding.');
})().catch(e=>{console.error(e);process.exitCode=1;});
