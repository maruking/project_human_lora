// Unit-test HTML JavaScript with a fake DOM, no browser/network/storage operations.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const file=process.argv[2],html=fs.readFileSync(file,'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let elements={},downloads=[],store={};
class Element {constructor(){this.value='';this.children=[];}append(...children){for(const child of children){this.children.push(child);if(child.id)elements[child.id]=child;}}addEventListener(name,fn){this[name]=fn;}replaceChildren(){this.children=[];}removeAttribute(name){delete this[name];}click(){downloads.push({href:this.href,name:this.download});}}
const blobs=new Map();let serial=0;
const context={document:{getElementById:id=>elements[id]||(elements[id]=new Element()),createElement:()=>new Element()},localStorage:{getItem:k=>store[k]||null,setItem:(k,v)=>store[k]=v},Blob:class{constructor(parts,opts){this.text=parts.join('');this.type=opts.type;}},URL:{createObjectURL:b=>{let k='blob:fixture'+serial++;blobs.set(k,b);return k;},revokeObjectURL:()=>{}},setTimeout:()=>{}};
vm.createContext(context);vm.runInContext(script,context);
const initial=vm.runInContext('exportRows()',context);assert(initial.length>0);
const labelFields=['human_face_usable','human_face_blurry','human_eye_occlusion','human_beauty_filter','human_visibility_problem','human_exposure_problem','human_notes'];
assert(initial.every(r=>labelFields.every(k=>r[k]==='')));
assert(elements.full.src.endsWith('_full.png'));
const presentations=vm.runInContext('presentations',context);
assert(Object.keys(presentations).length===initial.length);
assert(elements.metrics.children.length>0);
assert(elements.metrics.children[0].children[2].textContent.includes('25'));
assert(elements.gateReasons.children.length>0);
const example=initial.findIndex(r=>r.face_laplacian==='15.296');
assert(example>=0);vm.runInContext('index='+example+';show()',context);
assert(elements.gateReasons.children.some(e=>e.textContent.includes('1.589 < 1.6')));
assert(elements.gateReasons.children.some(e=>e.textContent.includes('15.296 < 50')));
vm.runInContext('index=0;show()',context);
elements.human_face_usable.value='UNSURE';elements.notes.value='Synthetic fixture "quotes", comma, 日本語\nline';vm.runInContext('save()',context);
elements.jsonExport.onclick();let json=JSON.parse(blobs.get(downloads.at(-1).href).text);
assert.equal(json.schema_version,1);assert.equal(json.status,'HUMAN_LABELS_NOT_APPLIED');assert.equal(json.records.length,initial.length);assert.equal(json.records[0].human_face_usable,'UNSURE');assert.equal(json.records[0].human_notes,elements.notes.value);
assert.deepEqual(Object.keys(json.records[0]),Object.keys(initial[0]));
// Reopening the updated UI must load a saved synthetic label under the same key.
const cacheKey=vm.runInContext('key',context);const saved=store[cacheKey];
vm.runInContext(script,vm.createContext({...context}));
assert.equal(elements.human_face_usable.value,'UNSURE');
assert.equal(store[cacheKey],saved);
elements.csvExport.onclick();let csv=blobs.get(downloads.at(-1).href).text;assert(csv.startsWith('\ufeff'));assert(csv.includes('""quotes""'));assert(csv.includes('human_notes'));
// Serialize exported rows for Python's CSV parser to verify proper roundtrip.
fs.writeFileSync(process.argv[3],JSON.stringify({json,csv,fixture_only:true}));
console.log('PASS: empty defaults, fake-DOM rendering, label persistence, JSON schema, CSV escaping; no human labels written');
