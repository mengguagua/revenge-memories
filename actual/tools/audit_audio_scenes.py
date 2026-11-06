"""Per-resource signal/context review. This never certifies perceptual listening.

Render comparisons using the game's gains and two-voice replacement rules;
source animation requests retain their native frame order and contact pause.
No window, speaker playback, GPU model, save or device access is required.
"""
from __future__ import annotations
import hashlib
import html
import json
import math
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "actual"
REPORT = PROJECT / "reports/audio-scene-review-20261024"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
SR = 44100
FPS = 60.0988
MUSIC_GAIN, SFX_GAIN = .50, .65

def read(path): return json.loads(path.read_text())
def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n")
def db(value): return float(20*math.log10(max(float(value),1e-12)))
def rms(a): return float(np.sqrt(np.mean(a.astype(np.float64)**2))) if a.size else 0.
def resource(path): return PROJECT / path.removeprefix("res://")
def load(path):
    a, rate = sf.read(path, dtype="float32", always_2d=True)
    if rate != SR or a.shape[1] != 2: raise ValueError(f"Unexpected audio format: {path}")
    return a
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def mono_check(a):
    stereo = rms(a)
    mono = rms(a.mean(axis=1))
    return {"mono_downmix_change_db":db(mono/max(stereo,1e-12)),
            "mono_cancellation_concern":bool(stereo>1e-6 and mono/stereo<.5)}
def status_text(row):
    return "需排查信号异常" if row["program_result"]=="needs_investigation" else "信号与时序检查通过"

