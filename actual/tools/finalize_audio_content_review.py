#!/usr/bin/env python3
"""Publish an auditable index only when all final waveforms have receipts."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'actual'
REPORT=PROJECT/'reports/audio-content-review-20261024'
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def esc(s):return str(s).replace('|','／').replace('\n',' ')

SFX_NOTES={
 '01':'保留逐次电音脉冲，避免把一次请求做成整段雷暴；按时间轴重复检查。',
 '02':'原声引导的新变体保留更清楚的电子起音；兼容备用，仅检查孤立反馈。',
 '03':'压紧单次命中手势，保留清楚起音；与生命刻度分开，不新增连击。',
 '04':'新合成候选更刺耳、拖尾更长，已舍弃，保留当前版本。',
 '05':'原声引导变体保留调制与清楚衰减；未检出当前触发，不增加用途。',
 '06':'原版替换听成低沉机械冲击，改为有音高调制的快速电子脉冲。',
 '07':'保留参考电子手势与起音，减少无关低频；仅作兼容备用。',
 '10':'确认提示现版清楚；新合成未形成稳定优势，保留。',
 '11':'对照结论不稳定，未证明候选更好；保留现版兼容提示。',
 '12':'按原音高与短包络重合成约113ms提示；同时检查菜单连移及HP逐格扣减。',
 '13':'重合成约48ms返回提示，去掉不必要的厚重拖尾，保持与确认音区分。',
 '15':'保留短促电子手势与原生时长预算；仅作兼容备用。',
 '16':'以参考音高包络重合成破空反馈，去掉低闷机械感。',
 '17':'候选未证明比现版更清楚；保留，不凭编号推断游戏用途。',
 '21':'修复低闷、起音不清及主体过弱；风刃与治疗共用，保留有限持续与停止请求。',
 '22':'用原声引导保留调制速度与清楚瞬态；兼容备用不新增调用。',
 '23':'修复能量主体偏弱，保留传送／显形调制；按30停止的原生窗口审查。',
 '25':'重合成约48ms翻页短音，避免每次文字推进出现长尾叠响。',
 '26':'将低沉钝击改为有起音和调制的电子能量；原生30停止仍生效。',
 '27':'按参考重合成法术短冲击；保留死亡法术语义，不作为角色死亡提示。',
 '31':'保留清楚电子起音及衰减，减少无关低频；兼容备用。',
 '32':'保留原声调制与音高走向；兼容备用，不猜测触发场景。',
 '33':'保留紧凑电子反馈与原生时长预算；仅作兼容备用。',
 '36':'参考音高／包络重合成，避免生成模型带入钝击或机械尾音。',
 '37':'原声引导变体保留更明确的电子手势；仅作兼容备用。',
 '40':'保留现版自然电子扫频，只修整峰体比例；活动RMS约−27.76→−24.90dBFS。',
 '41':'按参考音高／包络重合成，保留短音识别度；兼容备用。',
 '42':'原声引导变体保留清楚起音和电子调制；仅作兼容备用。',
 '43':'保持闪避／零伤害的短反馈，区别于命中；不凭音效制造伤害。',
 '44':'原声引导保留短促电子手势，去掉无关尾部；仅作兼容备用。',
 '45':'保留参考调制与清楚瞬态；仅作兼容备用。',
 '46':'分析参考后重合成电子反馈，避免钝击和无关低频；兼容备用。',
 '47':'恢复清楚高音调制与主体电平；按约96帧后30停止审查，尾音不无限循环。',
 '50':'原声引导变体保留清楚电子手势与短衰减；兼容备用。',
 '51':'现版短反馈没有稳定劣势，候选无明确提升，保留。',
 '52':'新合成丢失音高、变成宽频嘶声，已舍弃，保留当前调制音。',
 '53':'改为轻而迅速的电子前奏；按约50ms后被命中／闪避替换审查，不拉高整段。',
 '54':'按参考音高／包络重合成，去掉无关低频；仅作兼容备用。',
 '55':'现版单次提示清楚，没有证据支持替换，保留。',
 '60':'候选未形成稳定提升，保留当前短反馈；仅作兼容备用。',
 '61':'候选未形成稳定提升，保留当前短反馈；仅作兼容备用。'}

MUSIC_NOTES={
 'rm_prologue':'改写为庆典行进动机，保留不安底色；加强脉冲与低音接续，修正第一版循环音量落差。',
 'rm_battle_snow':'改写护送行进动机，明确直拍、短呼应与持续低音，去掉松散爵士／木管质感。',
 'rm_battle_tide':'改写为海上护航直拍进行，去掉轻松摇摆感；保留救援前进感。',
 'rm_battle_revenge':'改写克制而紧张的对抗动机；接头意见不一致，另做两版对照，未证明进一步改末音更好，保留V2。',
 'rm_battle_refuge':'改写短促呼应与持续推进，服务守井／撤离，去掉松弛伴奏。',
 'rm_battle_two_fronts':'改写为双声部问答与直拍低音，表达两队配合，减少声部堆积。',
 'rm_battle_sun_tower':'改写严肃的旧同袍对抗动机；接头意见不一致，另做两版对照，未证明进一步改末音更好，保留V2。',
 'rm_battle_circuit':'改写稀疏的不安对位与清楚脉冲，保留古设施的谨慎感，避免舞曲化。',
 'rm_battle_ascent':'改写相互呼应的救援进行，保持合军与前进的节奏感。',
 'rm_battle_final':'改写四声部终战动机，保持全阶段连续；给命中和支援提示保留音量空间。',
 'rm_jingle_victory':'由缺少明确句尾的氛围段改为约3.08秒上行完成短句；结算后恢复背景曲。',
 'rm_jingle_growth':'改为约2.28秒上行琶音与收束，明确成长确认，缩短占用时间。',
 'rm_jingle_award':'改为约2.58秒温和交接短句与主音收束，匹配托付／招募确认。',
 'rm_jingle_wounded':'改为约2.78秒克制下行短句，传达关切；不用死亡葬礼式长铺底。'}

def main():
    decisions=read(REPORT/'working-decisions.json')
    scenes=read(PROJECT/'reports/audio-scene-review-20261024/review.json')
    scene_by={r['id']:r for r in scenes['resources']}
    receipts=[(p,read(p)) for p in (REPORT/'omni-receipts').glob('*.json')]
    rows=[];tables={'music':[],'sfx':[]}
    for category,directory in [('music','soundtrack'),('sfx','sfx')]:
        plans={r['id']:r for r in read(PROJECT/f'reports/{directory}-20261024/plan.json')['tracks']}
        records=read(PROJECT/f'reports/{directory}-20261024/generation-report.json')['tracks']
        for track in records:
            ident=track['id'];digest=sha(ROOT/track['runtime_path'])
            assert digest==track['sha256'],ident+' metadata hash'
            def matching_body(item):
                p,d=item
                return (d['id']==ident and digest in d['source_sha256'] and
                        (d['kind']=='music_entire_loop_and_scene' if category=='music' else
                         d['kind'].startswith('sfx') and d['kind']!='final_scene_mix'))
            bodies=[item for item in receipts if matching_body(item)]
            assert bodies,ident+' missing final body review'
            body_path,body=max(bodies,key=lambda item:item[0].stat().st_mtime)
            scene=scene_by[ident]
            fixture=ROOT/scene['scene_fixture_path'];fixture_sha=sha(fixture)
            matches=[(p,d) for p,d in receipts if d['id']==ident and d['kind']=='final_scene_mix'
                     and d['asset_sha256']==digest and d['fixture_sha256']==fixture_sha
                     and d['source_sha256']==[fixture_sha]]
            assert matches,ident+' missing final scene review'
            scene_path,scene_receipt=max(matches,key=lambda item:item[0].stat().st_mtime)
            for receipt in [body,scene_receipt]:
                for frozen,expected in zip(receipt['archived_input_paths'],receipt['source_sha256']):
                    assert sha(ROOT/frozen)==expected,ident+' frozen input mismatch'
            audio,rate=sf.read(ROOT/track['runtime_path'],dtype='float32',always_2d=True)
            assert rate==44100 and audio.shape[1]==2 and np.isfinite(audio).all()
            assert float(np.abs(audio).max())<1 and not track['errors']
            if category=='music':
                assert body['audio_input_samples'][0]==len(__import__('review_audio_omni').load_slice(body['audios'][0]))
                changed=ident in decisions['music_recompose']
                method=('新写旋律编排＋本地模型音色' if changed else '保留现版')
                note=MUSIC_NOTES.get(ident,'整首、接头和最终场景已输入复核；当前音色与“'+plans[ident]['mood']+'”相容，未发现足以支持重做的稳定证据。')
            else:
                req=track['request'];changed=req not in decisions['sfx_retain']
                method=('原声引导生成' if req in decisions['sfx_reference_guided'] else
                        '音高／包络重合成' if req in decisions['sfx_synthesized'] else
                        '保留音色、修整电平' if req in decisions['sfx_remastered'] else '保留现版')
                note=SFX_NOTES[req]
            row={'id':ident,'title':track['title'],'type':category,'sha256':digest,
                 'runtime_path':track['runtime_path'],'changed_this_turn':changed,
                 'method':method,'scene':plans[ident].get('scene',plans[ident].get('role')),
                 'model_review_completed':True,'review_type':'local_waveform_conditioned_model',
                 'model':body['model'],'receipt':rel(body_path),'scene_receipt':rel(scene_path),
                 'scene_fixture_sha256':fixture_sha,'scene_fixture_path':scene['scene_fixture_path'],
                 'conclusion':note,'human_listening':False,
                 'model_response':body['response'],'scene_model_response':scene_receipt['response'],
                 'duration_seconds':len(audio)/rate,'sample_peak_dbfs':20*math.log10(max(float(np.abs(audio).max()),1e-12))}
            rows.append(row)
            body_link='omni-receipts/'+body_path.name;scene_link='omni-receipts/'+scene_path.name
            tables[category].append(f'| `{ident}` {esc(track["title"])} | {esc(row["scene"])} | {method} | {len(audio)/rate:.3f} | {esc(note)} | [音频输入记录]({body_link}) · [最终混音]({scene_link}) |')
    assert len(rows)==69 and len(tables['music'])==28 and len(tables['sfx'])==41
    changed={k:sum(r['changed_this_turn'] for r in rows if r['type']==k) for k in ['music','sfx']}
    assert changed=={'music':14,'sfx':32}
    result={'schema':1,'date':'2026-10-24','model_review_completed':True,'human_listening':False,
            'scope':'All 28 complete soundtrack cues, 24 loop joins, 41 source/replacement SFX comparisons and all 69 final game-gain fixtures; not human listening or iPhone testing.',
            'resources':rows,'changed':changed,'iphone_accessed':False,'screenshots':0}
    dump(REPORT/'final-review.json',result)
    intro='# 69项本地模型音频审查与修改依据\n\n28首配乐、41个音效均有实际波形输入记录；24个循环接头和69个最终场景混音逐项检查。修改14首配乐、32个音效，其他版本保留。本表是本地模型内容审查与代码／信号证据的综合判断，不声称人耳验收。具体模型偏差见 [范围与限制](README.md)。\n\n'
    header='| 资源／名称 | 场景／用途 | 本轮决定 | 秒数 | 修改或保留依据 | 可复查证据 |\n|---|---|---|---:|---|---|\n'
    (REPORT/'tracks.md').write_text(intro+'## 配乐（28首）\n\n'+header+'\n'.join(tables['music'])+'\n\n## 音效（41个）\n\n'+header+'\n'.join(tables['sfx'])+'\n')
    decisions.update(music_retain=[r['id'] for r in rows if r['type']=='music' and not r['changed_this_turn']],
        already_published_sfx=[r['id'].split('_')[-1] for r in rows if r['type']=='sfx' and r['changed_this_turn']],
        notes='Final 69 exact runtime hashes have body and scene receipts. Fourteen music and thirty-two SFX revised. Two V3 cadence candidates not published: comparison found no clear benefit. No iPhone, save or screenshot access.')
    dump(REPORT/'working-decisions.json',decisions)
    print(json.dumps({'resources':len(rows),'changed':changed,'missing_receipts':0},ensure_ascii=False))

if __name__=='__main__':main()
