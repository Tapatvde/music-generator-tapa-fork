// Exercise the actual browser helpers with synthetic settings and connection data.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(require('node:path').join(__dirname,'../static/app.js'),'utf8');
const timeLine=source.split('\n').find(line=>line.startsWith('const genTime ='));
const time=vm.createContext({fmt:seconds=>seconds,Date,isFinite});vm.runInContext(timeLine,time);
time.song={created_at:'2026-11-11T00:00:00Z',started_at:'2026-11-11T00:00:10Z',finished_at:'2026-11-11T00:00:15Z'};
assert.equal(vm.runInContext('genTime(song)',time),5);
time.song.result_meta={generation_seconds:3};assert.equal(vm.runInContext('genTime(song)',time),3);
const expression=source.match(/\$\{(exportFmt === "mp3"[^\n]+?)\}<\/a>/)[1];
for(const [file,format,label] of [['example.wav','wav','WAV'],['example.wav','mp3','MP3'],['example.flac','wav','FLAC']]){
  assert.equal(vm.runInNewContext(expression,{exportFmt:format,s:{file}}),label);
}
const fields=Object.fromEntries(['server_url','lm_url','timeout_minutes','songs_dir','dit','lm_device','highs','export_format'].map(key=>[key,{value:({timeout_minutes:'30',highs:'on',export_format:'mp3',dit:'xl',lm_device:'cpu'})[key]||''}]));
let payload,events=0;
const settings=vm.createContext({sf:fields,api:async(path,options)=>{payload=JSON.parse(options.body);return payload;},document:{dispatchEvent(){events++;}},Event:class{},alert:()=>assert.fail('unexpected settings error'),$:()=>({click(){}})});
vm.runInContext(source.slice(source.indexOf('const saveSettings ='),source.indexOf('// Anordnung:')),settings);
const nodes=new Map();let connection;
function node(id){if(!nodes.has(id))nodes.set(id,{hidden:false,value:'',children:[],replaceChildren(...values){this.children=values;}});return nodes.get(id);}
const qr=vm.createContext({$:node,remoteSel:node('#remoteSel'),document:{createElement:()=>({})},URLSearchParams,qrcode:()=>({addData(value){connection=value;},make(){},createSvgTag(){return '<svg></svg>';}})});
vm.runInContext(source.slice(source.indexOf('function showRemote('),source.indexOf('async function remoteCall(')),qr);
qr.data={enabled:true,addresses:['http://example-host:8767','http://192.0.2.1:8767'],token:'synthetic-token'};
vm.runInContext('showRemote(data)',qr);
const url=new URL(connection);assert.equal(url.protocol,'musicgenerator:');assert.equal(url.searchParams.get('server'),'http://example-host:8767');assert.equal(url.searchParams.get('token'),'synthetic-token');
assert.equal(nodes.get('#remoteInfo').hidden,false);
qr.data={enabled:false,addresses:[],token:''};vm.runInContext('showRemote(data)',qr);assert.equal(nodes.get('#remoteInfo').hidden,true);
(async()=>{await vm.runInContext('saveSettings()',settings);assert.equal(payload.highs,'on');assert.equal(payload.export_format,'mp3');assert.equal(payload.lm_device,'cpu');assert.equal(events,1);process.stdout.write('PASS: started-time fallback, actual export labels, settings notification, QR connection data and remote-off state.\n');})().catch(error=>{process.stderr.write(error.stack);process.exitCode=1;});
