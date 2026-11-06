#!/usr/bin/env python3
"""One owned two-second recruitment phrase; offline local retimbre, no source music."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source/recruit-npcs-20261025/audio'
OUT=ROOT/'actual/assets/music/20261025/rm_jingle_recruit.ogg'
MODEL=Path('/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx')
SR=44100
SEED=2026102503
MELODY=[(69,0,.16),(74,.16,.16),(78,.32,.16),(76,.48,.16),(81,.64,.20),(78,.84,.20),(86,1.04,.78)]
PROMPT=('TrackType: Music, VocalType: Instrumental. An original two-second warm recruitment-success fanfare for an early-console fantasy tactics game. '
        'Two clear soft pulse-wave voices, rounded triangle bass, dry sparse four-voice chiptune. '
        'Keep the supplied newly composed D-major melody, concise ascending call and resolved final tonic. '
        'Friendly relief and a new companion joining, not combat or a victory march. A clean natural release after the cadence. '
        'No acoustic instruments, orchestral pad, vocals, speech, choir or long introduction.')
NEGATIVE='vocals, speech, lyrics, choir, orchestral pad, acoustic drums, piano, harsh distortion, long intro, fade-in intro'

def write_json(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def main():
    SOURCE.mkdir(parents=True,exist_ok=True);(SOURCE.parent/'.gdignore').touch();OUT.parent.mkdir(parents=True,exist_ok=True)
    guide=SOURCE/'recruit-owned-guide.wav';raw=SOURCE/'recruit-local-model-float.wav'
    if OUT.exists():raise FileExistsError(OUT)
    a=np.zeros((round(4.2*SR),2),np.float32)
    def note(midi,start,length,gain,pulse=True,pan=0):
        x=np.arange(round(length*SR))/SR;p=2*np.pi*440*2**((midi-69)/12)*x
        wave=np.sin(p)+.23*np.sin(3*p)+.06*np.sin(5*p) if pulse else np.sin(p)-np.sin(3*p)/9+np.sin(5*p)/25
        env=np.minimum(x/.003,1)*np.minimum((length-x)/.07,1)*np.exp(-x/max(length*2,.3))
        v=wave*env*gain;at=round(start*SR);a[at:at+len(v)]+=v[:,None]*np.array([1-pan,1+pan])
    for pitch,start,length in MELODY:note(pitch,start,length,.17,True,-.05)
    for pitch,gain in [(50,.105),(62,.04),(66,.045),(69,.04)]:note(pitch,0,1.88,gain,False,.04)
    sf.write(guide,a,SR,subtype='FLOAT')
    for key in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE']:os.environ[key]='1'
    sys.path.insert(0,str(MODEL/'scripts'));import sa3_mlx
    sa3_mlx.save_wav=lambda path,audio,sample_rate=SR:sf.write(path,audio.T,sample_rate,subtype='FLOAT')
    if not raw.exists():
        sys.argv=['sa3_mlx.py','--dit','sm-music','--decoder','same-s','--seconds','4.2','--dit-dtype','fp32','--steps','8','--cfg','2.0','--seed',str(SEED),'--prompt',PROMPT,'--negative-prompt',NEGATIVE,'--out',str(raw),'--init-audio',str(guide),'--init-noise-level','0.25']
        sa3_mlx.main()
    model,rate=sf.read(raw,always_2d=True);assert rate==SR
    model=model[:2*SR];owned=a[:2*SR]
    model*=np.sqrt(np.mean(owned**2))/max(1e-8,np.sqrt(np.mean(model**2)))
    mixed=.72*owned+.28*model
    mixed*=.7/max(1e-8,float(np.abs(mixed).max()))
    mix=SOURCE/'recruit-mix.wav';sf.write(mix,mixed,SR,subtype='FLOAT')
    mastered=SOURCE/'recruit-master-2s.wav'
    subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-y','-i',str(mix),'-af','loudnorm=I=-18:TP=-2:LRA=7,atrim=duration=2,afade=t=in:d=0.003,afade=t=out:st=1.90:d=0.10','-ar',str(SR),'-ac','2',str(mastered)],check=True)
    mastered_audio,mastered_rate=sf.read(mastered,always_2d=True)
    sf.write(OUT,mastered_audio,mastered_rate,format='OGG',subtype='VORBIS')
    probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_format','-show_streams','-of','json',str(OUT)]))
    write_json(SOURCE/'generation.json',{'id':'rm_jingle_recruit','method':'new owned melody plus offline guide-conditioned local model texture','guide_fraction':.72,'model_fraction':.28,'model':'Stable Audio 3 sm-music/same-s','seed':SEED,'steps':8,'prompt':PROMPT,'negative_prompt':NEGATIVE,'melody_midi_start_duration':MELODY,'duration':2.0,'reference_music_used':False,'probe':probe,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()})
    print('RECRUIT_CUE_READY',OUT,probe['format']['duration'])
if __name__=='__main__':main()
