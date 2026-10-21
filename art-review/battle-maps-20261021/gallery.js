/* Offline gallery: the scene is an engine capture; overlays only explain its configuration. */
(() => {
  'use strict';
  const data = window.MAP_CATALOG;
  const $ = id => document.getElementById(id);
  const all = data.maps;
  const routes = {alm: '西队 · 胡纳普', celica: '东队 · 艾琳', joint: '两军合流'};
  const chapters = ['','第一章 · 西队行军','第二章 · 没有归来的船','第三章 · 双线推进','第四章 · 故人的另一面','第五章 · 日光仍在'];
  const colors = {deploy:'#8bb9e5',east:'#8bc8ba',object:'#e4d0a2',boss:'#d38c8c',enemy:'#bc797e',ally:'#cee3db',reinforcement:'#c5adce',exit:'#96c8a1'};
  const layer = {deploy:'show-deploy',east:'show-deploy',object:'show-objects',exit:'show-objects',enemy:'show-enemies',boss:'show-enemies',ally:'show-allies',reinforcement:'show-reinforcements'};
  const priority = {object:0,boss:1,exit:2,ally:3,deploy:4,east:4,enemy:5,reinforcement:6};
  let filtered = all.slice(), selected, kind = 'all', zoom = 'fit', loadedImage, generation = 0;
  let features = [], pinned = null, hovered = null, selectedObject = null;
  const canvas = $('tactical'), ctx = canvas.getContext('2d');
  const point = p => `(${p[0]}, ${p[1]})`;
  const same = (a,b) => a && b && a[0] === b[0] && a[1] === b[1];
  const valid = p => p && p[0]>=0 && p[1]>=0 && p[0]<selected.size[0] && p[1]<selected.size[1];
  const cell = p => valid(p) ? selected.terrain[selected.terrain_indices[p[1]*selected.size[0]+p[0]]] : null;
  const text = (id,value) => { $(id).textContent = value; };
  const element = (tag,content,className) => { const e=document.createElement(tag); if(content!==undefined)e.textContent=content; if(className)e.className=className; return e; };
  const appendLines = (id,lines) => { $(id).replaceChildren(...lines.map(line=>element('li',line))); };
  const className = u => selected.classes[String(u.class_id)] || '单位';
  const unitInfo = u => `${className(u)} · 等级${u.level} · 生命${u.hp}/${u.max_hp || u.hp} · ${point(u.position)}`;
  const operationCells = o => {
    if(o.fronts.length) return o.fronts;
    const [x,y]=o.position;
    return (o.adjacent ? [[x,y],[x-1,y],[x+1,y],[x,y-1],[x,y+1]] : [[x,y]]).filter(p=>valid(p) && cell(p).foot<255);
  };
  const operationText = o => `${o.mode}；${o.fronts.length?'指定操作格':'步兵可站的操作格'}：${operationCells(o).map(point).join('、') || '需结合通行职业判断'}。`;

  function makeFeatures() {
    features=[];
    const add=(id,position,type,label,title,description,extra={})=>{ if(valid(position))features.push({id,position,type,label,title,description,...extra}); };
    selected.deploy.forEach((p,i)=>{
      const east=(selected.deploy_by_route.celica || []).some(q=>same(p,q));
      add(`deploy-${i}`,p,east?'east':'deploy','P',`${east?'东队':'西队／单队'}部署候选格`, '部署容量与实际出阵名单以整备界面为准。');
    });
    selected.objects.forEach(o=>add(o.id,o.fronts[0] || o.position,'object',String(o.number),o.title,operationText(o),{object:o}));
    selected.enemies.forEach(u=>add(u.id,u.position,u.id===selected.boss_id?'boss':'enemy',u.id===selected.boss_id?'B':'',u.name_zh,unitInfo(u)));
    selected.npcs.forEach(u=>add(u.id,u.position,'ally','A',u.name_zh,unitInfo(u)+(u.controllable===false?'；剧情单位，不作为普通出阵队员操作。':'')));
    selected.boats.forEach(b=>add(b.id,b.position,'ally','A',b.label,`耐久${b.hp}/${b.max_hp}；延迟${b.delay}回合，预设航线见虚线。`));
    selected.reinforcements.forEach(u=>add(`reinforce-${u.id}`,u.position,'reinforcement','R',`援军 · ${u.name_zh}`,`${unitInfo(u)}；配置触发回合${selected.reinforcement_turn}，实际空位按游戏规则安排。`));
    if(selected.exit_marker.position)add('exit',selected.exit_marker.position,'exit','G',selected.exit_marker.label,'出口判定与当前关卡的护送／撤离条件一致。');
  }
  function showInspection(p) {
    const box=$('inspection'); box.replaceChildren();
    if(!p || !valid(p)) {
      box.append(element('strong','查看地图'),element('p','悬停查看地块名称、移动费用与回避；点击标记，或从下方列表选择目标。'));
      text('position-label','悬停查看地块，点击查看标记'); return;
    }
    const t=cell(p), cost=n=>n>=255?'不可通行':`${n}`;
    text('position-label',`坐标 ${point(p)}${pinned?' · 已固定':''}`);
    box.append(element('strong',`${point(p)} · ${t.name}`));
    box.append(element('p',`每格移动费用：步兵 ${cost(t.foot)} ／ 骑兵 ${cost(t.horse)} ／ 飞行 ${cost(t.fly)}；地形回避 +${t.avoid}。${t.category===15?'恢复地形：每回合恢复5生命。':''}`));
    features.filter(f=>same(p,f.position)).sort((a,b)=>priority[a.type]-priority[b.type]).forEach(f=>box.append(element('p',`${f.type==='object'?f.label+' · ':''}${f.title}：${f.description}`)));
    const atBuilding=selected.objects.filter(o=>same(o.position,p) && !same(o.fronts[0],p));
    atBuilding.forEach(o=>box.append(element('p',`${o.title}的实体／目标位置。${operationText(o)}`)));
  }
  const pixel = p => [selected.padding+(p[0]+.5)*16,selected.padding+(p[1]+.5)*16];
  function pathLine(points,color) {
    if(points.length<2)return;
    ctx.save();ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.setLineDash([4,4]);ctx.beginPath();
    points.forEach((p,i)=>{const [x,y]=pixel(p);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();ctx.restore();
  }
  function draw() {
    if(!selected || !loadedImage)return;
    const [w,h]=selected.size, pad=selected.padding;
    ctx.clearRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;ctx.drawImage(loadedImage,0,0);
    if($('show-blocked').checked) {
      for(let y=0;y<h;y++)for(let x=0;x<w;x++) {
        const t=cell([x,y]); if(t.foot<255)continue;
        ctx.fillStyle='#232c42a0';ctx.fillRect(pad+x*16,pad+y*16,16,16);
        ctx.strokeStyle='#e1d5db70';ctx.lineWidth=.7;ctx.beginPath();ctx.moveTo(pad+x*16+5,pad+y*16+5);ctx.lineTo(pad+x*16+11,pad+y*16+11);ctx.moveTo(pad+x*16+11,pad+y*16+5);ctx.lineTo(pad+x*16+5,pad+y*16+11);ctx.stroke();
      }
    }
    if($('show-grid').checked) {
      ctx.strokeStyle='#e1e9df37';ctx.lineWidth=.5;ctx.beginPath();
      for(let x=0;x<=w;x++){ctx.moveTo(pad+x*16,pad);ctx.lineTo(pad+x*16,pad+h*16);}
      for(let y=0;y<=h;y++){ctx.moveTo(pad,pad+y*16);ctx.lineTo(pad+w*16,pad+y*16);}ctx.stroke();
      ctx.font='8px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#e9efea';
      for(let x=0;x<w;x+=4)ctx.fillText(x,pad+x*16+8,pad-8);
      for(let y=0;y<h;y+=4)ctx.fillText(y,pad-10,pad+y*16+8);
    }
    ctx.strokeStyle='#e4e9de66';ctx.lineWidth=1;ctx.strokeRect(pad+.5,pad+.5,w*16-1,h*16-1);
    if($('show-allies').checked)selected.boats.forEach(b=>pathLine(b.path,'#b4d2dfbb'));
    if($('show-enemies').checked)pathLine(selected.transport_path,'#d1ada8bb');
    if(selectedObject) {
      operationCells(selectedObject).forEach(p=>{const [x,y]=pixel(p);ctx.fillStyle='#e4d0a270';ctx.fillRect(x-7,y-7,14,14);});
      if(selectedObject.fronts.length)pathLine([selectedObject.position,...selectedObject.fronts],'#e4d0a2ee');
    }
    const grouped=new Map();
    features.filter(f=>$(layer[f.type]).checked).forEach(f=>{const k=f.position.join(',');if(!grouped.has(k))grouped.set(k,[]);grouped.get(k).push(f);});
    grouped.forEach(group=>{
      group.sort((a,b)=>priority[a.type]-priority[b.type]);const f=group[0], [x,y]=pixel(f.position), r=f.type==='enemy'?3.7:6.2;
      ctx.save();ctx.shadowColor='#10191c';ctx.shadowBlur=3;ctx.fillStyle=colors[f.type];ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
      if(f.label){ctx.font='bold 8px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#16282b';ctx.fillText(f.label,x,y+.5);}
      if(group.length>1){ctx.fillStyle='#e8efef';ctx.beginPath();ctx.arc(x+5,y-5,2.5,0,Math.PI*2);ctx.fill();}ctx.restore();
    });
    const p=pinned || hovered;
    if(valid(p)) {const [x,y]=pixel(p);ctx.save();ctx.shadowColor='#d7eee3';ctx.shadowBlur=9;ctx.strokeStyle='#eff7ed';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(x,y,9,0,Math.PI*2);ctx.stroke();ctx.restore();}
  }
  function chooseFeature(f) {
    pinned=f.position;selectedObject=f.object || null;$(layer[f.type]).checked=true;
    document.querySelectorAll('.object-card').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.id===selectedObject?.id)));
    showInspection(pinned);draw();
    if(zoom!=='fit') {
      const stage=$('tactical-stage'),[x,y]=pixel(pinned),scale=Number(zoom);
      stage.scrollTo({left:Math.max(0,x*scale-stage.clientWidth/2),top:Math.max(0,y*scale-stage.clientHeight/2),behavior:'smooth'});
    }
  }
  function fillUnitList(id,units,prefix='') {
    const host=$(id);host.replaceChildren();
    if(!units.length){host.append(element('p','无', 'action-note'));return;}
    units.forEach(u=>{
      const b=element('button',`${u.id===selected.boss_id?'首领 · ':''}${u.name_zh}`);
      b.append(element('small',unitInfo(u)));b.onclick=()=>chooseFeature(features.find(f=>f.id===prefix+u.id));host.append(b);
    });
  }
  function renderDescription() {
    text('map-meta',`${chapters[selected.chapter]} / ${routes[selected.route]} / ${selected.optional?'支线':'主线'} / ${selected.size.join(' × ')} 格`);
    text('map-title',`${selected.code} · ${selected.name}`);text('map-goal',selected.goal);
    text('conditions',selected.conditions);appendLines('initial-status',selected.initial_objectives);
    appendLines('map-notes',selected.notes.length?selected.notes:['实体建筑与障碍按当前逻辑网格判断通行；选择地块可查看移动费用。']);
    text('enemy-summary',`初始敌军${selected.enemies.length}名：${Object.entries(selected.enemy_summary).map(([name,n])=>`${name}${n}名`).join('、')}。`);
    text('reinforcement-note',selected.reinforcements.length?`配置援军${selected.reinforcements.length}名，触发回合${selected.reinforcement_turn}；开启“援军口”可查看预定位置，实际落点会受占位影响。`:selected.code==='J54'?'无固定回合援军；首领半血时触发一波增援，详见胜负说明。':'无固定回合援军；召唤、剧情出现等动态变化以本关说明为准。');
    const byRoute=selected.deploy_by_route;
    text('deployment-note',Object.keys(byRoute).length?`两翼部署：西队${(byRoute.alm||[]).length}格，东队${(byRoute.celica||[]).length}格。部署点为候选位置，实际成员由整备决定。`:`部署候选格${selected.deploy.length}个；实际人数受出阵上限、队伍名册与伤情限制。剧情友军${selected.npcs.length}名另列。`);
    text('map-boundary',`可操作区域为 ${point([0,0])} 至 ${point(selected.size.map(n=>n-1))}；外围为场景背景。步兵通行图中“×”表示不可通行，以士兵／骑兵／飞行三类移动规则作对照，不代表当前人物的可达范围。`);
    const objects=$('objects');objects.replaceChildren();
    if(!selected.objects.length)objects.append(element('p','本关没有需要确认的场景对象；请按胜利条件处理敌军与剧情目标。','action-note'));
    selected.objects.forEach(o=>{
      const b=element('button',undefined,'object-card');b.dataset.id=o.id;b.setAttribute('aria-pressed','false');
      b.append(element('span',o.number,'number'));const content=element('span');
      content.append(element('strong',o.title),element('small',`${o.optional?'可选访问':'任务对象'} · ${o.mode}`,'tag'),element('small',`实体位置 ${point(o.position)}；${operationText(o)}`));
      if(o.reward_name)content.append(element('small',`首次访问补给：${o.reward_name}`));
      if(o.follows_unit)content.append(element('small','随目标单位移动；此处为开战位置。'));
      b.append(content);b.onclick=()=>chooseFeature(features.find(f=>f.id===o.id));objects.append(b);
    });
    fillUnitList('enemy-list',selected.enemies);fillUnitList('ally-list',selected.npcs);fillUnitList('reinforcement-list',selected.reinforcements,'reinforce-');
    $('boat-list').replaceChildren();selected.boats.forEach(b=>{const button=element('button',`${b.label} · 耐久${b.hp}/${b.max_hp}`);button.append(element('small',`起点 ${point(b.position)} · 延迟${b.delay}回合 · 速度${b.speed}`));button.onclick=()=>chooseFeature(features.find(f=>f.id===b.id));$('boat-list').append(button);});
    text('story',selected.story || '剧情背景与推进条件见本关任务说明。');text('next-step',selected.next || '战后返回所属队伍的当前行军节点。');
    text('rewards',selected.fixed_rewards.length?selected.fixed_rewards.join('、'):'未配置独立的固定通关补给。');
    if(selected.reward)$('rewards').append(element('br'),document.createTextNode(selected.reward));
    const source=$('source-note');source.replaceChildren(document.createTextNode(`配置快照 · ${selected.code} / 2026-10-21 · `));
    const a=element('a','查看本关配置');a.href=selected.source;source.append(a,document.createTextNode(` · SHA-256 ${selected.source_sha256.slice(0,16)}…`));
  }
  function updateZoom() {
    document.querySelectorAll('[data-zoom]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.zoom===zoom)));
    document.querySelectorAll('.stage-inner').forEach(e=>e.style.width=zoom==='fit'?'100%':`${selected.canvas[0]*Number(zoom)}px`);
  }
  function selectMap(code) {
    selected=all.find(m=>m.code===code) || filtered[0];if(!selected)return;
    $('map-select').value=selected.code;selectedObject=null;pinned=null;hovered=null;loadedImage=null;
    makeFeatures();renderDescription();showInspection(null);updateZoom();
    $('scenery').src=selected.image;$('scenery').alt=`${selected.code} ${selected.name} 当前初始场景全景`;
    canvas.width=selected.canvas[0];canvas.height=selected.canvas[1];canvas.setAttribute('aria-label',`${selected.code} ${selected.name}部署与目标标注`);
    $('full-image').href=selected.image;
    const g=++generation, img=new Image();img.onload=()=>{if(g!==generation)return;loadedImage=img;draw();};
    img.onerror=()=>{if(g===generation)text('position-label','地图加载失败，请检查文件完整性。');};img.src=selected.image;
    const index=filtered.indexOf(selected);$('previous').disabled=index<=0;$('next').disabled=index>=filtered.length-1;
    document.querySelectorAll('.map-card').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.code===selected.code)));
    try {const u=new URL(location.href);u.searchParams.set('map',selected.code);history.replaceState(null,'',u);}catch(_e){}
  }
  function renderCatalog() {
    const host=$('map-catalog');host.replaceChildren();
    for(let chapter=1;chapter<=5;chapter++) {
      const list=filtered.filter(m=>m.chapter===chapter);if(!list.length)continue;
      const section=element('section'),heading=element('div',undefined,'chapter-heading');
      heading.append(element('h3',chapters[chapter]),element('span',`${list.length}张`));section.append(heading);
      const grid=element('div',undefined,'catalog');
      list.forEach(m=>{
        const b=element('button',undefined,'map-card');b.dataset.code=m.code;b.setAttribute('aria-pressed',String(selected?.code===m.code));
        const frame=element('span',undefined,'map-thumb'),image=element('img');image.src=m.thumbnail;image.alt=`${m.code} ${m.name}缩略图`;image.loading='lazy';frame.append(image);
        const body=element('span',undefined,'map-card-body');body.append(element('strong',`${m.code} · ${m.name}`),element('small',`${routes[m.route]} · ${m.optional?'支线':'主线'} · ${m.size.join(' × ')}格`),element('small',`${m.deploy.length}个部署候选格 · ${m.enemies.length}名初始敌军`));
        b.append(frame,body);b.onclick=()=>{selectMap(m.code);$('map-viewer').scrollIntoView({behavior:'smooth',block:'start'});};grid.append(b);
      });section.append(grid);host.append(section);
    }
    text('catalog-count',`当前显示${filtered.length} / ${all.length}张 · 按章节排列`);
  }
  function filter(preferred) {
    const query=$('search').value.trim().toLowerCase();
    filtered=all.filter(m=>($('chapter').value==='all'||String(m.chapter)===$('chapter').value)&&($('route').value==='all'||m.route===$('route').value)&&(kind==='all'||m.optional===(kind==='side'))&&(!query||[m.code,m.name,m.node,m.goal,...m.notes].join(' ').toLowerCase().includes(query)));
    $('map-select').replaceChildren(...filtered.map(m=>{const o=element('option',`${m.code} · ${m.name}`);o.value=m.code;return o;}));
    $('map-select').disabled=!filtered.length;$('no-results').hidden=!!filtered.length;$('map-content').hidden=!filtered.length;
    renderCatalog();
    if(filtered.length)selectMap(filtered.some(m=>m.code===(preferred || selected?.code))?(preferred || selected.code):filtered[0].code);
    else {text('map-meta','筛选结果');text('map-title','没有符合条件的地图');text('map-goal','请调整章节、队伍或搜索关键词。');$('previous').disabled=true;$('next').disabled=true;}
  }
  function step(delta) {const index=filtered.indexOf(selected)+delta;if(index>=0 && index<filtered.length)selectMap(filtered[index].code);}
  function clearPin() {pinned=null;selectedObject=null;document.querySelectorAll('.object-card').forEach(b=>b.setAttribute('aria-pressed','false'));showInspection(hovered);draw();}
  function pointerCell(e) {const r=canvas.getBoundingClientRect();return [Math.floor(((e.clientX-r.left)*canvas.width/r.width-selected.padding)/16),Math.floor(((e.clientY-r.top)*canvas.height/r.height-selected.padding)/16)];}
  canvas.addEventListener('pointermove',e=>{hovered=pointerCell(e);if(!pinned)showInspection(hovered);draw();});
  canvas.addEventListener('pointerleave',()=>{hovered=null;if(!pinned)showInspection(null);draw();});
  canvas.addEventListener('click',e=>{const p=pointerCell(e);if(!valid(p)){clearPin();return;}const f=features.filter(f=>same(p,f.position) && $(layer[f.type]).checked).sort((a,b)=>priority[a.type]-priority[b.type])[0];if(f)chooseFeature(f);else{clearPin();pinned=p;showInspection(p);draw();}});
  ['chapter','route'].forEach(id=>$(id).addEventListener('change',()=>filter()));$('search').addEventListener('input',()=>filter());
  $('map-select').addEventListener('change',e=>selectMap(e.target.value));
  document.querySelectorAll('[data-kind]').forEach(b=>b.onclick=()=>{kind=b.dataset.kind;document.querySelectorAll('[data-kind]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));filter();});
  document.querySelectorAll('[data-zoom]').forEach(b=>b.onclick=()=>{zoom=b.dataset.zoom;updateZoom();});
  document.querySelectorAll('.overlay-controls input').forEach(c=>c.addEventListener('change',draw));
  $('previous').onclick=()=>step(-1);$('next').onclick=()=>step(1);
  $('reset-filters').onclick=()=>{$('chapter').value='all';$('route').value='all';$('search').value='';kind='all';document.querySelectorAll('[data-kind]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.kind==='all')));filter();};
  $('download-image').onclick=()=>{const a=element('a');a.href=selected.image;a.download=`${selected.code}-${selected.name}.png`;a.click();};
  document.addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey||e.altKey||/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)||!filtered.length)return;if(e.key==='ArrowLeft'){e.preventDefault();step(-1);}if(e.key==='ArrowRight'){e.preventDefault();step(1);}if(e.key.toLowerCase()==='g'){$('show-grid').checked=!$('show-grid').checked;draw();}if(e.key==='Escape')clearPin();});
  // Keep the read-only state observable for the local review check.
  Object.defineProperty(window,'mapGalleryState',{get:()=>({selected:selected?.code,visible:filtered.length,imageReady:!!loadedImage,features:features.length})});
  filter(new URLSearchParams(location.search).get('map') || 'M11');
})();
