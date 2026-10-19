from pathlib import Path
from PIL import Image
import json, hashlib, copy, shutil

V = Path(__file__).resolve().parents[1]; R = V.parent
reg = json.loads((V / 'registration.json').read_text())
for side in ['ally', 'enemy']:
    folder = R / f'professions/class-6-{side}/battle'
    path = folder / 'frame_mapping.json'
    data = json.loads((V / f'reference/{side}-mapping-before.json').read_text())
    base = '../../../' + V.name
    keys = data['canonical_frames']
    shutil.copyfile(folder / data['frame_mapping']['23'], V / f'reference/{side}-23.png')
    records = []
    for k in keys:
        record = copy.deepcopy(next(x for x in reg['records']
                                   if x['side'] == side and x['source_frame'] == k))
        png = V / f'deliverables/{side}/frame-{k:03d}.png'
        im = Image.open(png).convert('RGBA')
        record.update(path=f'{base}/deliverables/{side}/frame-{k:03d}.png',
                      previous_source=f'{base}/reference/{side}-{k}.png',
                      size=list(im.size), visible_bounds=list(im.getbbox()),
                      bytes=png.stat().st_size, sha256=hashlib.sha256(png.read_bytes()).hexdigest())
        records.append(record)
    record = copy.deepcopy(next(x for x in records
                                if x['source_frame'] == (12 if side == 'ally' else 19)))
    record.update(source_frame=23, path=f'{base}/deliverables/{side}/frame-023.png',
                  previous_source=f'{base}/reference/{side}-23.png')
    records.append(record)
    data.update(frame_mapping={str(x['source_frame']): x['path'] for x in records},
                records=records, revision=V.name, modified_by='Codex', status='review_candidate',
                output_atlas=f'{base}/deliverables/{side}/battle-atlas.png',
                qa_report=f'{base}/verification.json', output_atlas_frame_order=sorted(keys),
                art_mode='ImageGen simplification reference; final pose pixels retained with 8% horizontal resize, fixed palette remapping and registered whole-frame placement.',
                art_review='Pending user visual acceptance. Original sequences, effects, timing, seven pose structures and idle alias retained.',
                review_note='双方枪兵战斗场景：横向加宽约8%，高度保留；每方统一14色，合并相近明暗与细碎高光。盟军蓝灰甲、敌军暗红甲；保留原姿势结构、脚底锚点、动画时序和命中时刻。仅更新对照页，尚未接入测试包。',
                batches=[{'id': '同尺寸双方待机对照', 'review': f'{base}/reviews/factions-dark.png'},
                         {'id': '本方七姿势修改前后', 'review': f'{base}/reviews/{side}-previous-and-new-dark.png'}],
                runtime_integrated=False)
    data.pop('qa', None)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

path = R / 'tools/export_gallery.py'
source = path.read_text().replace("in ['archer-battle-light-armor-v3-20261019'",
                                 "in ['spearman-battle-width-palette-20261019','archer-battle-light-armor-v3-20261019'")
path.write_text(source)
path = R / 'index.html'
source = path.read_text().replace('data-default-action="professions-class-12-ally-battle--class_12_ally_bow"',
                                 'data-default-action="professions-class-6-ally-battle--original_class_6_normal"')
source = source.replace('弓箭手 · 轻甲造型修订稿', '枪兵 · 加宽与减色稿')
links = [('?action=professions-class-6-ally-battle--original_class_6_normal', '盟军枪兵 · 完整攻击'),
         ('?action=professions-class-6-enemy-battle--original_class_6_enemy_normal', '敌军枪兵 · 完整攻击'),
         ('?action=professions-class-6-ally-battle--reaction-idle', '盟军枪兵 · 待机'),
         ('?action=professions-class-6-enemy-battle--reaction-idle', '敌军枪兵 · 待机'),
         (V.name + '/overview.mp4', '本轮枪兵动作总览'),
         (V.name + '/reviews/factions-dark.png', '双方同尺寸对照'),
         (V.name + '/reviews/ally-previous-and-new-dark.png', '盟军七姿势修改前后'),
         (V.name + '/reviews/enemy-previous-and-new-dark.png', '敌军七姿势修改前后'),
         (V.name + '/verification.json', '制作与检查记录')]
nav = '<nav class="links" aria-label="本轮枪兵战斗场景" style="margin-bottom:12px">'
nav += ''.join(f'<a href="{url}">{label}</a>' for url, label in links) + '</nav>\n'
nav += '<p class="action-note" style="margin:0 0 22px">本轮仅优化双方枪兵战斗场景：人物横向加宽约8%，身高保留；同一阵营的七个姿势共用14色，减少细碎明暗。保留盟军蓝灰甲、敌军暗红甲以及下裙甲结构，沿用原有持枪、突刺和奔跑姿势，脚底锚点与动画节奏保持。仅更新对照页，尚未接入测试包。</p>\n'
start = source.index('<nav class="links" aria-label="本轮弓箭手战斗场景"')
source = source[:start] + nav + source[start:]
source = source.replace('本轮重做双方弓箭手的轻甲服装：', '此前完成的双方弓箭手轻甲服装：')
source = source.replace('?v=archer-battle-light-armor-v3-20261019', '?v=' + V.name)
path.write_text(source)
print('Updated both spearman preview mappings and gallery links.')
