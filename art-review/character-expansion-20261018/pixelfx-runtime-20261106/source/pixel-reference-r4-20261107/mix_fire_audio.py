"""Mix local Stable Audio model-based takes into one uninterrupted Fireball cue."""
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import wave

import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
PREVIOUS=HERE.parent/'magic-sound-r3-20261107/audio'
OUT=BASE/HERE.name
RATE=44100


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def level(a):
    return 20*math.log10(max(1e-10,float(np.sqrt(np.mean(a*a)))))


def samples(stage):
    path=PREVIOUS/'masters'/f'fire-{stage}.wav'
    raw=PREVIOUS/'sources'/f'fire-{stage}-model.wav'
    receipt=PREVIOUS/'sources'/f'fire-{stage}.json'
    assert sha(raw)==json.loads(receipt.read_text())['sha256']
    with wave.open(str(path),'rb') as f:
        assert (f.getframerate(),f.getnchannels(),f.getsampwidth())==(RATE,1,2)
        a=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float64)/32768
    return a,{'take':raw.name,'sha256':sha(raw),'master_sha256':sha(path)}


def norm(a,target):
    return (a-a.mean())*10**((target-level(a-a.mean()))/20)


def grains(a,n):
    """Retiming with overlapping short windows keeps the timbre of the sample."""
    if n<=0:
        return np.zeros(0)
    w=min(3072,len(a),max(448,n//2))
    hop=w//4
    win=np.hanning(w)**.8
    dst=np.zeros(n+w); denom=np.zeros(n+w)
    for i,j in enumerate(range(-w//2,n,hop)):
        src=round((len(a)-w)*max(0,min(1,(j+w//2)/n)))
        off=max(0,-j);start=max(0,j);stop=start+w-off
        dst[start:stop]+=a[src+off:src+w]*win[off:]
        denom[start:stop]+=win[off:]
    return dst[:n]/np.maximum(.0001,denom[:n])


def ramp(n):
    return np.sin(np.linspace(0,np.pi/2,n))**2


def emit(tasks):
    raw_charge,s1=samples('charge')
    raw_flight,s2=samples('release')
    raw_impact,s3=samples('resolve')
    pool={}
    stats={}
    for task in tasks:
        key=task['cue']; c=round(task['charge']*RATE); f=round(task['flight']*RATE)
        wide=task['cinema']
        if key in pool:
            continue
        assert .12<=c/RATE<3 and .055<=f/RATE<2,(key,c/RATE,f/RATE)
        flight=c; contact=c+f
        blend1=round(RATE*.038)
        blend2=round(RATE*.068)
        tail=round(RATE*(.80 if wide else .68))
        a=grains(raw_charge[round(RATE*.028):round(RATE*.315)],c+blend1)
        a=norm(a,-25 if wide else -27)*np.linspace(.46,1.33,len(a))**1.22
        # Cross into the rushing model texture before the first long silence.
        a[:round(RATE*.051)]*=ramp(round(RATE*.051))
        a[-blend1:]*=1-ramp(blend1)
        n=f+blend2
        f0=raw_flight[round(RATE*.012):round(RATE*.216)]
        b=norm(grains(f0,n),-21.8 if wide else -22.8)
        b*=np.linspace(.7,1.42,len(b))
        up=min(blend1,round(f*.34))
        b[:up]*=ramp(up)
        b[-blend2:]*=(1-ramp(blend2))*.68
        raw_peak=int(np.flatnonzero(np.abs(raw_impact)>10**(-45/20))[0])
        raw_hit=raw_impact[max(0,raw_peak-28):]
        # Preserve the recorded attack transient and stretch only the ember tail.
        hit_end=round(.129*RATE)
        overlap=round(.041*RATE)
        transient=raw_hit[:hit_end+overlap].copy()
        transient[:112]*=ramp(112)
        transient[-overlap:]*=1-ramp(overlap)
        decay=grains(raw_hit[hit_end:],tail-hit_end)
        decay*=np.linspace(.96,.24,len(decay))**1.30
        decay[:overlap]*=ramp(overlap)
        z=np.zeros(tail)
        z[:len(transient)]=transient
        z[hit_end:]+=decay
        z=norm(z,-18.3 if wide else -19.6)
        z[-round(.070*RATE):]*=1-ramp(round(.070*RATE))
        mix=np.zeros(contact+tail)
        mix[:len(a)]+=a
        mix[flight:flight+len(b)]+=b
        mix[contact:]+=z
        mix=.52*np.tanh(mix/.52)
        assert np.all(np.isfinite(mix))
        # Use actual sample offsets in the audit; check continuity at both joins.
        seams=[]
        for x in [flight,contact]:
            m=round(.016*RATE)
            left,right=level(mix[x-m:x]),level(mix[x:x+m])
            assert min(left,right)>-44,(key,left,right)
            seams.append([round(left,2),round(right,2)])
        pcm=np.round(mix*32767).astype('<i2')
        out=io.BytesIO()
        with wave.open(out,'wb') as w:
            w.setparams((1,2,RATE,len(pcm),'NONE','not compressed'))
            w.writeframes(pcm.tobytes())
        buf=out.getvalue()
        source_dir=HERE/'audio'
        source_dir.mkdir(exist_ok=True)
        (source_dir/(key+'.wav')).write_bytes(buf)
        pool[key]={'duration':round(len(mix)/RATE,6),'wav':base64.b64encode(buf).decode('ascii')}
        stats[key]={'sample_rate':RATE,'samples':len(mix),'release_sample':flight,'impact_sample':contact,
                    'release_seconds':round(flight/RATE,6),'impact_seconds':round(contact/RATE,6),
                    'peak_dbfs':round(20*math.log10(float(np.max(np.abs(mix)))),2),
                    'join_rms_dbfs_before_after':seams,'sha256':hashlib.sha256(buf).hexdigest()}
    (OUT/'r4-audio-bank.js').write_text('Object.assign(window.PIXELFX_SOUND_BANK,'+json.dumps(pool,separators=(',',':'))+');\n')
    (OUT/'qa/r4-fire-audio.json').write_text(json.dumps({
       'model':'Local Stable Audio 3 sm-sfx / same-s (MLX)',
       'source':'Re-edited locally generated Stable Audio 3 takes from R3; no remote synthesis',
       'waveform':'one mono PCM buffer per cadence; overlapping charge / flight / impact',
       'source_takes':[s1,s2,s3],'case_count':len(tasks),'unique_cues':len(pool),
       'tracks':stats,'cases':tasks},indent=2)+'\n')
    print(f'Mixed {len(tasks)} Fireball cases using {len(pool)} time-aligned buffers')


if __name__=='__main__':
    emit(json.loads(Path(sys.argv[1]).read_text()))
