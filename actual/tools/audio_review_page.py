"""Build the local, level-preserving original/new SFX comparison page."""
from __future__ import annotations

import html
import json
from pathlib import Path
import subprocess


def build_sfx_comparison(records, plans, report: Path, project: Path, ffmpeg: str):
    source = json.loads((project / "data/legacy/full_audio.json").read_text())
    plan_by_id = {row["id"]: row for row in plans}
    previews = report / "audition"
    previews.mkdir(parents=True, exist_ok=True)
    cards, table, pairs = [], [], []

    def preview(path, name):
        output = previews / name
        if not output.exists() or output.stat().st_mtime < path.stat().st_mtime:
            codec_args=(["-c:a","pcm_s16le"] if output.suffix=='.wav' else ["-c:a","libmp3lame","-b:a","192k"])
            subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-y",
                            "-i", str(path), "-map_metadata", "-1", *codec_args, str(output)], check=True)
        return "audition/" + name

    for record in records:
        plan = plan_by_id[record["id"]]
        request = str(record["request"]).upper()
        original = source["sfx_by_request"][request]
        old_path = project / original["path"].removeprefix("res://")
        new_path = project.parent / record["runtime_path"]
        old_preview = preview(old_path, f"original_{request.lower()}.wav")
        new_preview = preview(new_path, record["id"] + "_" + record['sha256'][:12] + ".wav")
        metrics = record["metrics"]
        baseline = record["source_baseline"]
        role = str(plan.get("role", ""))
        title = str(record["title"])
        state = "有限持续，由原调用停止" if record["manual_stop"] else "单次音效"
        if request in ("21", "53"):
            state += "；具体请求已启用，泛用 attack/death 别名禁用"
        if not plan.get("current_runtime_reference_count", 0):
            state += "；兼容备用，当前未检出触发"
        key = record["sha256"]
        esc = html.escape
        cards.append(f'''<article id="request-{request}" data-search="{esc(request+' '+title+' '+role, quote=True)}" data-sha="{key}" data-request="{request}">
<div class="heading"><h2><span class="code">{request}</span> {esc(title)}</h2><button type="button" class="compare" data-request="{request}">原声 → 新音效</button></div>
<p class="role">{esc(role)}</p><p class="facts">{esc(state)}</p>
<div class="comparison"><div class="sound"><h3>外传原声</h3><p class="facts">{float(original['duration']):.3f} 秒 · {baseline['active_rms_dbfs']:.2f} dBFS 活动 RMS</p><audio id="original-{request}" controls preload="none" src="{old_preview}"></audio></div>
<div class="sound new"><h3>新音效</h3><p class="facts">{metrics['seconds']:.3f} 秒 · {metrics['active_rms_dbfs']:.2f} dBFS 活动 RMS · 起音 {metrics['leading_onset_seconds']*1000:.1f} ms</p><audio id="new-{request}" controls preload="none" src="{new_preview}"></audio></div></div>
<details class="review"><summary>你的试听备注：<span class="review-state">待记录</span></summary><label>你的结论 <select class="verdict"><option value="pending">待记录</option><option value="accepted">可接受</option><option value="revise">需修改</option></select></label><label>备注 <textarea class="note" rows="2" placeholder="记录音色、音量、拖尾或场景不符的位置"></textarea></label><p class="facts">播放完成不会自动标为通过。状态保存在当前浏览器，声音文件更换后重新记录。</p></details>
<p class="links"><a href="../../assets/sfx/20261024/{record['id']}.ogg">新运行 OGG</a> · <a href="{esc('../../'+original['path'].removeprefix('res://'), quote=True)}">原声 OGG</a> · <a href="tracks/{record['id']}.json">制作指标</a></p></article>''')
        table.append(f"| {request} | {title} | {float(original['duration']):.3f} | {metrics['seconds']:.3f} | {baseline['active_rms_dbfs']:.2f} | {metrics['active_rms_dbfs']:.2f} | {metrics['true_peak_dbtp']:.1f} | {record['bytes']:,} |")
        pairs.append({"request": request, "id": record["id"], "sha256": key,
                      "original_preview": old_preview, "new_preview": new_preview,
                      "original_resource": original["path"], "new_resource": record["resource_path"]})

    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>原创音效试听 · 原声与新音效对比</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f0e8;color:#243035;font:16px/1.65 system-ui,sans-serif}main{max-width:1140px;margin:auto;padding:24px}h1{line-height:1.3;margin:0 0 12px}h2{font-size:20px;line-height:1.45;margin:0;overflow-wrap:anywhere}h3{font-size:16px;margin:0 0 6px}p{margin:10px 0}header{margin-bottom:22px}.intro{max-width:900px}.notice{background:#e8ece7;padding:14px 18px;border-radius:10px}.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:12px;background:#fffdf8;padding:16px;border-radius:12px;box-shadow:0 3px 15px #29312d10;margin:20px 0}button,select,input[type=search]{font:inherit;min-height:44px;border:0;border-radius:8px;padding:9px 14px;background:#e7eeea;color:#243b38}button{cursor:pointer;text-align:center;box-shadow:0 2px 5px #203c3220}button:hover{background:#d5e3dc}button:disabled{opacity:.5;cursor:default}input[type=search]{background:#f3f4ee;min-width:210px;flex:1}label{display:flex;gap:9px;align-items:center}input[type=range]{width:120px}#playback{min-height:26px;color:#355d68}.progress{font-size:14px;color:#53676a}article{background:#fffdf8;padding:22px;border-radius:12px;box-shadow:0 3px 15px #29312d10;margin:0 0 18px;scroll-margin:16px}article.playing{box-shadow:0 0 0 4px #789c9b50,0 3px 15px #29312d10}article[hidden]{display:none}.heading{display:flex;justify-content:space-between;align-items:center;gap:18px}.heading button{flex-shrink:0}.code{display:inline-block;color:#426b66;font-size:15px;margin-right:5px}.role{margin:10px 0 4px}.facts,.links{font-size:14px;color:#52666b}.comparison{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;margin:14px 0}.sound{min-width:0;padding:16px;border-radius:9px;background:#f2f0ea}.sound.new{background:#eaf0e9}audio{display:block;width:100%;margin-top:10px}.review{margin-top:12px;padding:10px 0}.review summary{cursor:pointer}.review label{margin-top:10px;align-items:flex-start}.review select{min-width:125px}.review textarea{font:inherit;width:100%;min-width:0;border:0;background:#f2f3ed;border-radius:8px;padding:10px}a{color:#355d68}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,summary:focus-visible{outline:none;box-shadow:0 0 0 4px #789c9b60}@media(max-width:680px){main{padding:15px}article{padding:17px}.comparison{grid-template-columns:1fr}.heading{align-items:flex-start;flex-direction:column;gap:10px}.toolbar{padding:13px}.heading button{width:100%}.toolbar button{flex:1}}
