// Synthetic fake DOM only: no actual browser, network or human label storage.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8'),script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements={},blobs=new Map(),downloads=[],store={'step3-calibration-legacy':'DO_NOT_CHANGE'};let serial=0;
class Element{constructor(){this.children=[];this.value='';}append(...children){for(const child of children){this.children.push(child);if(child.id)elements[child.id]=child;}}replaceChildren(){this.children=[];}addEventListener(name,fn){this[name]=fn;}removeAttribute(name){delete this[name];}click(){downloads.push({href:this.href,name:this.download});}}
function context(){return vm.createContext({document:{getElementById:id=>elements[id]||(elements[id]=new Element()),createElement:()=>new Element()},localStorage:{getItem:k=>store[k]||null,setItem:(k,v)=>store[k]=v},Blob:class{constructor(parts){this.text=parts.join('');}},URL:{createObjectURL:b=>{const key='blob:fixture'+serial++;blobs.set(key,b);return key;},revokeObjectURL:()=>{}},setTimeout:()=>{}})}
let ctx=context();vm.runInContext(script,ctx);
const records=vm.runInContext('records',ctx),initial=vm.runInContext('exportRows()',ctx);
assert(records.length>0&&records.length<=60);assert(records.every(r=>r.face_eligible==='false'));
assert.equal(new Set(records.map(r=>r.filename)).size,records.length);assert.equal(new Set(records.map(r=>r.frame_id)).size,records.length);assert(records.every(r=>r.boundaries.length===1&&r.boundaries[0].target_result==='FAIL'&&r.boundaries[0].other_failure_count===0&&r.boundaries[0].other_hard_gates==='ALL PASS'));
assert(initial.every(r=>r.human_accept===''&&r.human_notes===''));
for(let i=0;i<records.length;i++){
  vm.runInContext('index='+i+';show()',ctx);
  assert.equal(elements.questions.children.length,records[i].boundaries.length);
  assert.equal(elements.boundaries.children.length,records[i].boundaries.length);
  assert(elements.metrics.children.every(c=>c.children.length===7));
}
const i=0;vm.runInContext('index='+i+';show()',ctx);
const g1=records[i].boundaries[0].human_gate_name;
elements['accept_'+g1].value='ACCEPT';elements['notes_'+g1].value='Synthetic "quotes", 日本語\nline';elements['accept_'+g1].change();
assert.equal(elements.questions.children.length,1);
assert.equal(elements['accept_'+g1].value,'ACCEPT');
ctx=context();vm.runInContext(script,ctx);vm.runInContext('index='+i+';show()',ctx);
assert.equal(elements['accept_'+g1].value,'ACCEPT');
assert.equal(store['step3-calibration-legacy'],'DO_NOT_CHANGE');
elements.jsonExport.onclick();const json=JSON.parse(blobs.get(downloads.at(-1).href).text);
assert.equal(json.schema_version,2);assert.equal(json.status,'HUMAN_BOUNDARY_LABELS_NOT_APPLIED');assert.equal(json.records.length,initial.length);
const label=json.records.find(r=>r.filename===records[i].filename&&r.human_gate_name===g1);assert.equal(label.human_accept,'ACCEPT');assert(label.human_notes.includes('日本語'));
elements.csvExport.onclick();const csv=blobs.get(downloads.at(-1).href).text;assert(csv.startsWith('\ufeff'));assert(csv.includes('""quotes""'));
fs.writeFileSync(process.argv[3],JSON.stringify({json,csv,fixture_only:true}));
console.log('PASS: REJECT-only UI, per-Gate questions, single failing target and ALL PASS others, reload, legacy cache isolation, JSON/CSV export');
