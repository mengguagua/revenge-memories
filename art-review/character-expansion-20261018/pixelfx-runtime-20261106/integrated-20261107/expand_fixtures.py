"""Fill gaps in the playback catalog from the reachable Godot attack inventory."""
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'source/full-battle-20261107'
RULES = HERE.parents[3] / 'actual/data/legacy/rules_full.json'
ITEMS = {int(item['id']): item['name_zh'] for item in json.loads(RULES.read_text())['items']}
BODY = {
    1001: '裂石爪', 1002: '碎岩喷吐', 1003: '骸颚撕咬', 1004: '蚀息',
    1005: '翼喙重击', 1006: '日冠聚光',
}
EXTRA = {
    'outcome-critical': '剑士 · 必杀剑击',
    'outcome-recoil': '佣兵 · 暗黑剑反噬',
    'counter-near': '士兵 · 近身守备反击',
    'counter-ally': '士兵 · 远距守备反击',
}
RANGED = {'archery', 'javelin', 'lightning-sword'}


def identity(row, reach=False):
    unit, event = row['actor'], row['event']
    return (row['family'], unit['name_zh'], unit['side'], bool(unit.get('promoted')),
            int(event['weapon_index']), bool(reach and int(event['distance']) > 1))


def movement(row):
    name = row['actor']['name_zh']
    family, _, side, promoted, weapon, ranged = identity(row, True)
    if row['id'] in EXTRA:
        return EXTRA[row['id']]
    if family == 'mechanical':
        return row['label']
    move = {
        'sword': '暗黑剑' if weapon == 14 else '普通剑击',
        'lance': '枪击', 'javelin': '投枪', 'archery': '银弓' if weapon == 22 else '弓箭',
        'lightning-sword': '雷剑',
        'monster': BODY.get(weapon, '近身攻击'),
    }.get(family, ITEMS.get(weapon, '攻击'))
    if family in RANGED or family == 'monster' and weapon in (1002, 1006):
        move += '（远距）' if ranged else '（近距）'
    if promoted:
        name += '（进阶）'
    if side == 'enemy' and family in {'sword', 'lance', *RANGED} and name != '断路匪':
        name += '（敌方）'
    return name + ' · ' + move


def expand(original):
    ids = {row['id'] for row in original}
    already = {
        identity(row, row['family'] in RANGED or row['family'] == 'monster')
        for row in original if row['family'] not in {'map', 'cinema', 'mechanical'}
    }
    inventories = [json.loads((SOURCE / name).read_text())['jobs']
                   for name in ('inventory.json', 'inventory-special.json')]
    selected = []
    for row in sorted(sum(inventories, []), key=lambda job: (
        job.get('heavy', False), job.get('far', ''), job['id']
    )):
        key, family = row['id'], row['family']
        if key in ids or family in {'cinema', 'reaction'}:
            continue
        if key not in EXTRA and (key.startswith('counter-') or key.startswith('outcome-')):
            continue
        group = identity(row, family in RANGED or family == 'monster')
        if family != 'mechanical' and key not in EXTRA and group in already:
            continue
        already.add(group)
        ids.add(key)
        chosen = {field: row[field] for field in ('id', 'family', 'actor', 'target', 'exchange', 'event')}
        chosen.update(title=movement(row), archive='pre-fix', program=row['program'])
        selected.append(chosen)
    return sorted(selected, key=lambda row: (row['family'], row['title'], row['id']))


if __name__ == '__main__':
    target = HERE / 'capture-fixtures.json'
    original = [row for row in json.loads(target.read_text()) if not row.get('archive')]
    added = expand(original)
    target.write_text(json.dumps(original + added, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f'{len(original)} retained, {len(added)} added')