</style></head><body><main><header><h1>原创音效试听</h1><p class="intro">41 组外传原声／新音效并排对比，覆盖原有 42 个文件。菜单移动与 HP 刻度共用请求 12，因此只列一组。每项保留实际场景说明和原始相对音量，没有将新旧声音自动拉成一样响。</p><p class="notice">当前环境不支持音频输入，未完成真正听觉验收。信号、场景与时序检查见报告；听审结论由手动记录，播放完毕不会自动判定通过。原声仅用于本地对照，游戏读取新音效。</p><p><a href="README.md">修改依据与检查范围</a> · <a href="tracks.md">新旧音效指标表</a> · <a href="../audio-scene-review-20261024/index.html">69 条音频场景检查</a> · <a href="../soundtrack-20261024/index.html">28 首配乐试听</a></p>
<div class="toolbar"><input id="search" type="search" aria-label="筛选音效" placeholder="搜索请求编号、名称或场景"><button id="play-all" type="button">顺序对比筛选结果</button><button id="stop" type="button">停止</button><label>试听音量 <input id="volume" type="range" min="0" max="100" value="65"><output id="volume-value">65%</output></label></div><p class="facts">65% 对应当前游戏音效倍率；两边使用同一试听音量。这里是单独声音对比，配乐与音效叠加示例请进入场景检查页。</p><p id="playback" role="status" aria-live="polite">点击单项对比，或顺序播放筛选结果。</p><p id="progress" class="progress"></p></header><section>''' + "".join(cards) + '''</section></main>
<script>
const articles=[...document.querySelectorAll('article')],players=[...document.querySelectorAll('audio')],labels={pending:'待记录',accepted:'可接受',revise:'需修改'};let run=0,queuedPlayer=null;const key='revenge-sfx-audition-v1';let saved={};try{saved=JSON.parse(localStorage.getItem(key)||'{}')}catch(e){};
function summary(){let accepted=0,revise=0;articles.forEach(a=>{let state=a.querySelector('.verdict').value;accepted+=state==='accepted';revise+=state==='revise'});document.getElementById('progress').textContent=`共 ${articles.length} 组 · 手动可接受 ${accepted} · 需修改 ${revise} · 待记录 ${articles.length-accepted-revise}`}
articles.forEach(a=>{const v=a.querySelector('.verdict'),n=a.querySelector('.note'),s=a.querySelector('.review-state'),old=saved[a.dataset.request];if(old&&old.sha===a.dataset.sha){v.value=labels[old.verdict]?old.verdict:'pending';n.value=old.note||''}s.textContent=labels[v.value];function store(){s.textContent=labels[v.value];saved[a.dataset.request]={sha:a.dataset.sha,verdict:v.value,note:n.value};try{localStorage.setItem(key,JSON.stringify(saved))}catch(e){}summary()}v.addEventListener('change',store);n.addEventListener('input',store)});summary();
function volume(){const value=document.getElementById('volume').value/100;players.forEach(p=>p.volume=value);document.getElementById('volume-value').textContent=Math.round(value*100)+'%'}document.getElementById('volume').addEventListener('input',volume);volume();
function halt(message='已停止。'){run++;queuedPlayer=null;players.forEach(p=>p.pause());articles.forEach(a=>a.classList.remove('playing'));document.getElementById('playback').textContent=message}document.getElementById('stop').addEventListener('click',()=>halt());
players.forEach(p=>p.addEventListener('play',()=>{if(p!==queuedPlayer){run++;queuedPlayer=null;articles.forEach(a=>a.classList.remove('playing'));document.getElementById('playback').textContent='手动播放；连续对比已停止。'}players.forEach(other=>{if(other!==p)other.pause()})}));
function play(p,token){return new Promise(resolve=>{if(token!==run)return resolve(false);let settled=false;const finish=ok=>{if(settled)return;settled=true;p.removeEventListener('ended',ended);p.removeEventListener('error',failed);p.removeEventListener('pause',paused);if(queuedPlayer===p)queuedPlayer=null;resolve(ok&&token===run)};const ended=()=>finish(true),failed=()=>finish(false),paused=()=>{if(!p.ended)finish(false)};queuedPlayer=p;p.currentTime=0;p.addEventListener('ended',ended);p.addEventListener('error',failed);p.addEventListener('pause',paused);p.play().catch(()=>finish(false))})}
async function compare(list){halt('准备播放…');const token=run;for(let i=0;i<list.length;i++){const a=list[i],r=a.dataset.request;if(token!==run)return;a.classList.add('playing');for(const [side,name] of [['original','外传原声'],['new','新音效']]){if(token!==run)return;document.getElementById('playback').textContent=`${i+1}/${list.length} · ${r} · ${name}`;const ok=await play(document.getElementById(side+'-'+r),token);if(!ok){if(token===run)halt('播放已中断或浏览器阻止连续播放，请使用音频控件。');return}await new Promise(resolve=>setTimeout(resolve,220))}a.classList.remove('playing')}if(token===run)document.getElementById('playback').textContent='对比播放结束。你的听感仍可手动记录。'}
document.querySelectorAll('button.compare').forEach(b=>b.addEventListener('click',()=>compare([b.closest('article')])));document.getElementById('play-all').addEventListener('click',()=>compare(articles.filter(a=>!a.hidden)));document.getElementById('search').addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();articles.forEach(a=>a.hidden=!a.dataset.search.toLowerCase().includes(q))});
</script></body></html>'''
    final=project/'reports/audio-content-review-20261024/final-review.json'
    notice=('已完成本地音频理解模型逐条审查，最终依据与版本见模型审查报告。下方人工试听备注独立保存，播放完成不会自动判为通过。'
            if all(r.get('audio_content_review',{}).get('model_review_completed') for r in records) else '本地音频理解模型逐条审查进行中。已确认的问题正在替换；下方人工试听备注独立保存，播放完成不会自动判为通过。')
    page=page.replace('当前环境不支持音频输入，未完成真正听觉验收。信号、场景与时序检查见报告；听审结论由手动记录，播放完毕不会自动判定通过。原声仅用于本地对照，游戏读取新音效。',notice+' 原声用于对照；重制方法包括原声引导生成、音高与包络分析重合成，制作来源可逐项查阅。')
    page=page.replace('<a href="README.md">修改依据与检查范围</a>', '<a href="../audio-content-review-20261024/README.md">模型听审与修改依据</a> · <a href="README.md">制作范围</a>')
    page=page.replace('<h1>原创音效试听</h1>', '<h1>音效试听 · 原声与重制对比</h1>')
    page=page.replace('这里是单独声音对比，配乐与音效叠加示例请进入场景检查页。', '本页直接从运行 OGG 解码为 WAV 试听，避免额外 MP3 转码模糊短音起音。这里是单独声音对比，配乐与音效叠加示例请进入场景检查页。')
    (report / "index.html").write_text(page)
    (report / "comparison-manifest.json").write_text(json.dumps({"pairs": pairs, "count": len(pairs),
        "level_matching": False, "default_playback_gain": .65, "auditory_review": all(r.get("audio_content_review",{}).get("model_review_completed") for r in records), "human_listening": False}, ensure_ascii=False, indent=2) + "\n")
    (report / "tracks.md").write_text("# 新旧音效对照指标\n\n原声与新声保留实际相对电平；短于 400ms 的事件不使用 LUFS 判优。此表不是听觉验收结论。\n\n| 请求 | 名称 | 原秒数 | 新秒数 | 原活动 RMS | 新活动 RMS | 新真峰值 dBTP | 新字节 |\n|---|---|---:|---:|---:|---:|---:|---:|\n" + "\n".join(table) + "\n")
