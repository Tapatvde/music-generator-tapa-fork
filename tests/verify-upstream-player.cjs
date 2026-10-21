// Exercise the merged player with deferred loads and the fork's timed listening checkpoints.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const code=source.slice(source.indexOf('let playSeq = 0;'),source.indexOf('// ---------------------------------------------------------------- Einstellungen & Status'));
const nodes=new Map(),pending=new Map(),calls=[];
const ws={playing:true,time:0,isPlaying(){return this.playing;},pause(){calls.push('pause');this.playing=false;},
 load(url){return new Promise((resolve,reject)=>pending.set(url,{resolve,reject}));},
 play(){calls.push('play');this.playing=true;},playPause(){calls.push('toggle');},setTime(t){this.time=t;},getDuration(){return 80;}};
const context=vm.createContext({ws,currentId:null,played:new Set(),markPlayed(){},render(){},
 $:id=>{if(!nodes.has(id))nodes.set(id,{});return nodes.get(id);},
 window:{onSongPlayback:s=>calls.push(s.id)},document:{documentElement:{style:{setProperty(){}}}},
 ResizeObserver:class{observe(){}},Math});
vm.runInContext(code,context);
const play=(id,position=null)=>context.play({id,url:id,title:id},position);
(async()=>{
 const a=play('A');assert.equal(calls[0],'pause');
 const b=play('B',21);pending.get('B').resolve();await b;
 assert.equal(ws.time,21);assert.deepEqual(calls,['pause','B','play']);
 pending.get('A').resolve();await a;assert.deepEqual(calls,['pause','B','play']);
 const c=play('C'),d=play('D',95);pending.get('C').reject(Error('aborted'));await c;
 pending.get('D').resolve();await d;assert.equal(ws.time,79.99);
 assert.equal(calls.filter(x=>x==='C').length,0);
 await play('D',15);assert.equal(ws.time,15);assert.equal(calls.at(-1),'play');
 await play('D');assert.equal(calls.at(-1),'toggle');
 const e=play('E');pending.get('E').reject(Error('network'));await assert.rejects(e,/network/);
 console.log('PASS: previous song stops immediately; latest selection alone plays; stale cancellation ignored; genuine errors preserved; timed voice checkpoints and seek retained.');
})().catch(e=>{console.error(e);process.exitCode=1;});