def boundary_check(a):
    # Compare the wrapped edge with the local derivative distribution. Chord
    # or phrase coherence remains a separate model/human auditory judgement.
    tail, head = a[-SR//2:], a[:SR//2]
    derivatives = np.concatenate([np.diff(tail,axis=0),np.diff(head,axis=0)])
    jump = float(np.abs(a[-1]-a[0]).max())
    local = rms(derivatives)
    ratio = jump/max(local,1e-9)
    return {"seam_sample_step":jump,"seam_step_over_local_diff_rms":ratio,
            "seam_step_dbfs":db(jump),
            "level_change_100ms_db":db(rms(head[:4410]))-db(rms(tail[-4410:])),
            "possible_sample_click":bool(jump>.02 and ratio>6)}
def preview(path, audio):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not np.isfinite(audio).all() or float(np.abs(audio).max())>=1:
        raise ValueError("Preview would clip; preserve and investigate the mix")
    wav=path.with_suffix(".wav")
    sf.write(wav,audio,SR,subtype="PCM_16")
    subprocess.run([FFMPEG,"-v","error","-nostdin","-y","-i",str(wav),
                    "-map_metadata","-1","-c:a","libmp3lame","-b:a","160k",str(path)],check=True)
    # Retain a lossless decoded scene fixture for model review and audition.

def source_schedule(variant, speed=1.0, damage=4):
    ct=int(variant["contact_tick"])
    item=int(variant.get("source_item_id",0))
    support=40<=item<=47
    contact_pause=(.3 if support else (11+damage+16)/FPS)/speed
    events=[]
    for tick,frame in enumerate(variant["frames"]):
        time=tick/FPS/speed+(contact_pause if tick>ct else 0)
        for order,request in enumerate(frame.get("sound_requests",[])):
            events.append((time,order,int(request),"source frame"))
        if tick==ct and not support:
            events.append((time,100,0x03 if damage else 0x43,"contact feedback"))
            for hp in range(damage):
                events.append((time+(11+hp)/FPS/speed,100,0x12,"HP decrement"))
    end=len(variant["frames"])/FPS/speed+contact_pause
    events.append((end,200,-53,"action-end 53 cleanup"))
    return sorted(events),end

def render_sfx(events, data, controls, length=None):
    """Mirror OriginalAudio's two voices, stops, and special 53 replacement."""
    voices=[None,None];next_voice=0;segments=[];discarded=[]
    def stop(index,time):
        voice=voices[index]
        if voice is not None:
            cut=min(time,voice["end"])
            if cut>voice["start"]:segments.append({**voice,"stop":cut})
            if cut<voice["end"]:discarded.append({"request":voice["request"],"after_seconds":cut-voice["start"]})
            voices[index]=None
    for time,_order,number,_origin in events:
        for i,v in enumerate(voices):
            if v and v["end"]<=time:stop(i,v["end"])
        if number==-53:
            for i,v in enumerate(voices):
                if v and v["request"]=="53":stop(i,time)
            continue
        request=f"{number:02X}"
        if request in controls:
            if controls[request] in ["stop_all","stop_sfx"]:
                for i in range(2):stop(i,time)
            continue
        if request not in data: continue
        if request in ["03","43"]:
            for i,v in enumerate(voices):
                if v and v["request"]=="53":stop(i,time)
        index=next((i for i,v in enumerate(voices) if v is None),next_voice)
        stop(index,time)
        audio=data[request]
        voices[index]={"request":request,"start":time,"end":time+len(audio)/SR}
        next_voice=(index+1)%2
    timeline_end=max([e[0] for e in events]+[.1])
    remaining=[{"request":v["request"],"seconds_after_timeline":max(0,v["end"]-timeline_end)}
               for v in voices if v is not None and v["end"]>timeline_end]
    end=max([timeline_end]+[v["end"] for v in voices if v is not None])
    if length is not None:end=max(end,length)
    for i in range(2):stop(i,end)
    out=np.zeros((int((end+.05)*SR),2),dtype=np.float32)
    delivered={}
    for s in segments:
        start=int(s["start"]*SR);count=min(int((s["stop"]-s["start"])*SR),len(data[s["request"]]),len(out)-start)
        if count<=0:continue
        clip=data[s["request"]][:count]
        out[start:start+count]+=clip*SFX_GAIN
        delivered.setdefault(s["request"],[]).append(count/SR)
    return out,{"sample_peak_dbfs":db(np.abs(out).max()),"full_scale_samples":int((np.abs(out)>=1).sum()),
                "delivered_seconds_by_request":delivered,"preemptions":discarded,
                "voices_remaining_after_timeline":remaining}

def bed(a,count,start=0):
    index=(np.arange(count)+int(start*SR))%len(a)
    return a[index]*MUSIC_GAIN

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    music_report=read(PROJECT/"reports/soundtrack-20261024/generation-report.json")
    sfx_report=read(PROJECT/"reports/sfx-20261024/generation-report.json")
    music_plans={x["id"]:x for x in read(PROJECT/"reports/soundtrack-20261024/plan.json")["tracks"]}
    sfx_plans={x["id"]:x for x in read(PROJECT/"reports/sfx-20261024/plan.json")["tracks"]}
    music_by_id={r['id']:r for r in music_report['tracks']}
    source=read(PROJECT/"data/legacy/full_audio.json")
    new_sfx={r["request"]:load(ROOT/r["runtime_path"]) for r in sfx_report["tracks"]}
    old_sfx={key:load(resource(entry["path"])) for key,entry in source["sfx_by_request"].items()}
    variants=read(PROJECT/"data/legacy/full_animation_effects.json")["variants"]
    unique={}
    for name,v in variants.items():
        calls=tuple((i,int(r)) for i,f in enumerate(v["frames"]) for r in f.get("sound_requests",[]))
        if calls:unique.setdefault((calls,int(v["contact_tick"])),(name,v))
    traces=[];representative={};clipping=[]
    for name,v in unique.values():
        for speed in [1.,3.]:
            events,end=source_schedule(v,speed)
            a,metrics=render_sfx(events,new_sfx,source["control_requests"],end+.3)
            if metrics["full_scale_samples"]:clipping.append([name,speed])
            traces.append({"variant":name,"speed":speed,"events":len(events),**metrics})
            if speed==1:
                for _,_,n,_ in events:
                    request=f"{n:02X}"
                    if request in new_sfx:representative.setdefault(request,(name,v,events,end))
    # Ordinary physical contact uses the same real controller timing as spells.
    physical=[(.5,0,0x03,"contact")]+[(.5+(11+i)/FPS,0,0x12,"HP decrement") for i in range(4)]
    patterns={"physical":(physical,2.4),"fire":source_schedule(variants["class_11_ally_item_23"]),
              "lightning":source_schedule(variants["class_11_ally_item_24"])}
    rain=next((v for v in variants.values() if any(83 in f.get("sound_requests",[]) for f in v["frames"])),None)
    if rain:patterns["arrow_rain"]=source_schedule(rain)
    rows=[];cards=[];markdown=[]
    for record in music_report["tracks"]:
        ident=record["id"];plan=music_plans[ident];a=load(ROOT/record["runtime_path"])
        row={"id":ident,"title":record["title"],"type":"music","scene":plan["scene"],
             "sha256_matches":sha(ROOT/record["runtime_path"])==record["sha256"],
             "actual_game_gain":MUSIC_GAIN,"post_gain_integrated_lufs":record["metrics"]["integrated_lufs"]+db(MUSIC_GAIN),
             **mono_check(a),"auditory_review":False}
        if record["loop"]:row["loop_boundary"]=boundary_check(a)
        if record["kind"]=="jingle":
            underlying_key='rm_hub_hearth' if ident=='rm_jingle_award' else 'rm_battle_snow'
            underlying=load(ROOT/music_by_id[underlying_key]['runtime_path'])
            scene_audio=np.concatenate([bed(underlying,SR),a*MUSIC_GAIN,bed(underlying,SR,start=1)])
            context="按游戏倍率：背景曲 1 秒 → 暂停并播提示 → 从原位置恢复 1 秒"
        elif ident.startswith("rm_battle"):
            pattern="arrow_rain" if ident=="rm_battle_final" and rain else "lightning" if ident in ["rm_battle_circuit","rm_battle_ascent"] else "fire" if ident in ["rm_battle_tide","rm_battle_refuge"] else "physical"
            events,end=patterns[pattern];fx,_=render_sfx(events,new_sfx,source["control_requests"],end+.35)
            scene_audio=bed(a,len(fx),start=3)+fx
            context="按当前双声部与实际请求时序合成："+{"physical":"普通命中与生命刻度","fire":"火球脉冲","lightning":"雷电脉冲","arrow_rain":"箭雨命中"}[pattern]+"；不是实机录音"
        else:
            events=[(.6,0,0x12,"menu"),(1.,0,0x12,"menu"),(1.4,0,0x10,"confirm"),(2.5,0,0x25,"dialogue"),(3.8,0,0x25,"dialogue")]
            fx,_=render_sfx(events,new_sfx,source["control_requests"],5.)
            scene_audio=bed(a,len(fx),start=3)+fx
            context="按游戏倍率合成：背景曲＋菜单／对白提示；不是实机录音"
        row["scene_mix_peak_dbfs"]=db(np.abs(scene_audio).max())
        row['scene_context']=context
        row["scene_mix_full_scale_samples"]=int((np.abs(scene_audio)>=1).sum())
        if row["scene_mix_full_scale_samples"]:clipping.append([ident,"music scene"])
        preview(REPORT/"audition"/(ident+"_scene.mp3"),scene_audio)
        row['scene_fixture_path']=str((REPORT/'audition'/(ident+'_scene.wav')).relative_to(ROOT))
        row['scene_fixture_sha256']=sha(ROOT/row['scene_fixture_path'])
        seam=""
        if record["loop"]:
            preview(REPORT/"audition"/(ident+"_seam.mp3"),np.concatenate([a[-2*SR:],a[:2*SR]])*MUSIC_GAIN)
            seam=f'<p>循环边界：第 2 秒由末尾接回开头，按 50% 游戏倍率。</p><audio controls preload="none" src="audition/{ident}_seam.mp3"></audio>'
        row["program_result"]="needs_investigation" if row["mono_cancellation_concern"] or row.get("loop_boundary",{}).get("possible_sample_click") or row["scene_mix_full_scale_samples"] else "checks_passed_listening_pending"
        rows.append(row)
        cards.append(f'<article><h2>{html.escape(record["title"])}</h2><p>{html.escape(plan["scene"])}</p><p class="facts">程序检查：{status_text(row)} · 逐首听审：未完成</p><p>{context}</p><audio controls preload="none" src="audition/{ident}_scene.mp3"></audio>{seam}<p><a href="../soundtrack-20261024/index.html#{ident}">完整配乐试听</a></p></article>')
        markdown.append(f'| 配乐 | {record["title"]} | {plan["scene"]} | {row["scene_mix_peak_dbfs"]:.2f} | {row["mono_downmix_change_db"]:.2f} | {status_text(row)} | 待听审 |')
    for record in sfx_report["tracks"]:
        ident=record["id"];plan=sfx_plans[ident];request=record["request"];a=new_sfx[request]
        row={"id":ident,"request":request,"title":record["title"],"type":"sfx","scene":plan["role"],
             "sha256_matches":sha(ROOT/record["runtime_path"])==record["sha256"],
             "actual_game_gain":SFX_GAIN,"onset_seconds":record["metrics"]["leading_onset_seconds"],
             "source_active_rms_delta_db":record['metrics']['active_rms_dbfs']-record['source_baseline']['active_rms_dbfs'],
             **mono_check(a),"auditory_review":False}
        if request in representative:
            name,v,events,end=representative[request]
            row["representative_variant"]=name
            old_mix,_=render_sfx(events,old_sfx,source["control_requests"],end+.35)
            new_mix,stats=render_sfx(events,new_sfx,source["control_requests"],end+.35)
            row["representative_rms_delta_db"]=db(rms(new_mix))-db(rms(old_mix))
            row["scene_mix_peak_dbfs"]=stats["sample_peak_dbfs"]
            row["delivered_windows_seconds"]=stats["delivered_seconds_by_request"].get(request,[])
            windows=row["delivered_windows_seconds"]
            if windows:
                window=min(min(windows),len(a)/SR,len(old_sfx[request])/SR)
                count=max(1,int(window*SR))
                row["effective_window_seconds"]=window
                row["effective_window_original_rms_dbfs"]=db(rms(old_sfx[request][:count]))
                row["effective_window_new_rms_dbfs"]=db(rms(a[:count]))
                row["effective_window_delta_db"]=row["effective_window_new_rms_dbfs"]-row["effective_window_original_rms_dbfs"]
                if abs(row["effective_window_delta_db"])>6:
                    row["listening_focus"]="有效触发窗口的新旧电平相差超过6dB；需听审确认存在感，不能只凭整体RMS判断。"
            context="实际源动画请求序列（同一当前双声部规则）："+name
        elif int(request,16) in [0x10,0x12,0x13,0x25]:
            step=.10 if request=="12" else .50
            events=[(.2+i*step,0,int(request,16),"UI repetition") for i in range(6)]
            old_mix,_=render_sfx(events,old_sfx,source["control_requests"],2.)
            new_mix,stats=render_sfx(events,new_sfx,source["control_requests"],2.)
            row["scene_mix_peak_dbfs"]=stats["sample_peak_dbfs"]
            context="连续 UI 提示示例；请求 12 每 100 ms 一次，其余每 500 ms 一次"
        else:
            old_mix=old_sfx[request]*SFX_GAIN;new_mix=a*SFX_GAIN
            row["scene_mix_peak_dbfs"]=db(np.abs(new_mix).max())
            context="兼容备用：未检出当前调用，不增加猜测的游戏触发"
        if request in representative or request in ['10','12','13','25']:
            battle_music=load(ROOT/music_by_id['rm_battle_snow']['runtime_path'])
            hub_music=load(ROOT/music_by_id['rm_hub_hearth']['runtime_path'])
            if request=='12' and request in representative:
                events=[(.2+i*.10,0,0x12,'menu movement') for i in range(6)]
                menu_old,_=render_sfx(events,old_sfx,source['control_requests'],2.)
                menu_new,_=render_sfx(events,new_sfx,source['control_requests'],2.)
                menu_old+=bed(hub_music,len(menu_old),start=3)
                menu_new+=bed(hub_music,len(menu_new),start=3)
                old_mix+=bed(battle_music,len(old_mix),start=3)
                new_mix+=bed(battle_music,len(new_mix),start=3)
                gap=np.zeros((int(.4*SR),2),np.float32)
                old_mix=np.concatenate([menu_old,gap,old_mix])
                new_mix=np.concatenate([menu_new,gap,new_mix])
                context='菜单每100ms连移示例，间隔0.4秒后为实际源战斗与HP刻度；含当前配乐'
            else:
                background=hub_music if request in ['10','13','25'] else battle_music
                old_mix+=bed(background,len(old_mix),start=3)
                new_mix+=bed(background,len(new_mix),start=3)
                context+='；叠加当前配乐0.50／音效0.65'
            row['scene_background_music']=True
        else:row['scene_background_music']=False
        row['scene_context']=context
        row['scene_mix_peak_dbfs']=db(np.abs(new_mix).max())
        if float(np.abs(new_mix).max())>=1:clipping.append([ident,'final music/sfx mix'])
        preview(REPORT/"audition"/(ident+"_original_context.mp3"),old_mix)
        preview(REPORT/"audition"/(ident+"_new_context.mp3"),new_mix)
        row['scene_fixture_path']=str((REPORT/'audition'/(ident+'_new_context.wav')).relative_to(ROOT))
        row['scene_fixture_sha256']=sha(ROOT/row['scene_fixture_path'])
        row["program_result"]="needs_investigation" if row["mono_cancellation_concern"] else "checks_passed_listening_pending"
        rows.append(row)
        cards.append(f'<article><h2>{request} · {html.escape(record["title"])}</h2><p>{html.escape(plan["role"])}</p><p class="facts">程序检查：{status_text(row)} · 逐条听审：未完成</p><p>{html.escape(context)}</p><div class="pair"><div><h3>原声场景模拟</h3><audio controls preload="none" src="audition/{ident}_original_context.mp3"></audio></div><div><h3>新音效场景模拟</h3><audio controls preload="none" src="audition/{ident}_new_context.mp3"></audio></div></div><p><a href="../sfx-20261024/index.html#request-{request}">单条原声／新声对比与手动备注</a></p></article>')
        markdown.append(f'| 音效 | {record["title"]} | {plan["role"]} | {row["scene_mix_peak_dbfs"]:.2f} | {row["mono_downmix_change_db"]:.2f} | {status_text(row)} | 待听审 |')
    result={"resources":rows,"resource_count":len(rows),"music_count":28,"sfx_count":41,
            'asset_sha256_by_id':{r['id']:r['sha256'] for r in music_report['tracks']+sfx_report['tracks']},
            "source_animation_variants":len(variants),"deduplicated_sound_patterns":len(unique),
            "normal_and_fast_forward_patterns_checked":len(traces),"traces":traces,
            "clipping_scenarios":clipping,"auditory_review":False,
            "audio_input_supported":False,"iphone_accessed":False,
            "scope":"Signal and deterministic scene-mix checks only; not hearing, semantic validation or a physical-device recording."}
    dump(REPORT/"review.json",result)
    (REPORT/"tracks.md").write_text('# 69 条音频逐项场景检查\n\n本表为信号与时序检查；独立本地模型的逐条审查另行记录。场景混音使用当前游戏倍率：配乐0.50、音效0.65；774个源动画去重后检查148种声音序列，各检查正常/3倍速度，不重打关卡或截图。\n\n| 类型 | 名称 | 场景／用途 | 示例峰值dBFS | 单声道变化dB | 程序结果 | 听审 |\n|---|---|---|---:|---:|---|---|\n'+'\n'.join(markdown)+'\n')
    (REPORT/"index.html").write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>69 条音频场景检查</title><style>*{box-sizing:border-box}body{margin:0;font:16px/1.65 system-ui,sans-serif;background:#f3f0e8;color:#243035}main{max-width:1100px;margin:auto;padding:24px}h1{line-height:1.3}h2{font-size:20px;line-height:1.45}h3{font-size:16px}article{padding:22px;margin:18px 0;background:#fffdf8;border-radius:12px;box-shadow:0 3px 15px #29312d10}.pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px}audio{width:100%}.facts{font-size:14px;color:#53676b}a{color:#355d68}:focus-visible{outline:none;box-shadow:0 0 0 4px #789c9b60}@media(max-width:680px){main{padding:15px}.pair{grid-template-columns:1fr}article{padding:17px}}</style><main><h1>69 条音频场景检查</h1><p>28 首配乐、41 个音效。这里提供逐项信号／时序结果和可播放的场景样例。音频内容由独立本地模型审查；完成状态按资源和混音文件哈希核对，详见审查报告。</p><p>音频样例按当前游戏倍率与源动画请求序列离线合成，不是实机录音。未做响度拉齐；播放器默认100%已包含游戏倍率。循环片段的第2秒是接头。兼容备用音不凭空增加触发。</p><p><a href="tracks.md">69 条逐项检查表</a> · <a href="review.json">详细信号与时序数据</a> · <a href="../sfx-20261024/index.html">原声／新音效并排对比</a></p>'''+''.join(cards)+'''</main><script>document.addEventListener('play',e=>{if(e.target.tagName==='AUDIO')document.querySelectorAll('audio').forEach(a=>{if(a!==e.target)a.pause()})},true)</script></html>''')
    print(json.dumps({"resources":len(rows),"patterns":len(traces),"clipping_scenarios":clipping,
                      "investigate":[r["id"] for r in rows if r["program_result"]=="needs_investigation"],
                      "auditory_review":False},ensure_ascii=False))
    index=REPORT/'index.html'
    index.write_text(index.read_text().replace('.mp3"','.wav"'))
    from audio_content_review_metadata import refresh_scene_review_status
    refresh_scene_review_status(PROJECT)

if __name__=="__main__":main()
