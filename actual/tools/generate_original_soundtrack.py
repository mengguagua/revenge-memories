#!/usr/bin/env python3
"""Offline, resumable SA3 soundtrack production; never mutates the model checkout.

Run using StableAudio3SmallSFX/optimized/mlx/.venv/bin/python. A worker
process owns Metal for one cue, writes an unclipped FLOAT source, and exits.
Mastering/analysis use numpy, soundfile and the installed ffmpeg only.
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

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "actual/reports/soundtrack-20261024"
SOURCE = ROOT / "source/audio-20261024"
OUTPUT = ROOT / "actual/assets/music/20261024"
MODEL = Path("/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx")
FFMPEG = "/opt/homebrew/bin/ffmpeg"
SR = 44100
REVISION = 2
NEGATIVE = "vocals, singing, speech, lyrics, choir, crowd, harsh distortion, loud sound effects, abrupt stop"


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def command(argv, log=None):
    result = subprocess.run(argv, capture_output=True, text=True)
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {argv[0]}\n{result.stderr[-3000:]}")
    return result


def tracks():
    return json.loads((REPORT / "plan.json").read_text())["tracks"]


def source_paths(track, seed):
    raw = SOURCE / "raw" / f"{track['id']}_{seed}_float.wav"
    return raw, raw.with_suffix(".json")


def seed_for(track):
    return int(track.get("seed", 2026102400 + next(i for i, t in enumerate(tracks(), 1) if t["id"] == track["id"])))


def worker(track_id, seed):
    import numpy as np
    import soundfile as sf
    track = next(t for t in tracks() if t["id"] == track_id)
    seconds = float(track["generation_seconds"] if track["loop"] else min(8,track["duration_seconds"]+2))
    if not 0 < seconds <= 120:
        raise ValueError("Small-Music production duration must be in (0, 120] seconds")
    for relative in ("models/mlx/t5gemma_f16.npz", "models/mlx/dit_sm-music_f16.npz", "models/mlx/same_s_decoder_f32.npz"):
        if not (MODEL / relative).is_file():
            raise FileNotFoundError(f"Offline model missing: {relative}")
    sys.path.insert(0, str(MODEL / "scripts"))
    import sa3_mlx
    raw, meta = source_paths(track, seed)
    raw.parent.mkdir(parents=True, exist_ok=True)
    if raw.exists():
        raise FileExistsError(raw)
    captured = {}

    def save_float(path, audio, sample_rate=SR):
        if not np.isfinite(audio).all():
            raise ValueError("Model emitted non-finite audio")
        captured.update(raw_peak=float(np.abs(audio).max()), raw_rms=float(np.sqrt(np.mean(audio**2))), raw_samples_over_unity=int((np.abs(audio) > 1).sum()))
        sf.write(path, audio.T, sample_rate, subtype="FLOAT")

    sa3_mlx.save_wav = save_float
    prompt = "TrackType: Music, VocalType: Instrumental. " + track["prompt"]
    if track["loop"]:
        prompt += " Maintain steady repeating musical phrases throughout, no long introduction, no fade-out or final ending."
    else:
        prompt += f" A single short complete musical notification, not a song or repeating loop. Resolve the final cadence by {track['duration_seconds']} seconds, then let the final note decay naturally into quiet silence. No new phrase after the final chord."
    sys.argv = ["sa3_mlx.py", "--dit", "sm-music", "--decoder", "same-s", "--seconds", str(seconds), "--steps", "8", "--cfg", "1.5", "--seed", str(seed), "--prompt", prompt, "--negative-prompt", NEGATIVE, "--out", str(raw)]
    start = time.monotonic()
    sa3_mlx.main()
    dump(meta, {"track_id": track_id, "seed": seed, "model": "local Stable Audio 3 sm-music/same-s", "steps": 8, "cfg": 1.5, "prompt": prompt, "negative_prompt": NEGATIVE, "seconds": seconds, "sample_rate": SR, "channels": 2, "source_format": "FLOAT WAV", "offline": True, "generation_wall_seconds": round(time.monotonic()-start, 3), "sha256": digest(raw), **captured})


def db(value):
    return float(20 * math.log10(max(float(value), 1e-12)))


def analyze_signal(audio):
    import numpy as np
    hop = 441
    frames = len(audio) // hop
    rms = np.sqrt(np.mean(audio[:frames*hop].reshape(frames, hop, 2).astype(np.float64)**2, axis=(1, 2)))
    quiet = rms < 10**(-55/20)
    longest = run = 0
    for q in quiet[25:-25]:
        run = run + 1 if q else 0
        longest = max(longest, run)
    deriv = np.abs(np.diff(audio, axis=0))
    seam = float(np.max(np.abs(audio[-1]-audio[0])))
    return {"seconds": len(audio)/SR, "rms_dbfs": db(np.sqrt(np.mean(audio.astype(np.float64)**2))), "sample_peak_dbfs": db(np.abs(audio).max()), "nonfinite_samples": int((~np.isfinite(audio)).sum()), "samples_at_or_above_full_scale": int((np.abs(audio) >= 1).sum()), "interior_silence_longest_seconds": longest/100, "silent_frame_fraction": float(quiet.mean()), "rms_10ms_p10_dbfs": db(np.quantile(rms, .1)), "rms_10ms_p90_dbfs": db(np.quantile(rms, .9)), "seam_max_sample_delta": seam, "derivative_p99": float(np.quantile(deriv, .99)), "seam_delta_over_derivative_p99": seam/max(float(np.quantile(deriv,.99)),1e-9)}


def rhythm_features(audio, target_bpm):
    """Spectral flux tempo estimate; no claim that this establishes musical meter."""
    import numpy as np
    mono = audio.mean(axis=1)[::2]
    rate = SR/2
    nfft, hop = 2048, 441
    count = (len(mono)-nfft)//hop + 1
    freq = np.fft.rfftfreq(nfft, 1/rate)
    win = np.hanning(nfft)
    features, flux = [], []
    previous = None
    # Chroma + six coarse timbre bands + log energy for loop-window matching.
    midi = np.zeros(len(freq), dtype=int)
    usable = freq > 65
    midi[usable] = np.rint(69+12*np.log2(freq[usable]/440)).astype(int)
    for i in range(count):
        spectrum = np.abs(np.fft.rfft(mono[i*hop:i*hop+nfft]*win))
        logspec = np.log1p(spectrum)
        flux.append(float(np.maximum(logspec-previous, 0).mean()) if previous is not None else 0)
        previous = logspec
        chroma = np.array([spectrum[usable & (midi%12 == c)].sum() for c in range(12)])
        chroma /= max(float(np.linalg.norm(chroma)), 1e-9)
        bands = np.array([spectrum[(freq >= lo)&(freq < hi)].sum() for lo,hi in [(0,150),(150,400),(400,900),(900,2000),(2000,4500),(4500,11025)]])
        bands /= max(float(np.linalg.norm(bands)), 1e-9)
        energy = math.log10(max(float(np.linalg.norm(spectrum)),1e-8))
        features.append(np.concatenate([chroma, bands*.7, [energy*.3]]))
    features = np.asarray(features)
    flux = np.asarray(flux)
    centered = flux - flux.mean()
    frame_rate = rate/hop
    lo, hi = int(frame_rate*60/180), int(frame_rate*60/60)
    scores = []
    for lag in range(lo, hi+1):
        norm = np.linalg.norm(centered[:-lag])*np.linalg.norm(centered[lag:])
        correlation = float(np.dot(centered[:-lag],centered[lag:])/max(norm,1e-10))
        bpm = frame_rate*60/lag
        prior = math.exp(-.5*(math.log2(bpm/target_bpm)/.45)**2)
        scores.append((correlation*(.75+.25*prior),lag,correlation))
    _, lag, confidence = max(scores)
    estimate = frame_rate*60/lag
    bpm_used = estimate if confidence >= .08 else target_bpm
    return features, flux, frame_rate, {"target_bpm": target_bpm, "spectral_flux_estimate_bpm": round(estimate, 3), "autocorrelation": round(confidence,4), "alignment_bpm": round(bpm_used,3), "alignment_basis": "spectral_flux_estimate" if confidence >= .08 else "target_fallback_low_confidence", "note": "Algorithmic pulse estimate; musical beat/meter and perceived loop coherence require listening."}


def make_loop(audio, target_bpm):
    import numpy as np
    features, flux, fps, rhythm = rhythm_features(audio, target_bpm)
    duration = len(audio)/SR
    beat = 60/rhythm["alignment_bpm"]
    # Search whole four-bar multiples at a shared beat phase. Match entire
    # two-beat windows, not merely sample zero-crossings or a fixed tiny fade.
    phase_scores = []
    for phase in np.linspace(0,beat,32,endpoint=False):
        times = np.arange(phase,duration,beat)
        indices = np.clip(np.rint(times*fps).astype(int),0,len(flux)-1)
        phase_scores.append((float(flux[indices].mean()),float(phase)))
    phase = max(phase_scores)[1]
    fade = min(2*beat,1.8)
    candidates = []
    low = max(24, duration*.55)
    for bars in range(4,65,4):
        period = bars*4*beat
        length = period+fade
        if not low <= period <= duration-fade-1:
            continue
        for start in np.arange(phase, min(14,duration-length), beat):
            if start < .2:
                continue
            end = start+length
            a,b = int(start*fps),int((end-fade)*fps)
            k = max(2,int(fade*fps))
            if min(a,b)<0 or max(a,b)+k>len(features):
                continue
            first,last=features[a:a+k],features[b:b+k]
            mean_diff=float(np.linalg.norm(first.mean(0)-last.mean(0)))
            sequence_diff=float(np.sqrt(np.mean((first-last)**2)))
            energy_gap=float(abs(first[:,-1].mean()-last[:,-1].mean()))/.3*20
            # Reject fade-outs, near silence and large level changes.
            ia,ib=int(start*SR),int((end-fade)*SR)
            ka=int(fade*SR)
            if min(db(np.sqrt(np.mean(audio[ia:ia+ka]**2))),db(np.sqrt(np.mean(audio[ib:ib+ka]**2)))) < -38:
                continue
            score = mean_diff+sequence_diff+max(0,energy_gap-2)*.1+(1-period/duration)*.25
            candidates.append((score,start,end,bars,mean_diff,sequence_diff,energy_gap))
    if not candidates:
        raise RuntimeError("No sustained phrase-length loop candidate; regenerate this cue")
    chosen = min(candidates)
    score,start,end,bars,mean_diff,sequence_diff,energy_gap=chosen
    s,e,k=int(start*SR),int(end*SR),int(fade*SR)
    weight=(.5-.5*np.cos(np.linspace(0,np.pi,k,endpoint=True)))[:,None]
    bridge=audio[e-k:e]*(1-weight)+audio[s:s+k]*weight
    result=np.concatenate([bridge,audio[s+k:e-k]],axis=0).astype(np.float32)
    return result,{"method":"four-bar-multiple pulse alignment and two-beat chroma/timbre/energy window search; cosine equal-gain overlap", "source_start_seconds":round(start,6),"source_end_seconds":round(end,6),"source_phrase_bars_under_estimated_pulse":bars,"overlap_seconds":k/SR,"loop_offset_seconds":0.0,"candidate_count":len(candidates),"feature_mean_distance":round(mean_diff,5),"feature_sequence_rmse":round(sequence_diff,5),"crossfade_window_energy_gap_db":round(energy_gap,3),"selection_score":round(score,5),"rhythm":rhythm,"auditory_review":False,"auditory_review_note":"No local auditory perception tool available; algorithmic matching does not certify musical structure."}


def make_jingle(audio, target_seconds):
    import numpy as np
    # Preserve onset and choose a nearby low-energy cadence/tail; do not hard
    # trim at the requested nominal duration when the generated phrase continues.
    hop=441
    frames=len(audio)//hop
    env=np.sqrt(np.mean(audio[:frames*hop].reshape(frames,hop,2)**2,axis=(1,2)))
    active=np.flatnonzero(env>max(float(env.max())*.025,10**(-55/20)))
    if not len(active):
        raise RuntimeError("Silent generated jingle")
    start=max(0,int(active[0]*hop-.03*SR))
    min_end=max(target_seconds*.85,3)
    max_end=min(len(audio)/SR-.15,max(target_seconds+4,8))
    smooth=np.convolve(env,np.ones(25)/25,mode="same")
    a,b=int(min_end*100),int(max_end*100)
    local=smooth[a:b]
    # Prefer a convincing decay. If there is no decay near the target, retain
    # the whole generated phrase and explicitly record the longer duration.
    threshold=float(env.max())*.08
    lows=np.flatnonzero(local<threshold)
    natural=bool(len(lows))
    end_time=(a+int(lows[0]))/100+.35 if natural else len(audio)/SR
    end=min(len(audio),int(end_time*SR))
    result=audio[start:end].copy()
    fadein=min(int(.012*SR),len(result)//10)
    fadeout=min(int((.25 if natural else 1.6)*SR),len(result)//3)
    result[:fadein]*=np.linspace(0,1,fadein)[:,None]
    result[-fadeout:]*=(.5+.5*np.cos(np.linspace(0,np.pi,fadeout)))[:,None]
    return result,{"method":"preserve full onset, search low-energy cadence; retain full source when no natural early tail found", "source_start_seconds":start/SR,"source_end_seconds":end/SR,"requested_nominal_seconds":target_seconds,"natural_early_tail_found":natural,"tail_fade_seconds":fadeout/SR,"auditory_review":False}


def loudness(path, log=None):
    result=command([FFMPEG,"-hide_banner","-nostdin","-i",str(path),"-af","loudnorm=I=-18:TP=-2:LRA=11:print_format=json","-f","null","-"],log)
    blocks=re.findall(r'\{\s*"input_i".*?\}',result.stderr,re.S)
    if not blocks:
        raise RuntimeError("Missing FFmpeg loudness measurement")
    raw=json.loads(blocks[-1])
    return raw,{"integrated_lufs":float(raw["input_i"]),"true_peak_dbtp":float(raw["input_tp"]),"loudness_range_lu":float(raw["input_lra"])}


def master(track, seed):
    import numpy as np
    import soundfile as sf
    raw,meta=source_paths(track,seed)
    source_meta=json.loads(meta.read_text())
    audio,sr=sf.read(raw,dtype="float32",always_2d=True)
    if sr != SR or audio.shape[1] != 2 or not np.isfinite(audio).all():
        raise RuntimeError("Unexpected source audio format")
    if track["loop"]:
        edited,edit=make_loop(audio,float(track["bpm"]))
    else:
        edited,edit=make_jingle(audio,float(track["duration_seconds"]))
    premaster=SOURCE/"masters"/(track["id"]+"_edit_float.wav")
    premaster.parent.mkdir(parents=True,exist_ok=True)
    sf.write(premaster,edited,SR,subtype="FLOAT")
    measured,_=loudness(premaster,REPORT/"logs"/(track["id"]+"_premaster.log"))
    target=-18 if track["loop"] else -19
    final_master=SOURCE/"masters"/(track["id"]+"_master_float.wav")
    # Constant gain preserves the deliberately continuous loop envelope. Avoid
    # a time-varying limiter reacting differently at the beginning/end.
    gain_db=min(target-float(measured["input_i"]),-2.0-float(measured["input_tp"]))
    mastered=edited*10**(gain_db/20)
    sf.write(final_master,mastered,SR,subtype="FLOAT")
    dump(REPORT/"logs"/(track["id"]+"_master.json"),{"method":"constant gain; target loudness limited by -2 dBTP ceiling", "gain_db":gain_db,"target_lufs":target,"input_measurement":measured})
    path=OUTPUT/(track["id"]+".ogg")
    OUTPUT.mkdir(parents=True,exist_ok=True)
    # Installed ffmpeg has no libvorbis encoder; reuse bundled libsndfile's
    # real Vorbis encoder without installing or changing any dependencies.
    # libsndfile's Vorbis encoder requires bounded writes here: handing the
    # whole multi-million-frame array to one write can crash its native code.
    with sf.SoundFile(path,mode="w",samplerate=SR,channels=2,format="OGG",subtype="VORBIS",compression_level=.6) as encoded:
        for start in range(0,len(mastered),8192):
            encoded.write(mastered[start:start+8192])
    decoded,rate=sf.read(path,dtype="float32",always_2d=True)
    metrics=analyze_signal(decoded)
    _,levels=loudness(path,REPORT/"logs"/(track["id"]+"_decoded.log"))
    errors=[]
    if rate != SR or decoded.shape[1] !=2: errors.append("bad_format")
    if metrics["nonfinite_samples"]: errors.append("nonfinite")
    if metrics["samples_at_or_above_full_scale"]: errors.append("full_scale_samples")
    if levels["true_peak_dbtp"] > -1: errors.append("true_peak_headroom_below_1db")
    if metrics["rms_dbfs"] < -32: errors.append("unexpectedly_quiet")
    if track["loop"] and metrics["interior_silence_longest_seconds"] > 1: errors.append("interior_silence")
    if track["loop"] and metrics["seam_delta_over_derivative_p99"] > 1.5: errors.append("loop_sample_discontinuity")
    if metrics["seconds"] < (25 if track["loop"] else 2): errors.append("too_short")
    record={"id":track["id"],"title":track["title"],"kind":track["kind"],"revision":REVISION,"status":"signal_checks_passed" if not errors else "signal_checks_failed","errors":errors,"runtime_path":str(path.relative_to(ROOT)),"resource_path":"res://"+str(path.relative_to(ROOT/"actual")),"bytes":path.stat().st_size,"sha256":digest(path),"duration_seconds":metrics["seconds"],"loop":track["loop"],"loop_offset_seconds":0.0,"sample_rate":rate,"channels":decoded.shape[1],"codec":"vorbis","vorbis_quality":4,"target_integrated_lufs":target,"source":source_meta,"source_path":str(raw.relative_to(ROOT)),"master_path":str(final_master.relative_to(ROOT)),"editing":edit,"metrics":{**metrics,**levels},"auditory_review":False,"auditory_review_note":"Objective measurements only; no claim of human or model listening. Music content, absence of vocal textures and phrase coherence still need listening."}
    dump(REPORT/"tracks"/(track["id"]+".json"),record)
    print(json.dumps({"id":record["id"],"status":record["status"],"seconds":round(metrics["seconds"],3),"lufs":levels["integrated_lufs"],"true_peak":levels["true_peak_dbtp"],"bytes":record["bytes"],"errors":errors},ensure_ascii=False),flush=True)
    if errors: raise RuntimeError(f"{track['id']} failed signal checks: {errors}")
    return record


def build_review(records, all_tracks):
    import numpy as np
    import soundfile as sf
    lookup={t["id"]:t for t in all_tracks}
    previews=REPORT/"audition"
    previews.mkdir(parents=True,exist_ok=True)
    cards=[]
    rows=[]
    for record in records:
        track=lookup[record["id"]]
        audio=ROOT/record["runtime_path"]
        preview_name=record['id']+('_'+record['sha256'][:12] if record.get('revision',0)>=3 else '')+'.mp3'
        preview=previews/preview_name
        if not preview.exists() or preview.stat().st_mtime<audio.stat().st_mtime:
            command([FFMPEG,"-hide_banner","-nostdin","-y","-i",str(audio),"-c:a","libmp3lame","-b:a","192k",str(preview)])
        seam_markup=""
        if record["loop"]:
            seam_preview=previews/(record['id']+'_'+record['sha256'][:12]+'_seam.wav')
            if not seam_preview.exists() or seam_preview.stat().st_mtime<audio.stat().st_mtime:
                decoded,_=sf.read(audio,dtype="float32",always_2d=True)
                snippet=np.concatenate([decoded[-6*SR:],decoded[:6*SR]],axis=0)
                sf.write(seam_preview,snippet,SR,subtype="PCM_16")
            seam_markup=f'<details><summary>循环接头：尾部6秒→头部6秒（第6秒过接头，无额外有损转码）</summary><audio controls preload="none" src="audition/{seam_preview.name}"></audio></details>'
        m=record["metrics"]
        cards.append(f'<article id="{record["id"]}"><h2>{html.escape(record["title"])}</h2><p>{html.escape(track["scene"])}</p><p class="facts">{m["seconds"]:.2f} 秒 · {"循环" if record["loop"] else "单次提示"} · {m["integrated_lufs"]:.2f} LUFS · {m["true_peak_dbtp"]:.2f} dBTP · {record["bytes"]/1000:.0f} KB</p><audio controls preload="none" src="audition/{preview.name}"></audio>{seam_markup}<p class="links"><a href="../../assets/music/20261024/{record["id"]}.ogg">运行OGG</a> · <a href="tracks/{record["id"]}.json">完整指标与制作记录</a></p></article>')
        rows.append(f'| {record["title"]} | {track["scene"]} | {m["seconds"]:.2f} | {"是" if record["loop"] else "否"} | {m["integrated_lufs"]:.2f} | {m["true_peak_dbtp"]:.2f} | {record["bytes"]:,} |')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>原创配乐试听 · 2026-10-24</title><style>body{margin:0;background:#f3f0e8;color:#242b2c;font:16px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:24px}h1{line-height:1.25}header{padding:12px 0 24px}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr));gap:16px}article{background:#fffdf8;border-radius:12px;padding:20px;box-shadow:0 3px 15px #29312d10}h2{font-size:20px;margin:0 0 8px}audio{width:100%;margin:8px 0}a{color:#355d68}.facts,.links{font-size:14px;color:#536364}summary{cursor:pointer;padding:10px 0}:focus-visible{outline:none;box-shadow:0 0 0 4px #789c9b60}details audio{margin-top:0}</style><main><header><h1>原创配乐试听</h1><p><a href="../sfx-20261024/index.html">攻击、法术与界面音效试听（41 个音效）</a></p><p>28 首本地模型原创纯音乐：五章世界地图、战场、据点、剧情与短提示。运行素材为 44.1kHz 双声道 OGG；本页 MP3 仅为方便浏览器试听。</p><p>已完成音频解码、时长、响度、真峰值、静音与循环采样连续性检查。尚未进行听觉验收；指标不能代替对旋律、音色、是否混入人声纹理和乐句衔接的试听。循环短片段在第 6 秒接回开头，未额外修饰接头。</p><p><a href="generation-report.json">完整生成记录</a> · <a href="tracks.md">曲目指标表</a> · <a href="mapping.md">剧情与资源映射</a></p></header><section>'''+''.join(cards)+'''</section></main><script>document.addEventListener('play',e=>{if(e.target.tagName==='AUDIO')document.querySelectorAll('audio').forEach(a=>{if(a!==e.target)a.pause()})},true)</script></html>'''
    from audio_content_review_metadata import all_reviewed
    state=('本地音频理解模型逐条审查已完成，包含整首、循环接头及最终场景混音；人工听感记录与模型结论分开。' if all_reviewed(records) else '本地音频理解模型逐条审查进行中；已改曲目将重新输入复核。')
    page=page.replace('28 首本地模型原创纯音乐：','28 首原创纯音乐，包含模型生成及新写旋律导轨编排：')
    page=page.replace('已完成音频解码、时长、响度、真峰值、静音与循环采样连续性检查。尚未进行听觉验收；指标不能代替对旋律、音色、是否混入人声纹理和乐句衔接的试听。',state+' 制作方法和导轨／模型比例逐曲保存在记录中。')
    page=page.replace('<a href="generation-report.json">完整生成记录</a>','<a href="../audio-content-review-20261024/README.md">逐条听审与修改依据</a> · <a href="generation-report.json">完整生成记录</a>')
    page=page.replace("document.addEventListener('play'", "document.querySelectorAll('audio').forEach(a=>a.volume=.5);document.addEventListener('play'")
    page=page.replace('循环短片段在第 6 秒接回开头，未额外修饰接头。','播放器默认50%，对应当前游戏配乐倍率。循环短片段在第 6 秒接回开头，未额外修饰接头。')
    (REPORT/"index.html").write_text(page)
    (REPORT/"tracks.md").write_text('# 原创配乐制作指标\n\n本地模型生成与新写旋律导轨编排；原始 FLOAT WAV 保留在工程外层 source/audio-20261024，不放入游戏包。指标为实际运行 OGG 解码测量。逐条本地模型音频审查与修改依据见 [审查表](../audio-content-review-20261024/tracks.md)，不声称人耳验收。\n\n| 曲名 | 场景 | 实际秒数 | 循环 | LUFS | 真峰值 dBTP | 字节 |\n|---|---|---:|---|---:|---:|---:|\n'+'\n'.join(rows)+'\n')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--worker")
    ap.add_argument("--seed",type=int)
    ap.add_argument("--ids",nargs="*")
    ap.add_argument("--master-only",action="store_true")
    ap.add_argument("--report-only",action="store_true")
    args=ap.parse_args()
    for key in ("HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","PYTHONDONTWRITEBYTECODE"):
        os.environ[key]="1"
    if args.worker:
        return worker(args.worker,args.seed)
    SOURCE.mkdir(parents=True,exist_ok=True)
    (SOURCE/".gdignore").touch()
    (REPORT/"logs").mkdir(parents=True,exist_ok=True)
    all_tracks=tracks()
    by_id={t["id"]:t for t in all_tracks}
    selected=[by_id[i] for i in args.ids] if args.ids else all_tracks
    for track in ([] if args.report_only else selected):
        seed=args.seed if args.seed is not None and len(selected)==1 else seed_for(track)
        raw,meta=source_paths(track,seed)
        report=REPORT/"tracks"/(track["id"]+".json")
        if report.exists():
            previous=json.loads(report.read_text())
            output=ROOT/previous["runtime_path"]
            if previous.get('production_method')=='audio_review_refinement':
                if output.exists() and digest(output)==previous['sha256']:
                    print(f"RESUME preserve audio-reviewed refinement {track['id']}",flush=True)
                    continue
                raise RuntimeError('This cue uses refine_music_for_scene.py; rebuild and review its scene-led recipe rather than reverting to the earlier text-only score.')
            if previous.get("revision")==REVISION and previous.get("source",{}).get("seed")==seed and previous.get("status")=="signal_checks_passed" and output.exists() and digest(output)==previous["sha256"]:
                print(f"RESUME skip verified {track['id']}",flush=True)
                continue
        if not raw.exists() or not meta.exists():
            if args.master_only: raise FileNotFoundError(raw)
            print(f"GENERATE {track['id']} seed={seed}",flush=True)
            command([sys.executable,"-B",__file__,"--worker",track["id"],"--seed",str(seed)],REPORT/"logs"/(track["id"]+"_generation.log"))
        master(track,seed)
    records=[]
    for track in all_tracks:
        p=REPORT/"tracks"/(track["id"]+".json")
        if p.exists(): records.append(json.loads(p.read_text()))
    from audio_content_review_metadata import attach_content_reviews,all_reviewed,sync_runtime_review_metadata
    attach_content_reviews(records,ROOT/'actual')
    sync_runtime_review_metadata(records,ROOT/'actual/data/soundtrack.json')
    for record in records:dump(REPORT/'tracks'/(record['id']+'.json'),record)
    dump(REPORT/"generation-report.json",{"schema":1,"production_revision":max([REVISION]+[r['revision'] for r in records]),"model":"Local Stable Audio 3 with original guide composition/arrangement where recorded", "planned_tracks":len(all_tracks),"completed_tracks":len(records),"signal_checks_passed":sum(r["status"]=="signal_checks_passed" for r in records),"auditory_review":all_reviewed(records),"human_listening":False,"tracks":records})
    build_review(records,all_tracks)


if __name__=="__main__":
    main()
