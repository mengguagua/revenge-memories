#!/usr/bin/env python3
"""Recover all source music requests and campaign routing without changing audio.json."""
import argparse,array,hashlib,json,math,subprocess,tempfile,wave
from pathlib import Path
from extract_audio import ROOT,RATE,Renderer,build_nsf,read_bank,driver_loop,TRACE_SIZE,FRAME_US
from extract_graphics import blocks

def main(source,gme,encoder):
    manifest={'source':'Original unmodified FE2 bank014 music driver','music_by_request':{},'sfx_by_request':{},'routing':{},'ignored_requests':{},'silent_sfx_requests':[],'control_requests':{'00':'stop_all','30':'stop_sfx'},'failures':[]}
    current=json.loads((ROOT/'data/audio.json').read_text());existing={int(v['source_request'],16):v for group in ['music','sfx'] for v in current[group].values()}
    b6=blocks(source/'src/bank006.asm');b7=blocks(source/'src/bank007.asm');b12=blocks(source/'src/bank012.asm')
    manifest['routing']={'world_by_chapter':b7['L078A58']['db'][:5],'player_by_route':b6['L06BA5F']['db'][:2],'player_last_enemy_by_route':b6['L06BA61']['db'][:2],'enemy_by_route':b6['L06BA63']['db'][:2],'final_battle_by_phase':b6['L06BA65']['db'][:2],'hub_music_requests':b12['L0CB203']['db'][:31],'hub_music_index_by_map':b12['L0CB244']['db'][:120],'hub_music_lookup_limit_exclusive':111,'hub_music_default_index':4,'hub_music_rule':'L0CB222 checks map_id<111: lookup[map_id-1]. IDs111 and above always use index4(request95); the physical table has120 bytes, with10 unused default4 entries. Following bytes are unrelated records.','route_indices':{'alm':0,'celica':1},'source':'L078A43-L078A58(world); L06BA18-L06BA65(battle); L0CB222-L0CB244(hub)','last_enemy_rule':'L06BA91: fewer than two living enemies sets$7445; this selectsA3/A7 only on player phase.'}
    out=ROOT/'assets/original/audio';out.mkdir(exist_ok=True);path=ROOT/'data/full_audio.json';bank=read_bank(source/'fe2.nes')
    manifest['driver_sha256']=hashlib.sha256(bank).hexdigest()
    if path.exists():
        previous=json.loads(path.read_text());manifest['music_by_request']=previous.get('music_by_request',{});manifest['sfx_by_request']=previous.get('sfx_by_request',{})
    with tempfile.TemporaryDirectory(prefix='fe2-full-audio-') as tmpdir:
        tmp=Path(tmpdir);nsf=tmp/'fe2.nsf';nsf.write_bytes(build_nsf(bank));renderer=Renderer(gme,nsf)
        for request in [group*16+slot for group in range(7,12) for slot in range(8)]:
            key=f'{request:02X}'
            song_index=((request>>4)-7)*8+(request&7);song_pointer=bank[0x12df+song_index*2]+256*bank[0x12df+song_index*2+1]
            if not song_pointer:
                manifest['ignored_requests'][key]={'behavior':'preserve_current_music','source':'L0E92DF null pointer; L0E8146-L0E815D jumps to existing playback without resetting channels.'};continue
            temporary=request in [0x82,0x84,0xb6]
            if key in manifest['music_by_request'] and (ROOT/manifest['music_by_request'][key]['path'].removeprefix('res://')).exists() and manifest['music_by_request'][key]['duration']<179 and (not temporary or manifest['music_by_request'][key].get('resume_music',False)):continue
            if request in existing:manifest['music_by_request'][key]=existing[request];continue
            try:
                trace=tmp/f'{key}.trace';pcm=renderer.render(request,8 if temporary else 360 if request in [0x96,0xb7] else 180,trace);loop=None if temporary else driver_loop(trace);return_frame=None
                if temporary:
                    tracebytes=trace.read_bytes();desired=((request>>4)-7)*8+(request&7)
                    return_frame=next((i for i in range(len(tracebytes)//TRACE_SIZE) if tracebytes[i*TRACE_SIZE+16+0x44]!=desired),None)
                    if return_frame is None:raise RuntimeError('temporary tune did not return to saved BGM')
                    pcm=pcm[:round(return_frame*FRAME_US/1e6*RATE)*2]
                if loop:pcm=pcm[:round(loop['end_seconds']*RATE)*2]
                else:
                    last=next((i for i in range(len(pcm)-1,-1,-1) if abs(pcm[i])>12),0);pcm=pcm[:min(len(pcm),((last//2)+round(RATE*.12))*2)]
                peak=max(map(abs,pcm),default=0)/32768
                if not peak:raise RuntimeError('source request is silent')
                wav=tmp/f'{key}.wav'
                with wave.open(str(wav),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(pcm.tobytes())
                ogg=out/f'music_{key.lower()}.ogg';command=[str(encoder),str(wav),str(ogg)]
                if loop:command.extend([str(round(loop['start_seconds']*RATE)),str(len(pcm)//2)])
                subprocess.run(command,check=True,capture_output=True)
                manifest['music_by_request'][key]={'path':'res://'+str(ogg.relative_to(ROOT)),'source_request':f'0x{request:02X}','source_evidence':'Original packed bank014 sound request; scene routing is from the source tables in this manifest.','duration':round(len(pcm)/(RATE*2),6),'peak':round(peak,6),'peak_dbfs':round(20*math.log10(peak),3),'bytes':ogg.stat().st_size,'loop':bool(loop),'loop_offset':loop['start_seconds'] if loop else 0.0,'loop_analysis':loop,'default_enabled':True,'mapping_status':'source_request_verified'}
                if temporary:
                    manifest['music_by_request'][key].update({'resume_music':True,'source_return_frame':return_frame,'source_evidence':'L0E8128 preserves previous track$0646 for temporary slots10/12/38; opcodeBD(L0E8544) sets$0647 and restores saved BGM. PCM stops at first trace transition of$0644, before the unrelated previous track.'})
                print(key,manifest['music_by_request'][key]['duration'],manifest['music_by_request'][key]['loop'],flush=True)
            except Exception as exc:manifest['failures'].append({'request':key,'error':str(exc)})
            path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        for request in [group*16+slot for group in range(7) for slot in range(8)]:
            key=f'{request:02X}'
            if key in manifest['control_requests']:continue
            if request==0x56:manifest['control_requests'][key]='fade_music';continue
            sfx_index=(request>>4)*8+(request&7);sfx_pointer=bank[0x828+sfx_index*2]+256*bank[0x828+sfx_index*2+1]
            if not sfx_pointer:manifest['control_requests'][key]='stop_sfx';continue
            if key in manifest['sfx_by_request']:continue
            if request in existing:manifest['sfx_by_request'][key]=existing[request];continue
            try:
                pcm=renderer.render(request,8,tmp/f'sfx_{key}.trace');peak=max(map(abs,pcm),default=0)/32768
                if not peak:manifest['silent_sfx_requests'].append(key);continue
                last=next((i for i in range(len(pcm)-1,-1,-1) if abs(pcm[i])>12),0);sustained=last>int(len(pcm)*.97)
                pcm=pcm[:min(len(pcm),((last//2)+round(RATE*.12))*2)];wav=tmp/f'sfx_{key}.wav'
                with wave.open(str(wav),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(pcm.tobytes())
                ogg=out/f'sfx_{key.lower()}.ogg';subprocess.run([str(encoder),str(wav),str(ogg)],check=True,capture_output=True)
                manifest['sfx_by_request'][key]={'path':'res://'+str(ogg.relative_to(ROOT)),'source_request':f'0x{request:02X}','source_evidence':'Original packed sound request, used only when selected by source animation/event opcode.','duration':round(len(pcm)/(RATE*2),6),'peak':round(peak,6),'bytes':ogg.stat().st_size,'loop':False,'loop_offset':0,'manual_stop':sustained,'default_enabled':True,'mapping_status':'source_request_verified'}
            except Exception as exc:manifest['failures'].append({'request':key,'error':str(exc)})
    manifest['music_by_request']['73'].update({'default_enabled':True,'mapping_status':'source_ending_verified','source_evidence':'L04B0F9 initializes per-character ending epilogues and requests73; L04B149 uses display_order; L04B25E selects conditional character ending text. This is the original ending track, not an attract demo.'})
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'tracks':len(manifest['music_by_request']),'sfx':len(manifest['sfx_by_request']),'failures':manifest['failures']},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('/private/tmp/fe2-analysis-20261012'));p.add_argument('--gme',type=Path,default=Path('/private/tmp/fe2-audio-libgme/libgme.dylib'));p.add_argument('--encoder',type=Path,default=Path('/private/tmp/fe2-audio-work/encode_vorbis'));a=p.parse_args();main(a.source,a.gme,a.encoder)
