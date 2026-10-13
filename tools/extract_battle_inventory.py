#!/usr/bin/env python3
"""Source-backed drop and retreat tables, without runtime ROM use."""
import hashlib, json
from pathlib import Path
from extract_opening import Source

root = Path(__file__).resolve().parents[1]
source = Path('/private/tmp/fe2-analysis-20261012')
s = Source(source)
rom = (source / 'fe2.nes').read_bytes()
assert hashlib.sha1(rom).hexdigest() == '2153ae9a7b1c63e8d4d83a807f1c8c1f482f7293'
def raw(address, count):
    offset = 16 + 15 * 16384 + address - 0xC000
    return list(rom[offset:offset + count])

def ref(bank, label):
    path = source / 'src' / f'bank{bank:03d}.asm'
    lines = path.read_text().splitlines()
    return {'file':f'src/bank{bank:03d}.asm','label':label,'line':next(i+1 for i,line in enumerate(lines) if line.startswith(label+':'))}

rare = raw(0xF225, 24)
output = {
    'rare_drops': [{'character_id': rare[i], 'roll_threshold': rare[i+1], 'item_id': rare[i+2]} for i in range(0, 24, 3)],
    'rare_drop_cumulative_caps_by_chapter': raw(0xF23E, 5),
    'rare_drops_disabled_from_chapter': 5,
    'retreat_chance_by_map': raw(0xE249, 80),
    'enemy_retreat_turn_by_map': raw(0xE1F9, 80),
    'enemy_initiated_retreat_paths': [s.db(15,label)[:-1] for label in ['L0FE370','L0FE374','L0FE378','L0FE37C','L0FE382','L0FE389','L0FE390','L0FE39D']],
    'convoy_capacity': 40,
    'source': [ref(bank,label) for bank,label in [(6,'L06AA37'),(6,'L06AA62'),(6,'L069D28'),(6,'L069DD1'),(6,'L06B058'),(6,'L06B13C'),(6,'L06A010'),(6,'L06A70E'),(6,'L06A4EE'),(6,'L069127'),(6,'L06B7A6'),(8,'L08A3EE'),(15,'L0FFA89')]],
    'notes': {
        'drops': 'Enemy carried item is guaranteed when that enemy actually dies; no independent drop flag. An empty-handed killer carries it, occupied killer chooses storage or replacement. Allied neutral/illusion killer sends it to convoy.',
        'player_death': 'Formal player unit carried item automatically goes to current-route convoy; neutral/illusion units are excluded.',
        'rare': 'Only enemy without a carried item; exact source character ID; two separate random[0,99] results must each be below threshold. Global cumulative count has source chapter($744C) caps and is not reset at chapter change. Disabled if source counter reaches5; native narrative chapter5 preserves source counter4 through scenario_source_chapter_counter.',
        'trade': 'Adjacent orthogonal living allied units only; target cannot have native flag4 (illusion/NPC). Swap item bytes and update usable equipped weapon; acting unit ends action via L069E1D.',
        'retreat': 'Player phase availability rolls once at phase initialization, not upon each menu opening. Return destination must not contain any world enemy. The source $7477 enemy-world-action branch uses the last matching route sequence in reverse lookup order and is disallowed in chapter2.',
        'forced_retreat': 'L06A50A checks the 40/60/255 turn table at enemy phase start. L06B7A6 then retreats the attacking world army: $7477=0 uses player route previous node; nonzero uses attacking enemy army previous node. Do not equate every timeout with player victory.',
        'storage_limit': 'Manual battle loot storage checks40; source automatic death/illusion storage has no capacity check. Native implementation preserves such automatic items even beyond40 instead of emulating SRAM overwrite.',
        'survivors': 'L08A3EE prunes defeated original enemy records from their army when retreating; it does not retain current HP. Next encounter restores remaining records with full HP.'
    }
}
(root/'data/battle_inventory.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print('Extracted 8 rare drops, 80 retreat probabilities and 8 retreat paths')
