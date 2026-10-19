from pathlib import Path
from PIL import Image
import json, hashlib

V = Path(__file__).resolve().parents[1]; R = V.parent
reg = json.loads((V / 'registration.json').read_text()); base = '../../../' + V.name
for side in ['ally', 'enemy']:
    path = R / f'professions/class-8-{side}/battle/frame_mapping.json'
    data = json.loads((V / f'reference/{side}-mapping-before.json').read_text())
    for record in data['records']:
        k = record['source_frame']; p = V / f'deliverables/{side}/frame-{k:03d}.png'
        old_path = record.get('path', record.get('output_path'))
        record.update(path=f'{base}/deliverables/{side}/frame-{k:03d}.png',
                      previous_source=f'{base}/reference/{side}-{k:03d}.png',
                      kind='existing_pose_outfit_palette_simplification',
                      shared_body_palette=reg['palettes'][side],
                      size=list(Image.open(p).size), alpha_bounds=list(Image.open(p).getbbox()),
                      bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        if 'output_path' in record:
            record['output_path'] = record['path']
        if k in [0, 1, 2, 3, 4, 5, 7, 16]:
            record['protected_blade'] = next(x['protected_blade_segment'] for x in reg['records']
                                             if x['side'] == side and x['source_frame'] == k)
        if k == 6:
            record['preserved_slash_layer'] = f'{base}/reference/{side}-slash-006.png'
        record['previous_art_metadata_scope'] = 'Older generation/registration fields document the unchanged prior pose geometry; current color processing is recorded in the revision registration.json.'
    data.update(frame_mapping={str(x['source_frame']): x['path'] for x in data['records']},
                revision=V.name, modified_by='Codex', status='review_candidate', runtime_integrated=False,
                output_atlas=f'{base}/deliverables/{side}/battle-atlas.png',
                output_atlas_frame_order=[0, 1, 2, 3, 4, 5, 6, 7, 16],
                qa_report=f'{base}/verification.json',
                art_review='Pending user visual acceptance. Exact alpha/positions, sword protection and original slash/lightning retained.',
                art_mode='ImageGen color reference, fixed body palettes, protected existing sword and slash pixels; no scaling or translation except proven source aliases.',
                review_note='佣兵战斗场景减色：人物主体每方共用14色，服装合并明暗；盟军保留暖紫衣装、棕色皮具及少量浅金边，敌军统一偏蓝紫。保留现有比例、姿势、腾空高度与脚底位置，刀刃保护，原刀光和雷电效果保持。仅更新对照，未接入测试包。',
                batches=[{'id': '双方简色待机', 'review': f'{base}/reviews/factions-dark.png'},
                         {'id': '本方全姿势修改前后', 'review': f'{base}/reviews/{side}-previous-and-new-dark.png'}])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

path = R / 'tools/export_gallery.py'
source = path.read_text().replace("in ['spearman-enemy-blue-violet-v2-20261019'",
    "in ['mercenary-battle-simple-v1-20261019','spearman-enemy-blue-violet-v2-20261019'")
path.write_text(source)
path = R / 'index.html'; source = path.read_text()
source = source.replace('data-default-action="professions-class-6-enemy-battle--original_class_6_enemy_normal"',
                        'data-default-action="professions-class-8-ally-battle--original_class_8_normal"')
source = source.replace('敌军枪兵 · 蓝紫配色稿', '佣兵 · 双方简色／敌军蓝紫稿')
links = [('?action=professions-class-8-ally-battle--original_class_8_normal', '盟军佣兵 · 普通攻击'),
         ('?action=professions-class-8-enemy-battle--original_class_8_enemy_normal', '敌军佣兵 · 普通攻击'),
         ('?action=professions-class-8-ally-battle--class_8_ally_levin', '盟军佣兵 · 雷剑'),
         ('?action=professions-class-8-enemy-battle--class_8_enemy_levin', '敌军佣兵 · 雷剑'),
         (V.name + '/overview.mp4', '本轮佣兵动作总览'),
         (V.name + '/reviews/factions-dark.png', '双方简色形象'),
         (V.name + '/reviews/ally-previous-and-new-dark.png', '盟军全姿势修改前后'),
         (V.name + '/reviews/enemy-previous-and-new-dark.png', '敌军全姿势修改前后'),
         (V.name + '/verification.json', '本轮检查记录')]
nav = '<nav class="links" aria-label="本轮佣兵战斗场景" style="margin-bottom:12px">'
nav += ''.join(f'<a href="{url}">{label}</a>' for url, label in links) + '</nav>\n'
nav += '<p class="action-note" style="margin:0 0 22px">本轮简化双方佣兵战斗场景的服装配色：人物主体每方统一14色，衣甲保留少量明暗。盟军为暖紫衣装、棕色皮具与克制的浅金边；敌军采用蓝紫衣甲，保持自然肤色与发色。现有比例、所有姿势、腾空高度、脚底与动作节奏保持；刀刃单独保护，原作刀光和雷电效果保留。只更新对照页，地图形象与测试包未修改。</p>\n'
start = source.index('<nav class="links" aria-label="本轮敌军蓝紫配色"')
source = source[:start] + nav + source[start:]
source = source.replace('?v=spearman-enemy-blue-violet-v2-20261019', '?v=' + V.name)
path.write_text(source)
print('Updated both mercenary battle preview mappings and gallery entry.')
