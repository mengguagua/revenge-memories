// Static artifact and event-model checks; no browser, speaker or UI automation.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const page = path.join(root, 'actual/reports/sfx-20261024/index.html');
const html = fs.readFileSync(page, 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
const checks = [];
function check(ok, label) { assert.ok(ok, label); checks.push(label); }
class Element extends EventTarget {
  constructor() { super(); this.value=''; this.textContent=''; this.hidden=false; this.dataset={}; this.classes=new Set(); this.classList={add:x=>this.classes.add(x),remove:x=>this.classes.delete(x)}; }
}
let autoEnd = true;
const played = [];
class Audio extends Element {
  constructor(id) { super(); this.id=id; this.paused=true; this.ended=false; this.volume=1; this.currentTime=0; this.blocked=false; }
  play() {
    if(this.blocked)return Promise.reject(new Error('simulated autoplay rejection'));
    this.paused=false; this.ended=false; played.push(this.id); this.dispatchEvent(new Event('play'));
    if(autoEnd)setTimeout(()=>{if(!this.paused){this.paused=true;this.ended=true;this.dispatchEvent(new Event('ended'));}},2);
    return Promise.resolve();
  }
  pause() { if(!this.paused){this.paused=true;this.dispatchEvent(new Event('pause'));} }
}
const ids = new Map(), articles = [], players = [], buttons = [];
for(const match of html.matchAll(/<article id="request-([0-9A-F]+)" data-search="([^"]*)" data-sha="([^"]*)"/g)) {
  const request=match[1], a=new Element(); a.dataset={request,search:match[2],sha:match[3]};
  const fields={'.verdict':new Element(),'.note':new Element(),'.review-state':new Element()}; fields['.verdict'].value='pending';
  a.querySelector=x=>fields[x]; articles.push(a);
  const b=new Element(); b.closest=()=>a; buttons.push(b);
  for(const side of ['original','new']){const p=new Audio(side+'-'+request);players.push(p);ids.set(p.id,p);}
}
for(const id of ['search','play-all','stop','volume','volume-value','playback','progress'])ids.set(id,new Element());
ids.get('volume').value='65';
const document={querySelectorAll:s=>s==='article'?articles:s==='audio'?players:s==='button.compare'?buttons:[],getElementById:id=>ids.get(id)};
const storage = new Map();
const context=vm.createContext({document,localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},setTimeout:(fn,ms)=>setTimeout(fn,Math.min(ms,3)),Promise});
vm.runInContext(script,context);
async function main(){
  check(articles.length===41 && players.length===82,'41 original/new pairs with 82 native players');
  const missing=[];
  for(const match of html.matchAll(/(?:src|href)="([^"#]+)"/g)){
    const target=match[1].split('#')[0];
    if(!/^(https?:|data:)/.test(target)&&!fs.existsSync(path.resolve(path.dirname(page),target)))missing.push(target);
  }
  check(!missing.length,'every comparison media/link target exists');
  check(players.every(p=>p.volume===.65),'both sides start at the same 65 percent gain');
  await vm.runInContext('compare([articles[0]])',context);
  check(played.slice(-2).join(',')==='original-12,new-12','one-click comparison plays original then replacement');
  check(articles.every(a=>a.querySelector('.verdict').value==='pending'),'playback never declares listening approval');
  autoEnd=false;
  const waiting=vm.runInContext('compare([articles[0]])',context);
  await ids.get('new-03').play(); await waiting;
  check(!ids.get('new-03').paused,'manual playback safely takes over from a comparison queue');
  vm.runInContext('halt()',context);
  check(players.every(p=>p.paused),'stop cancels queued and manual playback');
  articles[0].querySelector('.verdict').value='accepted';
  articles[0].querySelector('.verdict').dispatchEvent(new Event('change'));
  const saved=JSON.parse(storage.get('revenge-sfx-audition-v1'));
  check(saved['12'].verdict==='accepted'&&saved['12'].sha===articles[0].dataset.sha,'only manual judgement persists with the current asset hash');
  autoEnd=true; ids.get('original-12').blocked=true;
  await vm.runInContext('compare([articles[0]])',context);
  check(ids.get('playback').textContent.includes('阻止连续播放'),'autoplay failures show a useful fallback message');
  const output={passed:true,checks,browser_visual_checked:false,actual_media_played:false,method:'Static authored HTML and Node EventTarget media-state mocks; no browser access',missing_links:missing};
  fs.writeFileSync(path.join(root,'actual/reports/audio-scene-review-20261024/comparison-page-checks.json'),JSON.stringify(output,null,2)+'\n');
  console.log('AUDIO_COMPARISON_PAGE',checks.length,'checks passed');
}
main().catch(e=>{console.error(e);process.exitCode=1});
