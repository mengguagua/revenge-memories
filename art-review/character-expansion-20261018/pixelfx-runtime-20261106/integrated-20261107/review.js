(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const clips = window.BATTLE_REVIEW || [];
  const player = $('pair');
  const original = $('old-audio');
  const category = $('category');
  const cases = $('case-select');
  const search = $('case-search');
  const seekbar = $('scrub');
  const canvas = [$('before'), $('after')];
  const contexts = canvas.map(node => node.getContext('2d'));
  const wells = canvas.map(node => node.parentElement);
  const viewButtons = [...document.querySelectorAll('[data-view]')];
  const quick = [
    ['cinema-hunapu-sword-advanced','胡纳普 · 进阶剑必杀'],
    ['cinema-eileen-sword-advanced','艾琳 · 进阶剑必杀'],
    ['d29883179289','美杜莎'],['550bfa9abfce','石翼兽'],
    ['cyclops-pulse','独眼傀儡'],['owl-rake','飞枭傀儡'],['prometheus-anchor','普罗米修斯傀儡']
  ];
  const groups = [
    ['sword','剑击'],['lightning-sword','雷剑'],['lance','长枪'],['javelin','投枪'],
    ['archery','弓箭'],['magic','魔法'],['support','治疗与支援'],
    ['mechanical','机械傀儡'],['monster','非人敌军'],['map','地图演出']
  ];
  let clip;
  let mode = innerWidth <= 690 ? 'native' : 'close';
  let manualMode = false;
  let poster;
  let ready = false;
  let intendedTime = 0;
  let animate = 0;
  let mediaRequest;
  let showOriginalDuration = false;
  let objectUrls = [];
  const width = 592;
  const fps = 60;

  if (!clips.length) {
    $('status').textContent = '实机视频索引未载入。';
    return;
  }
  const criticalCount = clips.filter(row => row.kind === 'cinema').length;
  const monsterCount = clips.filter(row => row.kind === 'monster').length;
  $('coverage').textContent = clips.length + ' 段实录 · ' + criticalCount + ' 段主角必杀 · ' + monsterCount + ' 段非人敌军招式';
  const technique = row => row.title.split(' · ').at(-1);
  const group = row => {
    if (row.kind !== 'cinema') return row.kind;
    return ({剑击:'sword',弓箭:'archery'})[technique(row)] || 'magic';
  };
  const names = new Map(groups);
  const classOrder = [14,8,9,10,1,4,7,6,2,22,3,5,12,13,20,16,11,15,19,18,17,21];
  const priority = new Map(classOrder.map((id,i)=>[id,i]));
  const projectileGroups = new Set(['archery','javelin','lightning-sword']);
  function sectionOf(row) {
    const kind = group(row);
    if (kind === 'magic' || kind === 'support') return technique(row);
    if (kind === 'monster' || kind === 'mechanical') return row.title.split(' · ')[0];
    if (row.kind === 'cinema') return '主角必杀';
    if (kind === 'sword') return '常规剑击';
    if (kind === 'lance' || kind === 'javelin') {
      if ([1,4,7].includes(row.classId)) return '骑兵';
      if ([3,5].includes(row.classId)) return '飞行单位';
      return '步兵';
    }
    if (projectileGroups.has(kind)) return row.title.startsWith('胡纳普') || row.title.startsWith('艾琳')
      ? '主角' : '普通职业';
    return names.get(kind);
  }
  const matches = () => {
    const tokens = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    return clips.filter(row => {
      const label = (row.title + ' ' + names.get(group(row)) + (row.side === 'enemy' ? ' 敌方' : '')).toLowerCase();
      return tokens.every(token => label.includes(token));
    });
  };

  function fillCategories(value) {
    const rows = matches();
    category.replaceChildren();
    if (search.value.trim()) category.append(new Option('全部匹配','all'));
    for (const [key,label] of groups) {
      if (rows.some(row => group(row) === key)) category.append(new Option(label,key));
    }
    if ([...category.options].some(option => option.value === value)) category.value = value;
  }
  fillCategories();

  function fillCases(value) {
    const choices = matches().filter(row => category.value === 'all' || group(row) === category.value);
    const rank = row => row.kind === 'cinema' ? 1 : 0;
    choices.sort((a,b) => (rank(a)-rank(b))
      || (priority.get(a.classId)??99)-(priority.get(b.classId)??99)
      || a.title.localeCompare(b.title,'zh-CN'));
    const sections = new Map();
    cases.replaceChildren();
    const hasValue = choices.some(row => row.key === value);
    if (!hasValue && search.value.trim()) {
      const prompt = new Option(choices.length ? '选择匹配的招式' : '没有匹配的招式','');
      prompt.disabled = true;
      cases.append(prompt);
    }
    for (const row of choices) {
      const label = (category.value === 'all' ? names.get(group(row)) + ' · ' : '') + sectionOf(row);
      if (label && !sections.has(label)) {
        const section = document.createElement('optgroup');
        section.label = label;
        sections.set(label, section);
        cases.append(section);
      }
      (sections.get(label) || cases).append(new Option(row.title,row.key));
    }
    if (hasValue) cases.value = value;
    cases.disabled = !choices.length;
    $('match-count').textContent = search.value.trim() ? choices.length + ' 个匹配' : '';
  }

  function duration() {
    return (showOriginalDuration ? clip.beforeDuration : clip.afterDuration) ?? clip.duration;
  }

  function updateDuration() {
    seekbar.max = Math.min(clip.frames-1,Math.ceil(duration()*fps));
    const button = $('full-duration');
    button.setAttribute('aria-pressed',String(showOriginalDuration));
    button.textContent = showOriginalDuration ? '按新版时长播放' : '查看旧版全程';
    $('status').textContent = clip.afterDuration
      ? (showOriginalDuration ? '两版同时开始。新版结束后，右侧停在最后一帧。' : '两版同时开始，默认播到新版结束。')
      : '两侧在命中时对齐。可逐帧查看，并切换试听一侧。';
  }

  function crop() {
    if (mode === 'phone') return [0,0,592,240];
    return clip.kind === 'cinema' || clip.kind === 'map' ? [116,0,406,240] : [191,0,256,240];
  }

  function redraw() {
    if (!clip) return;
    const [x,y,w,h] = crop();
    wells[0].closest('.screens').classList.toggle('stacked',mode==='close' && w>300);
    const fromVideo = ready && player.readyState >= 2;
    const image = fromVideo ? player : poster;
    const sampleScale = fromVideo ? 2 : 1;
    // While seeking or buffering, keep the last decoded picture. The
    // opening poster must not flash back after the clip has started.
    for (let side=0;side<2 && (!ready || fromVideo && !player.seeking);side++) {
      const surface = canvas[side];
      if (surface.width !== w) surface.width = w;
      if (surface.height !== h) surface.height = h;
      const available = surface.parentElement.clientWidth;
      const desired = mode === 'close' ? 2 : 1;
      const displayScale = mode === 'phone' ? Math.min(1,available/w) : desired;
      surface.style.width = w*displayScale+'px';
      surface.style.height = h*displayScale+'px';
      const context = contexts[side];
      context.imageSmoothingEnabled = false;
      context.fillStyle = '#090f17';
      context.fillRect(0,0,w,h);
      if (fromVideo || (image?.complete && image.naturalWidth)) {
        context.drawImage(image,(side*width+x)*sampleScale,y*sampleScale,w*sampleScale,h*sampleScale,0,0,w,h);
      }
    }
    for (const button of viewButtons) button.setAttribute('aria-pressed',String(button.dataset.view === mode));
    const t = Math.min(duration(),ready && !player.seeking ? player.currentTime : intendedTime);
    $('time').textContent = t.toFixed(2)+' / '+duration().toFixed(2)+' 秒';
    seekbar.value = Math.min(Number(seekbar.max),Math.round(t*fps));
  }

  function stop() {
    player.pause();
    original.pause();
    cancelAnimationFrame(animate);
    $('play').textContent = '播放';
  }

  function seek(time) {
    if (!clip) return;
    stop();
    intendedTime = Math.max(0,Math.min(Number(seekbar.max)/fps,time));
    if (player.readyState) player.currentTime = intendedTime;
    if (original.readyState) original.currentTime = intendedTime;
    redraw();
  }

  function audioMode() {
    const value = $('sound').value;
    player.muted = value !== 'after';
    original.pause();
    if (value === 'before') {
      original.currentTime = player.currentTime;
      original.playbackRate = player.playbackRate;
      if (!player.paused) original.play().catch(() => {});
    }
  }

  async function play() {
    if (!clip) return;
    if (!player.paused) { stop(); return; }
    if (player.ended || player.currentTime>=duration()-1/fps) seek(0);
    player.muted = $('sound').value !== 'after';
    try {
      const run = player.play();
      if ($('sound').value === 'before') {
        original.currentTime = player.currentTime;
        original.playbackRate = player.playbackRate;
        original.play().catch(() => {});
      }
      await run;
      $('play').textContent = '暂停';
      animate = requestAnimationFrame(tick);
    } catch {
      $('status').textContent = '视频暂未载入，稍候可重新播放。';
    }
  }

  function tick() {
    if (player.paused) return;
    if (clip.afterDuration && player.currentTime>=duration()) {
      seek(Number(seekbar.max)/fps);
      return;
    }
    if ($('sound').value === 'before' && original.readyState && Math.abs(original.currentTime-player.currentTime)>.16) {
      original.currentTime = player.currentTime;
    }
    redraw();
    animate = requestAnimationFrame(tick);
  }

  async function mediaSources(row) {
    mediaRequest?.abort();
    const request = new AbortController();
    mediaRequest = request;
    player.removeAttribute('src');
    original.removeAttribute('src');
    player.load();
    original.load();
    objectUrls.forEach(url => URL.revokeObjectURL(url));
    objectUrls = [];
    const paths = [row.video,row.beforeAudio];
    if (location.protocol !== 'file:') {
      try {
        // Local static servers may serve the whole file without byte ranges.
        // A local Blob gives WebKit a seekable copy for frame controls.
        const files = await Promise.all(paths.map(async path => {
          const response = await fetch(path,{signal:request.signal});
          if (!response.ok) throw new Error(path);
          return response.blob();
        }));
        if (request.signal.aborted) return;
        objectUrls = files.map(file => URL.createObjectURL(file));
      } catch {
        if (request.signal.aborted) return;
      }
    }
    [player.src,original.src] = objectUrls.length ? objectUrls : paths;
    player.playbackRate = Number($('speed').value);
  }

  function load(key) {
    const next = clips.find(row => row.key === key);
    if (!next) return;
    stop();
    clip = next;
    showOriginalDuration = false;
    if (!manualMode) mode = innerWidth<=690 || clip.kind==='cinema' || clip.kind==='map' ? 'native' : 'close';
    ready = false;
    intendedTime = clip.posterTime;
    $('viewer').setAttribute('aria-busy','true');
    $('viewer').dataset.case = clip.key;
    if (!matches().some(row => row.key === key)) search.value = '';
    fillCategories(search.value.trim() && category.value === 'all' ? 'all' : group(clip));
    fillCases(clip.key);
    $('family').textContent = names.get(group(clip)) +
      (clip.kind === 'cinema' ? ' · 主角必杀' : '');
    $('case-title').textContent = clip.title;
    $('result').textContent = clip.hpStart === null || clip.hpStart === undefined
      ? '地图结果一致'
      : '目标生命 '+clip.hpStart+' → '+clip.hpEnd+' · '+(clip.support ? '支援演出' : clip.commits+' 次结算');
    $('before-label').textContent = clip.afterDuration ? '调速前' : clip.archive ? '本轮修正前' : '接入前';
    $('after-label').textContent = clip.afterDuration ? '调速后' : '当前实机';
    $('before-caption').textContent = clip.afterDuration
      ? 'Godot 1× · '+clip.beforeDuration.toFixed(2)+' 秒' : clip.archive ? 'Godot 历史录制' : 'Godot 原版';
    $('after-caption').textContent = clip.afterDuration
      ? 'Godot 1× · '+clip.afterDuration.toFixed(2)+' 秒' : 'Godot 已接入版';
    $('full-duration').hidden = !clip.afterDuration;
    $('dash').hidden = (clip.flightAt ?? clip.dashAt) == null;
    $('dash').textContent = clip.flightAt == null ? '查看突进' : '查看飞行';
    $('portrait').hidden = clip.portraitAt == null;
    $('first-slash').hidden = clip.firstSlashAt == null;
    $('hp').hidden = clip.hpAt === null;
    $('cue').hidden = clip.cueAt === null;
    $('hit').textContent = clip.kind === 'map' ? '查看反馈' : clip.firstSlashAt == null ? '查看命中' : '查看第二斩';
    $('sound').options[1].text = $('after-label').textContent;
    $('sound').options[2].text = $('before-label').textContent;
    updateDuration();
    for (const b of $('quick').children) b.setAttribute('aria-pressed',String(b.dataset.case === clip.key));
    poster = new Image();
    poster.onload = redraw;
    poster.src = clip.poster;
    mediaSources(clip);
    history.replaceState(null,'','#'+clip.key);
    redraw();
  }

  for (const [key,name] of quick) {
    if (!clips.some(row => row.key === key)) continue;
    const button = document.createElement('button');
    button.textContent = name;
    button.type = 'button';
    button.dataset.case = key;
    button.onclick = () => load(key);
    $('quick').append(button);
  }
  category.onchange = () => {
    fillCases(clip.key);
    if (cases.value && cases.value !== clip.key) load(cases.value);
  };
  cases.onchange = () => load(cases.value);
  search.oninput = () => { fillCategories(search.value.trim() ? 'all' : group(clip));fillCases(clip.key); };
  search.onkeydown = event => {
    if (event.key === 'Enter') load([...cases.options].find(option => !option.disabled)?.value);
  };
  player.onloadedmetadata = () => { player.currentTime = intendedTime; };
  player.onloadeddata = player.onseeked = () => {
    ready = true;
    $('viewer').setAttribute('aria-busy','false');
    redraw();
  };
  player.onended = () => { stop();redraw(); };
  player.onerror = () => { $('status').textContent = '录制视频载入失败，仍可查看对照关键帧。'; };
  $('play').onclick = play;
  $('restart').onclick = () => { seek(0);play(); };
  $('prev').onclick = () => seek((Math.round(player.currentTime*fps)-1)/fps);
  $('next').onclick = () => seek((Math.round(player.currentTime*fps)+1)/fps);
  $('cue').onclick = () => seek(clip.cueAt);
  $('dash').onclick = () => seek(clip.flightAt ?? clip.dashAt);
  $('portrait').onclick = () => seek(clip.portraitAt);
  $('first-slash').onclick = () => seek(clip.firstSlashAt);
  $('hit').onclick = () => seek(clip.contact+.08);
  $('hp').onclick = () => seek(clip.hpAt);
  $('full-duration').onclick = () => {
    showOriginalDuration = !showOriginalDuration;
    updateDuration();
    seek(player.currentTime);
  };
  seekbar.oninput = () => seek(Number(seekbar.value)/fps);
  $('speed').onchange = () => {
    player.playbackRate = Number($('speed').value);
    original.playbackRate = player.playbackRate;
  };
  $('sound').onchange = audioMode;
  for (const button of viewButtons) button.onclick = () => { manualMode=true;mode=button.dataset.view;redraw(); };
  wells.forEach((well,index) => well.addEventListener('scroll',() => {
    const peer = wells[1-index];
    if (peer.scrollLeft!==well.scrollLeft) peer.scrollLeft=well.scrollLeft;
  }));
  addEventListener('resize',redraw);
  addEventListener('hashchange',() => load(location.hash.slice(1)));
  addEventListener('keydown',event => {
    if (['BUTTON','SELECT','INPUT','A'].includes(document.activeElement.tagName)) return;
    if (event.code === 'Space') { event.preventDefault();play(); }
    if (event.key === 'ArrowRight') $('next').click();
    if (event.key === 'ArrowLeft') $('prev').click();
  });
  load(clips.find(row => row.key===location.hash.slice(1))?.key || 'c30ab900b09f');
})();
