#!/usr/bin/env python3
"""Generate the de-duplicated original SFX replacement set locally, offline.

Use the installed StableAudio3SmallSFX MLX venv. The model checkout remains
read-only; unclipped FLOAT sources are retained outside the actual project.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"actual/reports/sfx-20261024"
SOURCE=ROOT/"source/sfx-20261024"
OUTPUT=ROOT/"actual/assets/sfx/20261024"
MODEL=Path("/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx")
FFMPEG="/opt/homebrew/bin/ffmpeg"
SR=44100
REVISION=2
NEGATIVE="music, musical melody, song, rhythm section, speech, voice, vocals, singing, choir, crowd, unrelated background ambience"


def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    tmp.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv,log=None):
    r=subprocess.run(argv,capture_output=True,text=True)
    if log:
        log.parent.mkdir(parents=True,exist_ok=True)
        log.write_text(r.stdout+r.stderr)
    if r.returncode: raise RuntimeError(f"Command failed {r.returncode}: {argv[0]}\n{r.stderr[-2500:]}")
    return r


def db(value):
    return float(20*math.log10(max(float(value),1e-12)))


def tracks():
    return json.loads((REPORT/"plan.json").read_text())["tracks"]


def artifact_revision(track):
    if track.get('runtime_asset_revision'):return int(track['runtime_asset_revision'])
    # Only these three effects changed in scene review; retain other valid cues.
    return 2 if str(track.get("request")) in {"21","23","53"} else 1


def seed_for(track):
    overrides=REPORT/"seed-overrides.json"
    if overrides.exists():
        saved=json.loads(overrides.read_text())
        if track["id"] in saved: return int(saved[track["id"]])
    return int(track.get("seed",20261024000+int(track["id"].split("_")[-1],16)))


def raw_paths(track,seed):
    p=SOURCE/"raw"/f"{track['id']}_{seed}_float.wav"
    return p,p.with_suffix(".json")


def target(track):
    return float(track.get("target_duration_seconds",track.get("duration_seconds",.7)))


def maximum(track):
    return float(track.get("max_duration_seconds",target(track)*1.25+.05))


def worker(track_id,seed):
    import numpy as np
    import soundfile as sf
    t=next(x for x in tracks() if x["id"]==track_id)
    seconds=float(t["generation_seconds"])
    request=str(t.get("request"))
    short_ui={"12","13","25","54","55"}
    if request in short_ui: seconds=min(seconds,1.0)
    if request=="16": seconds=min(seconds,1.4)
    if request=="21": seconds=min(seconds,1.8)
    if not .1<=seconds<=120: raise ValueError("Invalid Small-SFX duration")
    for rel in ["models/mlx/t5gemma_f16.npz","models/mlx/dit_sm-sfx_f16.npz","models/mlx/same_s_decoder_f32.npz"]:
        if not (MODEL/rel).is_file(): raise FileNotFoundError(rel)
    sys.path.insert(0,str(MODEL/"scripts"))
    import sa3_mlx
    raw,meta=raw_paths(t,seed)
    raw.parent.mkdir(parents=True,exist_ok=True)
    if raw.exists(): raise FileExistsError(raw)
    captured={}
    def save_float(path,a,sample_rate=SR):
        if not np.isfinite(a).all(): raise ValueError("Non-finite output")
        captured.update(raw_peak=float(np.abs(a).max()),raw_rms=float(np.sqrt(np.mean(a*a))),raw_samples_over_unity=int((np.abs(a)>1).sum()))
        sf.write(path,a.T,sample_rate,subtype="FLOAT")
    sa3_mlx.save_wav=save_float
    prompt="TrackType: SFX. "+t["prompt"]
    if request in short_ui:
        role={"12":"menu movement and health-counter updates","13":"cancelling a menu, with a very slight downward pitch bend","25":"advancing a dialogue line, extra gentle and short","54":"a neutral reserved compatibility cue, medium-low pitch","55":"a neutral reserved compatibility cue, medium-high pitch"}[request]
        prompt=f"TrackType: SFX. One isolated original retro game interface sound for {role}. A soft rounded electronic square-wave blip with a stable midrange tonal body lasting eighty milliseconds and a brief smooth release. Restrained clear synthetic pulse, high duty cycle and soft edges. Immediate onset. No physical impact, no mechanical click, no woody knock, no percussion, no ringing. One blip only, no melody or musical phrase, no voices, no background."
    if request=="16":
        prompt="TrackType: SFX. One compact original retro projectile air rush. A dense smooth half-second band-limited pink-noise whoosh with a rounded electronic low-mid body, immediate clear front and quick gentle decay. Even short rushing body, no sharp snap, no click, no impact, no explosion, no ringing, no repeated event, no voice or music."
    if request=="21":
        prompt="TrackType: SFX. One smooth compact original retro magic air sweep for wind and healing activation. A continuous soft rounded electronic resonant layer blended with dense filtered midrange noise. Balanced even body and softly rounded edges; a clear gentle opening, one short sweep, quick clean release. No isolated spark, no click, no physical impact, no voices or musical notes."
    if request=="23":
        prompt="TrackType: SFX. A finite eight-second retro fantasy teleportation energy texture. Continuous dense softly warbling electronic midrange buzz with filtered noise. Constant even amplitude and a clearly audible stable body from the very first instant until the end. No opening transient, no isolated event, no silence, no crescendo, no fade-in, no fade-out, no rhythm, no notes, no music, no voices. Designed to be stopped by a game animation after half a second or one second."
    if request=="41":
        prompt="TrackType: SFX. A finite eight-second neutral synthetic compatibility texture. Steady band-limited low-mid electronic noise with subdued coarse texture, continuous even amplitude from the first moment to the ending, no attacks or sharp peaks. No clicks, no transients, no sweeps, no rhythmic pulses, no musical tones, no implied combat action, no voice or music."
    if not t.get("loop") and not t.get("manual_stop"):
        prompt+=f" Single isolated one-shot, immediate attack and natural decay within {target(t):.2f} seconds. Then silence. No second event, no repeated sequence, no music or voice."
    else:
        prompt+=" Continuous stable sound-effect texture, immediate onset, no musical rhythm, no melody, no voice, no isolated repeated attack."
    negative=t.get("negative_prompt",NEGATIVE)
    if request in short_ui: negative+=", needle click, physical impact, mouse click, wooden knock, drum"
    sys.argv=["sa3_mlx.py","--dit","sm-sfx","--decoder","same-s","--seconds",str(seconds),"--steps","8","--cfg","1.5","--seed",str(seed),"--prompt",prompt,"--negative-prompt",negative,"--out",str(raw)]
    begin=time.monotonic()
    sa3_mlx.main()
    dump(meta,{"id":track_id,"seed":seed,"model":"local Stable Audio 3 sm-sfx/same-s","steps":8,"cfg":1.5,"prompt":prompt,"negative_prompt":negative,"seconds":seconds,"sample_rate":SR,"channels":2,"source_format":"FLOAT WAV","offline":True,"generation_wall_seconds":round(time.monotonic()-begin,3),"sha256":digest(raw),**captured})


def envelope(a,hop=220):
    import numpy as np
    count=len(a)//hop
    return np.sqrt(np.mean(a[:count*hop].reshape(count,hop,2).astype(np.float64)**2,axis=(1,2))),hop/SR


def edit_shot(a,t):
    import numpy as np
    env,dt=envelope(a)
    if not len(env) or float(env.max())<1e-6: raise RuntimeError("Silent generated SFX")
    # Detect meaningful onset relative to the event, retaining 3 ms pre-roll.
    onset_candidates=np.flatnonzero(env>=max(float(env.max())*.045,10**(-65/20)))
    onset=int(onset_candidates[0]*dt*SR) if len(onset_candidates) else 0
    start=max(0,onset-int(.003*SR))
    shifted=a[start:]
    ev,dt=envelope(shifted)
    nominal=target(t); cap=min(maximum(t),len(shifted)/SR)
    # Locate the first dominant transient, then a sustained low-energy tail.
    # Restrict attack search to the intended event rather than a later repeat.
    attack_range=max(1,min(len(ev),int(min(cap*.6,.45)/dt)))
    peak_index=int(np.argmax(ev[:attack_range]))
    peak=float(ev[:max(attack_range,peak_index+1)].max())
    threshold=max(peak*.035,10**(-65/20))
    minimum=max((peak_index+1)*dt,min(nominal*.5,.5))
    lower=int(minimum/dt); upper=max(lower+1,min(len(ev),int(cap/dt)))
    hold=max(2,int(min(.025,nominal*.1)/dt))
    natural=None
    for index in range(lower,max(lower,upper-hold)):
        if bool(np.all(ev[index:index+hold]<threshold)):
            natural=index*dt
            break
    if natural is not None:
        end_seconds=min(cap,natural+min(.035,nominal*.12))
        tail_mode="detected natural decay"
    else:
        # A local envelope minimum near the allotted event boundary allows a
        # smooth decay, but is explicitly reported rather than called natural.
        lower=max(lower,int(min(cap*.7,nominal*.8)/dt))
        stop=min(len(ev),int(cap/dt))
        index=lower+int(np.argmin(ev[lower:stop])) if stop>lower else stop-1
        end_seconds=min(cap,max(minimum,(index+1)*dt))
        tail_mode="bounded event; shaped low-energy tail"
    end=max(32,min(len(shifted),int(end_seconds*SR)))
    result=shifted[:end].copy()
    fadein=min(int(.001*SR),max(1,len(result)//40))
    fadeout=min(int((.012 if natural is not None else min(.06,nominal*.22))*SR),max(1,len(result)//5))
    result[:fadein]*=np.linspace(0,1,fadein)[:,None]
    result[-fadeout:]*=(.5+.5*np.cos(np.linspace(0,np.pi,fadeout)))[:,None]
    return result,{"method":"first meaningful onset, first transient, natural-decay search, bounded envelope tail", "source_start_seconds":start/SR,"source_end_seconds":(start+end)/SR,"source_leading_silence_trimmed_seconds":start/SR,"natural_tail_found":natural is not None,"tail_mode":tail_mode,"tail_fade_seconds":fadeout/SR,"target_seconds":nominal,"maximum_seconds":maximum(t)}


def edit_sustained(a,t):
    import numpy as np
    seconds=min(target(t),maximum(t),len(a)/SR)
    env,dt=envelope(a)
    onset_fraction=.3 if str(t.get("request"))=="53" else .04
    active=np.flatnonzero(env>max(float(env.max())*onset_fraction,10**(-65/20)))
    start=max(0,int(active[0]*dt*SR)-int(.003*SR)) if len(active) else 0
    length=min(len(a)-start,int(seconds*SR))
    result=a[start:start+length].copy()
    if t.get("loop"):
        # Stable texture loop: match energy/spectral windows, preserving the
        # requested period. No musical beat assumptions for non-musical SFX.
        overlap=min(.2,seconds*.08)
        k=int(overlap*SR)
        if len(a)-start>=length+k:
            extra=a[start+length:start+length+k]
            w=(.5-.5*np.cos(np.linspace(0,np.pi,k)))[:,None]
            result[:k]=extra*(1-w)+result[:k]*w
        else:
            length-=k
            w=(.5-.5*np.cos(np.linspace(0,np.pi,k)))[:,None]
            result=np.concatenate([result[-k:]*(1-w)+result[:k]*w,result[k:-k]])
        editing={"method":"continuous non-musical texture, cosine equal-gain wrap","loop_offset_seconds":0,"overlap_seconds":overlap}
    else:
        fadein=min(int(.002*SR),len(result)//10)
        fadeout=min(int(.04*SR),len(result)//10)
        result[:fadein]*=np.linspace(0,1,fadein)[:,None]
        result[-fadeout:]*=(.5+.5*np.cos(np.linspace(0,np.pi,fadeout)))[:,None]
        editing={"method":"manual-stop texture; preserve finite source semantics, 2ms onset/40ms natural stop smoothing","loop_offset_seconds":0}
    return result,{**editing,"source_start_seconds":start/SR,"target_seconds":target(t),"maximum_seconds":maximum(t)}


def measure(path,a,log=None):
    import numpy as np
    ev,dt=envelope(a)
    active=ev[ev>max(float(ev.max())*.03,10**(-55/20))]
    onset=np.flatnonzero(ev>max(float(ev.max())*.03,10**(-55/20)))
    r=command([FFMPEG,"-hide_banner","-nostdin","-i",str(path),"-af","ebur128=peak=true","-f","null","-"],log or REPORT/"logs"/(path.stem+"_decoded.log"))
    lufs=re.findall(r"\bI:\s*([-+\d.]+) LUFS",r.stderr)
    true_peaks=re.findall(r"Peak:\s*([-+\d.]+) dBFS",r.stderr)
    levels={"integrated_lufs":float(lufs[-1]) if len(a)/SR>=.4 and lufs and float(lufs[-1])>-65 else None,"true_peak_dbtp":float(true_peaks[-1]) if true_peaks else None}
    if levels["true_peak_dbtp"] is None: raise RuntimeError("Missing true-peak measurement")
    interior=ev[max(1,int(.05/dt)):-max(1,int(.05/dt))]
    quiet=interior<10**(-60/20)
    longest=run=0
    for q in quiet:
        run=run+1 if q else 0; longest=max(longest,run)
    return {"seconds":len(a)/SR,"sample_rate":SR,"channels":2,"rms_dbfs":db(np.sqrt(np.mean(a.astype(np.float64)**2))),"active_rms_dbfs":db(np.sqrt(np.mean(active**2))) if len(active) else -240,"sample_peak_dbfs":db(np.abs(a).max()),"first_50ms_rms_dbfs":db(np.sqrt(np.mean(a[:2205].astype(np.float64)**2))),"nonfinite_samples":int((~np.isfinite(a)).sum()),"samples_at_or_above_full_scale":int((np.abs(a)>=1).sum()),"leading_onset_seconds":float(onset[0]*dt) if len(onset) else None,"longest_internal_silence_seconds":longest*dt,"last_10ms_rms_dbfs":db(np.sqrt(np.mean(a[-441:].astype(np.float64)**2))),"first_last_sample_delta":float(np.abs(a[0]-a[-1]).max()),"lufs_note":"Integrated loudness is not meaningful for events shorter than 400ms; use active RMS and true peak." if len(a)/SR<.4 else "Measured gated integrated loudness",**levels}


def original_profile(t):
    request=str(t.get("request",t.get("source_request",t["id"].split("_")[-1]))).replace("0x","").upper()
    rows=json.loads((REPORT/"source-signal-profile.json").read_text())["rows"]
    return next(r for r in rows if r["request"]==request)


def limits(t):
    category=str(t.get("category",t.get("role",""))).lower()
    request=str(t.get("request",t.get("source_request",t["id"].split("_")[-1]))).replace("0x","").upper()
    is_ui=category.startswith("ui") or request in {"10","11","12","13","25","54","55"}
    original=original_profile(t)
    old_rms=float(original["active_rms_dbfs"])
    old_peak=float(original["peak_dbfs"])
    if is_ui: return min(-22.0,old_rms),min(-10.0,old_peak+1)
    if t.get("manual_stop") or t.get("loop"): return min(-23.0,old_rms),min(-8.0,old_peak+1)
    if category in {"physical","impact","hit","weapon"} or request in {"02","03","04","22","43"}: return min(-20.0,old_rms+2),min(-6.0,old_peak+2)
    return min(-22.0,old_rms+1),min(-7.0,old_peak+1)


def master(t,seed):
    import numpy as np
    import soundfile as sf
    raw,meta=raw_paths(t,seed)
    source=json.loads(meta.read_text())
    a,sr=sf.read(raw,dtype="float32",always_2d=True)
    if sr!=SR or a.shape[1]!=2 or not np.isfinite(a).all(): raise RuntimeError("Unexpected source format")
    edited,editing=edit_sustained(a,t) if t.get("manual_stop") or t.get("loop") else edit_shot(a,t)
    target_rms,peak_ceiling=limits(t)
    env,dt=envelope(edited)
    active=env[env>max(float(env.max())*.03,10**(-55/20))]
    active_rms=db(np.sqrt(np.mean(active**2))) if len(active) else -240
    peak=db(np.abs(edited).max())
    shaping={"applied":False}
    if target_rms-active_rms-(peak_ceiling-peak)>6 and not str(t.get("category","")).startswith("ui"):
        # A bounded soft knee rounds only exceptional transient tips; it is
        # not hard clipping, resynthesis, or a blanket loudness compressor.
        original_peak=float(np.abs(edited).max())
        knee=original_peak*.4; width=original_peak*.6
        magnitude=np.abs(edited)
        mask=magnitude>knee
        shaped=np.where(mask,knee+width*np.tanh(1.85*(magnitude-knee)/width)/1.85,magnitude)
        edited=np.sign(edited)*shaped
        env,dt=envelope(edited)
        active=env[env>max(float(env.max())*.03,10**(-55/20))]
        active_rms=db(np.sqrt(np.mean(active**2)))
        peak=db(np.abs(edited).max())
        shaping={"applied":True,"method":"smooth tanh soft knee only above 40 percent of source peak","affected_samples":int(mask.sum()),"total_samples":int(mask.size),"maximum_peak_reduction_db":db(original_peak)-peak,"reason":"excessive transient crest made useful event energy too quiet under original peak budget"}
    gain_db=min(target_rms-active_rms,peak_ceiling-peak)
    mastered=edited*10**(gain_db/20)
    # Absolute activity gating can change after large attenuation; settle the
    # final active-RMS target using the same original-reference threshold.
    for _ in range(3):
        settled,_=envelope(mastered)
        selected=settled[settled>max(float(settled.max())*.03,10**(-55/20))]
        measured_rms=db(np.sqrt(np.mean(selected**2))) if len(selected) else -240
        if measured_rms<=target_rms+.1: break
        correction=target_rms-measured_rms
        gain_db+=correction;mastered*=10**(correction/20)
    scene_envelope=None
    if str(t.get("request"))=="53":
        # Arrow-rain replaces this wash at contact, only three native ticks
        # after onset. Match that short lead-in rather than the whole 4s file.
        # The prior global-RMS master made the actual 50ms window 12.7dB
        # louder than the original despite a quieter whole-file average.
        time=np.arange(len(mastered))/SR
        blend=np.clip((time-.06)/.24,0,1)
        rise=.5-.5*np.cos(np.pi*blend)
        floor=10**(-10/20)
        mastered*= (floor+(1-floor)*rise)[:,None]
        scene_envelope={"reason":"verified 53 lead-in lasts three source ticks before hit/miss replacement",
                        "attenuation_db":-10,"hold_seconds":.06,"smooth_recovery_end_seconds":.30}
    master_path=SOURCE/"masters"/(t["id"]+"_master_float.wav")
    master_path.parent.mkdir(parents=True,exist_ok=True)
    sf.write(master_path,mastered,SR,subtype="FLOAT")
    out=OUTPUT/(t["id"]+".ogg");out.parent.mkdir(parents=True,exist_ok=True)
    with sf.SoundFile(out,mode="w",samplerate=SR,channels=2,format="OGG",subtype="VORBIS",compression_level=.6) as f:
        for i in range(0,len(mastered),8192): f.write(mastered[i:i+8192])
    decoded,rate=sf.read(out,dtype="float32",always_2d=True)
    metrics=measure(out,decoded)
    errors=[]
    if rate!=SR or decoded.shape[1]!=2: errors.append("format")
    if metrics["nonfinite_samples"] or metrics["samples_at_or_above_full_scale"]: errors.append("invalid_or_clipped_samples")
    if metrics["true_peak_dbtp"]>-3: errors.append("insufficient_sfx_peak_headroom")
    if scene_envelope is None and metrics["active_rms_dbfs"]<target_rms-6: errors.append("unexpectedly_quiet")
    if scene_envelope is not None:
        original_map=json.loads((ROOT/"actual/data/legacy/full_audio.json").read_text())
        original_path=ROOT/"actual"/original_map["sfx_by_request"]["53"]["path"].removeprefix("res://")
        original_audio,_=sf.read(original_path,dtype="float32",always_2d=True)
        window=int(.05*SR)
        current_window=db(np.sqrt(np.mean(decoded[:window].astype(np.float64)**2)))
        original_window=db(np.sqrt(np.mean(original_audio[:window].astype(np.float64)**2)))
        metrics.update(scene_window_50ms_rms_dbfs=current_window,
                       source_window_50ms_rms_dbfs=original_window,
                       scene_window_delta_db=current_window-original_window)
        if not -5<=current_window-original_window<=3.5:errors.append("53_contact_window_level_mismatch")
    if metrics["seconds"]>maximum(t)+.005: errors.append("duration_exceeds_event_budget")
    if metrics["seconds"]<min(.035,target(t)*.3): errors.append("event_too_short")
    if metrics["leading_onset_seconds"] is None or metrics["leading_onset_seconds"]>.035: errors.append("delayed_attack")
    if str(t.get("request"))=="53" and metrics["first_50ms_rms_dbfs"]<metrics["active_rms_dbfs"]-9: errors.append("arrow_prelude_too_weak_in_actual_50ms_window")
    if not t.get("loop") and metrics["last_10ms_rms_dbfs"]>-25: errors.append("tail_cut_at_high_energy")
    record={"id":t["id"],"title":t.get("title",t["id"]),"request":t.get("request",t.get("source_request",t["id"].split("_")[-1])),"revision":artifact_revision(t),"status":"signal_checks_passed" if not errors else "signal_checks_failed","errors":errors,"runtime_path":str(out.relative_to(ROOT)),"resource_path":"res://"+str(out.relative_to(ROOT/"actual")),"bytes":out.stat().st_size,"sha256":digest(out),"duration_seconds":metrics["seconds"],"loop":bool(t.get("loop",False)),"loop_offset_seconds":0.0,"manual_stop":bool(t.get("manual_stop",False)),"default_enabled":t.get("default_enabled",True),"sample_rate":SR,"channels":2,"codec":"vorbis","source":source,"source_path":str(raw.relative_to(ROOT)),"master_path":str(master_path.relative_to(ROOT)),"editing":editing,"mastering":{"method":"constant active-RMS gain with category peak ceiling","target_active_rms_dbfs":target_rms,"sample_peak_ceiling_dbfs":peak_ceiling,"gain_db":gain_db,"runtime_gain_unchanged":True},"metrics":metrics,"auditory_review":False,"auditory_review_note":"Objective signal/timing checks only; sound identity, absence of speech/music and subjective fatigue need listening."}
    baseline=original_profile(t)
    record["source_baseline"]=baseline
    record["mastering"]["transient_shaping"]=shaping
    if scene_envelope is not None:record["mastering"]["scene_envelope"]=scene_envelope
    record["mastering"].update({"active_rms_comparison_method":"220-sample (approximately 5ms) stereo RMS windows; active=max(0.03*max_window_rms,-55dBFS), matching source baseline", "active_rms_delta_from_original_db":metrics["active_rms_dbfs"]-baseline["active_rms_dbfs"],"sample_peak_delta_from_original_db":metrics["sample_peak_dbfs"]-baseline["peak_dbfs"],"basis":"Preserve original relative levels: UI not louder in active RMS; ordinary impacts at most +2dB and magic +1dB; sustained textures capped at -23dBFS active RMS."})
    dump(REPORT/"tracks"/(t["id"]+".json"),record)
    dump(REPORT/"attempts"/(t["id"]+f"_{seed}.json"),record)
    print(json.dumps({"id":record["id"],"status":record["status"],"seconds":round(metrics["seconds"],4),"onset_ms":round((metrics['leading_onset_seconds'] or 0)*1000,2),"rms":round(metrics["active_rms_dbfs"],2),"true_peak":metrics["true_peak_dbtp"],"natural_tail":editing.get("natural_tail_found"),"errors":errors},ensure_ascii=False),flush=True)
    if errors: raise RuntimeError(f"{t['id']}: {errors}")
    return record


def review(records,plans):
    from audio_review_page import build_sfx_comparison
    build_sfx_comparison(records, plans, REPORT, ROOT/"actual", FFMPEG)


def produce(t,args,single):
    seed=args.seed if args.seed is not None and single else seed_for(t)
    raw,meta=raw_paths(t,seed); previous=REPORT/"tracks"/(t["id"]+".json")
    if previous.exists():
        reviewed=json.loads(previous.read_text())
        if reviewed.get('production_method')=='audio_review_refinement':
            asset=ROOT/reviewed['runtime_path']
            if not args.remaster and asset.exists() and digest(asset)==reviewed['sha256']:
                print(f"RESUME preserve audio-reviewed refinement {t['id']}",flush=True);return
            raise RuntimeError('This cue uses an audio-guided or UI-synthesis recipe; rebuild its candidate with refine_sfx_from_audio.py/refine_ui_sounds.py, review it, then publish. Refusing to revert it through the old text-only recipe.')
    if previous.exists() and not args.remaster:
        old=json.loads(previous.read_text());p=ROOT/old["runtime_path"]
        if old.get("revision")==artifact_revision(t) and old["source"]["seed"]==seed and old["status"]=="signal_checks_passed" and p.exists() and digest(p)==old["sha256"]:
            print(f"RESUME skip verified {t['id']}",flush=True);return
    if not raw.exists() or not meta.exists():
        if args.master_only: raise FileNotFoundError(raw)
        print(f"GENERATE {t['id']} seed={seed}",flush=True)
        command([sys.executable,"-B",__file__,"--worker",t["id"],"--seed",str(seed)],REPORT/"logs"/(t["id"]+"_generation.log"))
    master(t,seed)
    if args.seed is not None and single:
        path=REPORT/"seed-overrides.json"
        overrides=json.loads(path.read_text()) if path.exists() else {}
        overrides[t["id"]]=seed;dump(path,overrides)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--worker");ap.add_argument("--seed",type=int);ap.add_argument("--ids",nargs="*");ap.add_argument("--master-only",action="store_true");ap.add_argument("--report-only",action="store_true");ap.add_argument("--remaster",action="store_true");ap.add_argument("--keep-going",action="store_true");args=ap.parse_args()
    for key in ["HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","PYTHONDONTWRITEBYTECODE"]: os.environ[key]="1"
    if args.worker: return worker(args.worker,args.seed)
    SOURCE.mkdir(parents=True,exist_ok=True);(SOURCE/".gdignore").touch();(REPORT/"logs").mkdir(parents=True,exist_ok=True)
    plans=tracks();lookup={t["id"]:t for t in plans};selected=[lookup[i] for i in args.ids] if args.ids else plans
    failures=[]
    for t in ([] if args.report_only else selected):
        try:
            produce(t,args,len(selected)==1)
        except Exception as error:
            if not args.keep_going: raise
            failures.append({"id":t["id"],"error":str(error)})
            print(f"NEEDS_REPAIR {t['id']}: {error}",flush=True)
    records=[]
    for t in plans:
        p=REPORT/"tracks"/(t["id"]+".json")
        if p.exists():
            record=json.loads(p.read_text())
            record.update(default_enabled=t.get("default_enabled",True),title=t.get("title",record["title"]))
            dump(p,record);records.append(record)
    from audio_content_review_metadata import attach_content_reviews,all_reviewed,sync_runtime_review_metadata
    attach_content_reviews(records,ROOT/'actual')
    sync_runtime_review_metadata(records,ROOT/'actual/data/sound_effects.json')
    for record in records:dump(REPORT/'tracks'/(record['id']+'.json'),record)
    dump(REPORT/"generation-report.json",{"schema":1,"production_revision":max([REVISION]+[r['revision'] for r in records]),"model":"Local Stable Audio 3; reviewed refinements include reference-conditioned generation and UI synthesis", "planned_tracks":len(plans),"completed_tracks":len(records),"signal_checks_passed":sum(r["status"]=="signal_checks_passed" for r in records),"auditory_review":all_reviewed(records),"human_listening":False,"tracks":records})
    review(records,plans)
    if failures:
        dump(REPORT/"batch-failures.json",failures)
        raise RuntimeError(f"{len(failures)} isolated SFX require repair; other tracks completed")


if __name__=="__main__": main()
