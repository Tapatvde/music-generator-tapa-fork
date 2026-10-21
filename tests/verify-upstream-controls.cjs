// Exercise active-mode keyboard routing and the actual two-click delete handler with no real requests.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const calls=[],nodes=new Map();let keydown,modal=false;
for(const id of ['#deepPanel','#deepForm','#deepAction','#deepSource','#deepCaption','#libHeading'])nodes.set(id,{hidden:true,value:'cover',requestSubmit(){calls.push(id+':submit');},focus(){calls.push(id+':focus');}});
const shortcuts=vm.createContext({form:{requestSubmit(){calls.push('simple:submit');},prompt:{focus(){calls.push('simple:focus');}}},
 recBtn:{dispatchEvent(event){assert.equal(event.type,'click');assert.equal(event.detail,0);calls.push('record:toggle');}},
 MouseEvent:class{constructor(type,options){this.type=type;Object.assign(this,options);}},
 $:id=>nodes.get(id),document:{querySelector:()=>modal?{}:null,addEventListener(type,fn){keydown=fn;}}});
vm.runInContext(source.slice(source.indexOf('// Tastenkürzel (mit Alt'),source.indexOf('let libStats =')),shortcuts);
function press(code,extra={}){keydown({altKey:true,ctrlKey:false,metaKey:false,code,preventDefault(){},...extra});}
press('KeyG');press('KeyN');assert.deepEqual(calls.splice(0),['simple:submit','simple:focus']);
press('KeyR');assert.deepEqual(calls.splice(0),['record:toggle']);
nodes.get('#deepPanel').hidden=false;press('KeyG');press('KeyN');press('KeyB');
assert.deepEqual(calls.splice(0),['#deepForm:submit','#deepCaption:focus','#libHeading:focus']);
nodes.get('#deepAction').value='voice';press('KeyN');assert.deepEqual(calls.splice(0),['#deepSource:focus']);
modal=true;press('KeyG');press('KeyN');press('KeyB');press('KeyR');assert.deepEqual(calls,[]);
modal=false;press('KeyG',{ctrlKey:true});assert.deepEqual(calls,[]);

const actions=[],timers=[];
const deletes=vm.createContext({s:{status:'done'},id:'test',api:async(...args)=>actions.push(args),
 render(){},renderFolders(){},syncStopBtn(){},refresh(){},announce(){},t:key=>key,
 setTimeout(fn){timers.push(fn);return timers.length;},clearTimeout(){},
 CSS:{escape:x=>x},document:{querySelector:()=>null,addEventListener(){}},alert:message=>{throw Error(message);}});
const arming=source.slice(source.indexOf('let armedKey ='),source.indexOf('// ---------------------------------------------------------------- Ordner'));
const deletion=source.slice(source.indexOf('  if (a === "del") {'),source.indexOf('  refresh();\n});\n// Zwei-Klick-Bestätigung'));
vm.runInContext(arming+'\nasync function deleteClick(){ const a="del";\n'+deletion+'\n}',deletes);
(async()=>{
 await deletes.deleteClick();assert.equal(actions.length,0);assert.equal(vm.runInContext('armedKey',deletes),'song:test');
 await deletes.deleteClick();assert.equal(actions.length,1);assert.equal(actions[0][1].method,'DELETE');
 assert.equal(vm.runInContext('armedKey',deletes),null);
 await deletes.deleteClick();timers.at(-1)();assert.equal(vm.runInContext('armedKey',deletes),null);
 await deletes.deleteClick();assert.equal(actions.length,1);
 deletes.id='another';await deletes.deleteClick();assert.equal(actions.length,1);assert.equal(vm.runInContext('armedKey',deletes),'song:another');
 deletes.s.status='queued';await deletes.deleteClick();assert.equal(actions.length,2);
 console.log('PASS: Alt+G/N/B follow Simple/Deep mode; modal dialogs block background shortcuts; finished songs need two clicks on the same song; expiration resets confirmation; queue cancellation stays immediate.');
})().catch(e=>{console.error(e);process.exitCode=1;});
