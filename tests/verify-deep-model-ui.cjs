// Exercise the actual Deep UI and request handler without the real GPU queue.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const nodes=new Map(),options=new Map(),requests=[];
function node(id){
  if(!nodes.has(id))nodes.set(id,{value:'',checked:false,disabled:false,hidden:false,textContent:'',handlers:{},
    addEventListener(type,fn){this.handlers[type]=fn;},setAttribute(){},scrollIntoView(){},
    querySelectorAll(){return [];},querySelector(selector){return option(selector);}});
  return nodes.get(id);
}
function option(selector){if(!options.has(selector))options.set(selector,{disabled:false,textContent:''});return options.get(selector);}
const original={id:'original',status:'done',title:'Original',caption:'Warm',lyrics:'[verse]\nHello',params:{duration:260},result_meta:{duration:260,bpm:84}};
let settings={dit:'xl',dit_xl_available:true},release=null;
const context=vm.createContext({I18N:{de:{dit_xl:'XL · SFT 4B',dit_standard:'Standard · SFT 2B'},en:{}},window:{mixLevelRequest:()=>({vocals:true}),openVoiceDialog:async()=>{},setMixLevels(){}},
  $:node,document:{body:{classList:{toggle(){}}},addEventListener(){}},
  localStorage:{getItem(){return null;},setItem(){}},applyI18n(){},render(){},refresh:async()=>{},esc:value=>String(value),fmt:value=>String(value),
  api:async(url,options)=>{
    if(url==='/api/songs')return [original];if(url==='/api/voices')return {profiles:[]};if(url==='/api/settings')return settings;
    requests.push(JSON.parse(options.body));if(release===true)await new Promise(resolve=>release=resolve);return {id:'test'};
  },alert:message=>{throw Error(message);},Promise,Set,JSON,Number,String});
context.t=(key,...args)=>{const value=context.I18N.de[key];return typeof value==='function'?value(...args):value||key;};
for(const [id,value] of Object.entries({deepSoundModel:'default',deepAction:'cover-nofsq',deepSource:'original',deepStrength:'90',deepSeconds:'20',deepStart:'0',deepMeter:'4'}))node('#'+id).value=value;
node('#deepPreview').checked=true;
vm.runInContext(fs.readFileSync(require('node:path').join(__dirname,'../static/deep.js'),'utf8'),context);
(async()=>{
  assert.equal(node('#deepSubmit').disabled,true);
  await vm.runInContext('setDeepMode(true)',context);
  if(node('#deepStatus').textContent)throw new Error(node('#deepStatus').textContent);
  assert.equal(node('#deepModelStatus').textContent,'Für diesen Auftrag: XL · SFT 4B');
  assert.equal(node('#deepRequestSummary').textContent,'Vorschau · XL · SFT 4B · 20');
  node('#deepSoundModel').value='standard';vm.runInContext('syncDeepControls()',context);
  const submit=()=>node('#deepForm').handlers.submit({preventDefault(){}});
  release=true;const pending=submit();await submit();assert.equal(requests.length,1);
  assert.equal(requests[0].sound_model,'standard');assert.equal(settings.dit,'xl');
  release();await pending;
  node('#deepPreview').checked=false;vm.runInContext('syncDeepControls()',context);
  assert.equal(node('#deepRequestSummary').textContent,'Vollfassung · Standard · SFT 2B · 260');
  await submit();assert.equal(requests[1].preview,false);
  settings={dit:'standard',dit_xl_available:false};node('#deepSoundModel').value='xl';await vm.runInContext('loadDeepData()',context);
  assert.equal(option('option[value="xl"]').disabled,true);assert.equal(node('#deepSubmit').disabled,true);
  await submit();assert.equal(requests.length,2);
  node('#deepAction').value='voice';vm.runInContext('syncDeepControls()',context);
  assert.equal(node('#deepRemixOptions').hidden,true);assert.equal(node('#deepRequestSummary').textContent,'');
  await submit();assert.equal(requests.length,2);
  console.log('PASS: visible default XL, explicit Standard request without changing default, whole-song length, duplicate submit blocked, missing XL blocked, RVC bypass.');
})().catch(error=>{console.error(error);process.exitCode=1;});
