// Evaluate the actual dictionaries and fork fallbacks without UI/API side effects.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'../static'),select={options:[],add(option){this.options.push(option);}},context=vm.createContext({
  localStorage:{getItem:()=>null,setItem(){}},navigator:{language:'de-DE'},Option:function(text,value){this.text=text;this.value=value;},
  document:{documentElement:{},querySelectorAll:()=>[],querySelector:selector=>selector==='#uiLang'?select:null,dispatchEvent(){}},Event:function(){}});
vm.runInContext(fs.readFileSync(path.join(root,'i18n.js'),'utf8'),context);
for(const file of ['voices.js','profile-library.js','mix-levels.js','deep.js']){
  const source=fs.readFileSync(path.join(root,file),'utf8'),pattern=/Object\.assign\(I18N\.(?:de|en),\s*\{/g;
  let match;while((match=pattern.exec(source))){const end=source.indexOf('\n});',match.index);assert.ok(end>match.index);vm.runInContext(source.slice(match.index,end+4),context);pattern.lastIndex=end+4;}
}
assert.equal(select.options.length,12);
for(const option of select.options){
  vm.runInContext(`setLang(${JSON.stringify(option.value)})`,context);
  assert.equal(context.document.documentElement.lang,option.value);
  for(const key of ['voice_button','profiles_manage','deep_full_submit','deep_from_preview','mix_title','upd_fork_current','dit_xl']){
    const value=vm.runInContext(`t(${JSON.stringify(key)},'version')`,context);assert.notEqual(value,key,key);assert.equal(typeof value,'string');
  }
}
vm.runInContext("setLang('unknown')",context);assert.equal(context.document.documentElement.lang,'en');
vm.runInContext("setLang('toString')",context);assert.equal(context.document.documentElement.lang,'en');
console.log('PASS: 12 language options; translated core and DE/EN fork fallbacks; Deep/voice/profile/mix/updater labels; invalid language safely falls back.');
