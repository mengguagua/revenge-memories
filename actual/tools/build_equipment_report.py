#!/usr/bin/env python3
"""Build internal equipment design notes and the actual-UI screenshot gallery."""
import json
import hashlib
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/equipment-0.3.9'


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    schedule = read('data/equipment_progression.json')
    campaign = read('data/campaign.json')
    stages = {d['code']: d for d in (read('data/stages/' + p.name) for p in sorted((ROOT / 'data/stages').glob('*.json')))}
    by_id = {str(d['id']): d for d in stages.values()}
    items = {x['id']: x for x in read('data/legacy/rules_full.json')['items'] + schedule['items']}

    def names(ids):
        return '、'.join(items[int(i)]['name_zh'] for i in ids)

    text = ['# 前两章武器与投放设定 · 0.3.9', '',
            '本文为内部设计资料，包含投放地点与隐藏规则。玩家状态页只显示当前装备；装备说明仅保留操作与装备效果，不公开掉率、必掉、装备池或补给保底。', '',
            '0.3.9采用两条战利品路径：明确携带的装备正常击杀后必掉；未携带装备的敌人约10%掉落分级战利品。携带必掉沿用《外传》的设计，未携带者10%分级掉落属于本作改编。新增铜/铁级武器、法器与固定补给继续保留。', '',
            '## 保底与携带', '',
            '- 男主第一章最多可招募8人，女主第二章最多可招募7人；开局与加入时，每人带一件适用武器，法师和修女使用法器。格曼当前无招募事件，不计满员人数。',
            '- 章末全员拥有适用武器不依赖访问奖励或随机掉落；支线招募仍需完成对应条件。',
            '- 每人仍只有一个携带槽。武器、盾、戒指互斥；带盾时使用职业默认攻击，武器可留在本队行囊备用。',
            '- 东西两队物品独立。每队增加一面固定钢盾，共增加2面；原有皮盾访问奖励保留。', '',
            '## 新增基础装备', '', '| 武器 | 威力/加成 | 命中 | 重量 |', '|---|---|---|---|']
    for item in schedule['items']:
        focus = item['family'] == 'focus'
        text.append(f'|{item["name_zh"]}|+{item["might"]}|{"加成+" if focus else "基础"}{item["hit"]}{"" if focus else "%"}|{item["weight"]}|')
    text += ['', '铜/铁剑和枪为1格；铜/铁弓为1—3格、对飞行特效，钢弓/圣弓仍为1—5格。法器只增强已学会的攻击法术，不增加法术，也不改变治疗、射程与生命消耗。', '',
             '## 队员加入装备', '', '| 队伍 | 队员 | 装备 |', '|---|---|---|']
    armies = {'第一章·男主队': ['hunapu', 'daan', 'otto', 'fula', 'lena', 'lance', 'beck', 'hervi'],
              '第二章·女主队': ['eileen', 'mireille', 'lisa', 'carlo', 'lord', 'roan', 'shia']}
    for army, members in armies.items():
        for key in members:
            text.append(f'|{army}|{campaign["characters"][key]["name_zh"]}|{names([schedule["starter_items"][key]])}|')
    text += ['', '全部成员存活并加入、领取全部固定补给/访问/宝箱时，男主队共21件武器或法器、4面盾；女主队共17件武器或法器、4面盾。不含敌军战利品（包括明确携带的必掉装备）。每人只携带其中一件，其余留在各自行囊。']
    text += ['', '## 固定战后补给', '', '下列物品自动收入本队行囊并显示提示，每关只发一次。', '', '| 关卡 | 补给 |', '|---|---|']
    for key, ids in schedule['clear_rewards'].items():
        stage = by_id[key]
        text.append(f'|{stage["code"]} {stage["name_zh"]}|{names(ids)}|')
    text += ['', 'S11原有通关钢剑与“取回工具”的钢枪奖励继续保留。', '', '## 建筑访问与探索', '', '| 关卡 | 交互位置 | 一次性奖励 |', '|---|---|---|']
    for stage in stages.values():
        for obj in stage['objects']:
            if obj.get('kind') == 'visit' and obj.get('reward_item'):
                text.append(f'|{stage["code"]} {stage["name_zh"]}|{obj["label"]}|{names([obj["reward_item"]])}|')
    text += ['|F23通关后|礁岛·渔村岸边，岸上宝箱|圣剑|', '|F25通关后|潮狩军港·神教仓院，军港武器箱|圣弓|', '',
             'S11工具间原先重复投放钢枪，现改为铁弓；工具回收与兰斯加入仍各有钢枪。建筑与门前访问方式不变。', '',
             '## 敌人携带与掉落', '',
             f'- 明确携带者从上一版33名收紧为{sum(len(v) for v in schedule["enemy_loadouts"].values())}名；所持装备在战斗中实际生效，正常击杀必定获得，不再判定35%—70%。',
             '- 其余148名敌人（含10名增援）采用名义10%的普通战利品判定；该规则不在玩家界面中预告。当前8位随机数离散取值下，单次普通判定为26/256，约10.16%。',
             '- 每次实际击杀最多一件战利品；重复死亡处理不能重掷或复制。投降、逃走及无击杀者的事件移除不掉落。',
             '- 击杀者空手且适用则直接携带；空手但不适用则寄存本队；手里已有物品则显示保留/替换/寄存选择。',
             '- 空手魔物的原版极低概率掉落优先判定；未成功才进入10%普通池，不会同时出两件。传奇掉落章限额不影响普通掉落；当前可触发的稀有武器仍为流星枪。',
             '- 普通池不包含格拉迪乌斯、流星枪、太阳枪、月光枪、法尔西昂、王家之剑、龙盾、天使戒与速度戒。', '',
             '| 关卡 | 敌人 | 携带物 | 掉率 |', '|---|---|---|---|']
    for code, loadouts in schedule['enemy_loadouts'].items():
        stage = stages[code]
        enemies = {u['id']: u for u in stage['enemies']}
        for key, (item, chance) in loadouts.items():
            text.append(f'|{code} {stage["name_zh"]}|{enemies[key]["name_zh"]}（{key}）|{names([item])}|{chance}%|')
    text += ['', 'F24士兵首领继续携带可使用的钢枪；投枪仍可由该关固定补给获得。S21首领明确携带的投枪改为击杀必掉。', '',
             '## 未携带者的分级装备池', '',
             '按敌人自身等级选择：Lv1—2基础、Lv3—5中级、Lv6—9进阶、Lv10以上高级。上级职业达到Lv3、或首领达到Lv5时，最低使用进阶池；早期Lv3普通首领仍使用中级池。兵种区分剑、枪、弓、法器及魔物遗物。', '',
             '下表权重是通过约10%掉落判定之后的池内选择比例，不是每次击杀概率。例如低级枪兵掉铜枪约为10%×70%。', '',
             '| 兵种 | 等级档 | 池内装备与权重 |', '|---|---|---|']
    role_labels = {'sword': '剑兵', 'lance': '枪兵/骑兵', 'bow': '弓兵', 'focus': '法系', 'monster': '魔物遗物'}
    tier_labels = ['基础', '中级', '进阶', '高级']
    for role, tiers in schedule['random_loot']['pools'].items():
        for tier, pool in enumerate(tiers):
            entries = '、'.join(names([entry['item_id']]) + str(entry['weight']) + '%' for entry in pool)
            text.append(f'|{role_labels[role]}|{tier_labels[tier]}|{entries}|')
    text += ['',
             '## 旧存档', '',
             '- 在非战斗场景、据点或重新整备时，补发已过关卡的新补给；对当前队员与本队武器做适用性匹配，仅缺口补基础装备。',
             '- 保留已有装备、成长与阵亡。已带盾时不覆盖，缺少的武器寄存行囊；阵亡者不补发。手动卸下后不会反复生成免费武器。',
             '- 正在进行中的战斗保留单位、携带物和战况，已携带者也按新规则必掉，不再读取旧百分比；未携带者进入分级10%规则。重新整备/下一关使用收紧后的携带者名单。',
             '- 奖励独立记录；读档、重复结算、重进据点不能反复领取。重试恢复开战前库存，不保留失败战斗的掉落。',
             '- 行囊满时自动剧情补给仍保留，手动战利品选择继续按原容量规则处理。', '',
             '## 配置与验证', '',
             '配置源为 `data/equipment_progression.json`，原版0—58号定义不变，新物品为59—66号。重建地图/角色后运行 `python3 tools/balance_equipment.py` 可重新应用投放表。', '',
             '验证见 `reports/equipment-0.3.9/`。定向边界夹具与实际按键试玩分开记录，不把夹具当作自然通关。']
    (ROOT / 'docs/前两章武器与投放设定.md').write_text('\n'.join(text) + '\n')
    if (OUT / 'package-checks.json').exists():
        captures = read('reports/equipment-0.3.9/captures.json')
        tests = read('reports/equipment-0.3.9/checks.json')
        loot = read('reports/equipment-0.3.9/loot-checks.json')
        ui_patch = (OUT / 'package-ui-checks.json').exists()
        package = read('reports/equipment-0.3.9/package-ui-checks.json' if ui_patch else 'reports/equipment-0.3.9/package-checks.json')
        state = read('reports/chapter2/state-checks.json')
        claims = read('reports/chapter2/equipment-claim-check.json')
        samples = [read('reports/battlefield-0.3.0/play/' + label + '/' + label + '-play.json')
                   for label in ['equipment-0.3.9']]
        assert all(d['passed'] for d in [captures, tests, loot, package, state, claims] + samples)
        images = []
        from PIL import Image
        for record in captures['shots']:
            path = ROOT / record['path'].replace('res://', '')
            images.append({'path': path.relative_to(ROOT).as_posix(), 'pixels': list(Image.open(path).size), 'bytes': path.stat().st_size})
        pck = ROOT / 'dist/RevengeMemories.app/Contents/Resources/RevengeMemories.pck'
        summary = {'version': '0.3.9', 'passed': True, 'new_weapon_types': 8, 'enemy_loadouts': loot['explicit_carriers'],
                   'ordinary_enemies': loot['unheld'], 'reinforcements': loot['reinforcements'], 'carried_drop_percent': 100, 'ordinary_drop_percent': 10,
                   'guaranteed_full_roster': {'west': 8, 'east': 7},
                   'all_fixed_rewards': {'west': {'weapons': 21, 'shields': 4}, 'east': {'weapons': 17, 'shields': 4}},
                   'checks': {'equipment': tests['checks'], 'loot': loot['checks'], 'chapter2_state': state['checks'], 'claims': claims['checks'], 'package': package['checks']},
                   'playthroughs': [{k: b[k] for k in ['code', 'outcome', 'final_turn', 'key_inputs']} for sample in samples for b in sample['battles']],
                   'key_inputs': sum(sample['inputs'] for sample in samples), 'images': images,
                   'layout_errors': captures['layout_errors'], 'background_guard': True, 'visible_windows': False,
                   'scope': 'Text-only hide-loot-hints patch: fresh status and four-page help captures plus external runtime-pack UI checks. Mechanics and battle-play evidence above are the prior 0.3.9 verification, not rerun for this presentation patch.' if ui_patch else 'Two independent actual-keyboard battle samples from genuine checkpoints, not a continuous full campaign. Boundary/state checks are explicitly fixtures.',
                   'pck_bytes': pck.stat().st_size, 'pck_sha256': hashlib.sha256(pck.read_bytes()).hexdigest()}
        (OUT / 'delivery-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
        body = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
                '<title>前两章装备投放 · 0.3.9</title><style>body{margin:0;background:#101e23;color:#eee9db;font:17px/1.7 system-ui,sans-serif}main{max-width:1050px;margin:auto;padding:32px 24px}a{color:#dccb83;text-underline-offset:4px}a:focus-visible{outline:none;box-shadow:0 0 16px #dccb8388;border-radius:5px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px}article{background:#20383e;border-radius:14px;overflow:hidden}article h2,article p{margin:18px 22px}img{width:100%;height:auto;image-rendering:pixelated;display:block}</style><main>',
                '<h1>装备界面 · 0.3.9</h1><p>状态页只显示人物属性与当前装备，装备说明保留操作方法。物品获取规律留待玩家探索。</p>',
                '<p><a href="../../docs/前两章武器与投放设定.md">内部设计资料（含剧透）</a> · <a href="delivery-summary.json">实际验证记录</a></p>',
                '<p>实际按键抽样与定向规则检查见验证记录。Godot实机截图使用启动前后台防护和离屏视口，文字安全区0错误。</p><section class="grid">']
        labels = {'01-west-bronze-sword': '男主装备', '02-enemy-bow-drop': '敌军装备', '03-east-iron-sword': '女主装备', '04-healer-copper-focus': '修女装备', '05-west-reserve-weapons': '本队装备行囊', '06-unheld-random-drop': '未携带装备'}
        labels.update({'07-equipment-help-' + str(i): '装备操作说明 · ' + str(i) for i in range(1, 5)})
        for image in images:
            name = Path(image['path']).name
            label = labels[Path(name).stem]
            body.append(f'<article><h2>{html.escape(label)}</h2><a href="screenshots/{name}"><img src="screenshots/{name}" alt="{html.escape(label)}" width="426" height="240"></a></article>')
        body.append('</section></main></html>')
        (OUT / 'index.html').write_text('\n'.join(body))
    print('Updated equipment document from authoritative schedule.')


if __name__ == '__main__':
    main()
