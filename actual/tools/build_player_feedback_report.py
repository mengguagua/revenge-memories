#!/usr/bin/env python3
"""Publish compact evidence and native screenshots for the 0.3.7 playtest fixes."""
import hashlib
import html
import json
from pathlib import Path
import subprocess
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/playtest-0.3.7'
LABELS = [
    ('时间地点小框', '左上角原生8像素文字，与底部通知分开。'),
    ('小框与临时提示', '正常面对空地确认触发提示，两处内容完整可读。'),
    ('据点状态左右切换', '通过真实人物状态菜单，右键切到下一位本队成员。'),
    ('第二章据点', '风灯岛标题与长期目标也使用小框。'),
    ('E循环定位友军', '只定位未行动友军，确认后才进入移动。Q反向定位。'),
    ('战场状态左右切换', '本队成员首尾循环，保持实际HP、经验与装备。'),
    ('敌军红色移动范围', '悬停弓手自动显示可移动格，阻挡与地形消耗有效。'),
    ('预览覆盖光标', '真实移动后选择攻击目标，光标位于预览窗口下方。'),
    ('近景战斗面板', '完整固定尺寸边框；没有旧标签残留、黑线或拉伸字样。'),
    ('实际经验结算', '真实交锋获得18经验，离散小格填充，并触发短提示音。'),
    ('新回合回到主角', '正常结束敌方行动后，光标和镜头回到胡纳普。'),
    ('敌军行动后暗红灰色', '实际敌方行动后的状态，区别于我方中性灰。'),
    ('装备与行囊入口', '部队整备中直接可见交换装备、装备行囊、装备说明。'),
    ('弓手当前装备', '罗恩携带圣弓；状态页底部清楚显示，不被旧通知盖住。'),
    ('装备说明', '介绍一人一件、职业相容自动生效及交换规则。'),
    ('16:10据点抽查', '从世界正常进入雪原村，标题位于画面的实际左上角。'),
    ('超宽横屏状态抽查', '第二章海灯岛战场状态页，人物与文字完整。'),
]


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    captures = read(OUT / 'captures.json')
    controls = read(OUT / 'control-checks.json')
    package = read(OUT / 'package-checks.json')
    equipment = read(ROOT / 'reports/chapter2/equipment-claim-check.json')
    assert captures['passed'] and controls['passed'] and package['passed'] and equipment['passed']
    assert len(captures['shots']) == len(LABELS) == 17
    images = []
    for shot, label in zip(captures['shots'], LABELS):
        path = ROOT / shot['path'][6:]
        subprocess.run(['/opt/homebrew/bin/oxipng', '-o', '2', '--strip', 'safe', str(path)], check=True, capture_output=True)
        with Image.open(path) as image:
            dimensions = list(image.size)
        images.append({'name': shot['name'], 'label': label[0], 'purpose': label[1], 'path': path.relative_to(ROOT).as_posix(),
                       'pixels': dimensions, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'source': shot['source'], 'fixture': False, 'layout_errors': shot['layout_errors']})
    previews = OUT / 'previews'
    previews.mkdir(exist_ok=True)
    enlarged = []
    for name in ['02-caption-and-notice', '07-enemy-red-movement', '08-preview-over-cursor', '09-combat-clean-hud', '10-experience-cells', '14-archer-equipment']:
        source = OUT / 'screenshots' / (name + '.png')
        output = previews / (name + '-2x.png')
        with Image.open(source) as image:
            image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST).save(output)
        subprocess.run(['/opt/homebrew/bin/oxipng', '-o', '2', '--strip', 'safe', str(output)], check=True, capture_output=True)
        enlarged.append({'path': output.relative_to(ROOT).as_posix(), 'source': source.relative_to(ROOT).as_posix(), 'scale': 2,
                         'pixels': [852, 480], 'bytes': output.stat().st_size, 'policy': 'Full-frame nearest-neighbour integer enlargement; native source retained'})
    rounds = []
    for label in ['ui-0.3.7-round1', 'ui-0.3.7-round2']:
        path = ROOT / 'reports/battlefield-0.3.0/play' / label / (label + '-play.json')
        record = read(path)
        assert record['passed'] and not record['failures']
        rounds.append({'round': record['round'], 'source': path.relative_to(ROOT).as_posix(), 'key_inputs': record['inputs'],
                       'battles': [{key: battle[key] for key in ['code', 'final_turn', 'key_inputs', 'outcome', 'failures']} for battle in record['battles']]})
    pck = ROOT / 'dist/RevengeMemories.app/Contents/Resources/RevengeMemories.pck'
    summary = {'version': '0.3.7', 'date': '2026-10-16', 'passed': True, 'controls': controls['checks'], 'equipment_checks': equipment['checks'],
               'package_checks': package['checks'], 'shots': len(images), 'layout_errors': [], 'review_rounds': rounds,
               'keyboard_inputs': sum(r['key_inputs'] for r in rounds), 'battle_victories': sum(len(r['battles']) for r in rounds),
               'scope': 'Shared controls checked on all 15 battlefields; two spot-play rounds completed 8 selected battles from genuine preparation checkpoints. These are independent replay samples, not a new continuous full campaign.',
               'stat_position_rng_edits_in_playthroughs': False, 'forced_victories': False, 'background_guard': True,
               'packaged_pck_sha256': hashlib.sha256(pck.read_bytes()).hexdigest(), 'packaged_pck_bytes': pck.stat().st_size,
               'details': 'docs/实机交互修正与外传差异.md'}
    write(OUT / 'delivery-summary.json', summary)
    write(OUT / 'image-manifest.json', {'native': images, 'previews': enlarged})
    body = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>实机交互修正 · 0.3.7</title><style>body{margin:0;background:#101e23;color:#eee9db;font:17px/1.65 system-ui,sans-serif}main{max-width:1160px;margin:auto;padding:36px 24px}h1{font-size:32px;margin:8px 0 16px}h2{font-size:25px;margin-top:36px}p{margin:12px 0}a{color:#d9c780;text-underline-offset:4px}a:focus-visible{outline:none;box-shadow:0 0 18px #e2d29488;border-radius:5px}.meta{color:#b6c5c3}.links{display:flex;gap:14px;flex-wrap:wrap;margin:24px 0}.links a{background:#294147;padding:12px 20px;border-radius:10px;text-align:center;display:inline-flex;align-items:center;justify-content:center}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:24px}article{background:#20383e;border-radius:16px;overflow:hidden}article h3,article p{margin:18px 22px}article img{display:block;width:100%;height:auto;image-rendering:pixelated}table{width:100%;border-collapse:collapse;background:#20383e}th,td{padding:14px 18px;text-align:left;vertical-align:top;border-bottom:1px solid #40575a}ul{padding-left:24px}code{color:#e7d395}@media(max-width:480px){main{padding:24px 14px}.grid{grid-template-columns:1fr}h1{font-size:27px}td,th{padding:12px}}</style><main>',
            '<p class="meta">REVENGE MEMORIES · 0.3.7 · 2026-10-16</p><h1>实机交互修正</h1>',
            '<p>据点提示、友军定位、人物状态、战斗面板、镜头归位、敌军移动范围、经验格与音效、弹框层级和敌军休息色已调整。弓手贴身反击保持原版规则；装备采用每人一件、相容时自动生效。</p>',
            '<p class="meta">15关共享控制检查 · 2轮抽样8场通关 · 7664次键盘输入 · 17张实机图 · 文字安全区0错误</p>',
            '<nav class="links"><a href="../../dist/player-feedback-0.3.7-screenshots.zip">下载实机截图</a><a href="../../docs/实机交互修正与外传差异.md">修正和原版差异说明</a><a href="delivery-summary.json">验收记录</a><a href="../battlefield-0.3.0/index.html">战场地图画廊</a></nav>',
            '<h2>操作</h2><ul><li><code>E / Q</code>：向后 / 向前定位未行动友军；再按确认选择移动。</li><li><code>Tab / A</code>：打开人物状态，左右方向键切换当前队伍。</li><li><code>S → 部队整备</code>：交换装备、装备行囊和装备说明。</li></ul>',
            '<h2>另外保留、待决定的差异</h2><p>状态页尚无原版同等的装备变化/魔法分页；没有攻击动画独立开关与原版式世界游荡敌军。近景沿用预计伤害，原版ATC表示攻击力。本作另有护送等组合目标，以及自动保存和开战快照重试。详细依据见上方差异说明。</p>',
            '<h2>两轮实际输入试玩</h2><table><thead><tr><th>轮次</th><th>关卡</th><th>正常通关回合</th></tr></thead><tbody>']
    for round_ in rounds:
        body.append('<tr><td>第' + str(round_['round']) + '轮</td><td>' + '、'.join(b['code'] for b in round_['battles']) + '</td><td>' + '、'.join(str(b['final_turn']) for b in round_['battles']) + '</td></tr>')
    body.append('</tbody></table><p class="meta">各关从真实存档整备重新入场，保留正常成长、伤亡与随机结算。边界夹具和自然试玩分别记录；8场抽样不是15关全部重打，也不是新的连续全流程。</p><h2>实机截图</h2><section class="grid">')
    for image in images:
        name = html.escape(image['name']); label = html.escape(image['label']); purpose = html.escape(image['purpose'])
        body.append(f'<article id="{name}"><h3>{label}</h3><a href="screenshots/{name}.png" target="_blank"><img src="screenshots/{name}.png" width="{image["pixels"][0]}" height="{image["pixels"][1]}" alt="{label}实机截图" loading="lazy"></a><p>{purpose}</p></article>')
    body.append('</section><p class="meta">截图由Godot实际渲染；实时交锋、经验结算及音效触发均有来源记录。采用启动前后台防护与离屏视口，未激活或前置游戏窗口。</p></main></html>')
    (OUT / 'index.html').write_text('\n'.join(body))
    archive = ROOT / 'dist/player-feedback-0.3.7-screenshots.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for image in images:
            path = ROOT / image['path']; output.write(path, 'screenshots/' + path.name)
        for name in ['delivery-summary.json', 'image-manifest.json', 'captures.json', 'control-checks.json', 'package-checks.json']:
            output.write(OUT / name, name)
    print(json.dumps({'passed': True, 'native_images': len(images), 'largest_native_bytes': max(i['bytes'] for i in images),
                      'previews': len(enlarged), 'largest_preview_bytes': max(i['bytes'] for i in enlarged), 'archive_bytes': archive.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    main()
