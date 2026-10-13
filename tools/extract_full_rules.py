#!/usr/bin/env python3
"""Extract full FE2 rules tables from original, SHA-verified rebuilt ROM + ASM.
No runtime ROM dependency; output is ordinary native game data.
"""
import argparse, hashlib, json, re
from pathlib import Path
from extract_opening import Source

ZH = ['普通武器','普通弓','钢枪','银枪','投枪','圣枪','骑士杀手','格拉迪乌斯','流星枪','太阳枪','月光枪','钢剑','银剑','勇者剑','暗黑剑','雷之剑','圣剑','法尔西昂','王家之剑','触手','钢弓','圣弓','银弓','火球','雷电','诸神黄昏','圣光','风刃','箭雨','光环','盖亚','多拉','史莱姆','死亡','美杜莎','恢复','全体恢复','召唤','眼光','眼球','恢复','远程恢复','吸血','传送','全体恢复','幻影','驱邪','无法攻击','皮盾','钢盾','银盾','圣盾','封魔盾','龙盾','圣戒','天使戒','速度戒','魔道戒','祈祷戒']

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,default=Path('/private/tmp/fe2-analysis-20261012')); ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data/rules_full.json'); a=ap.parse_args()
    s=Source(a.source); rom=(a.source/'fe2.nes').read_bytes()
    assert hashlib.sha1(rom).hexdigest()=='2153ae9a7b1c63e8d4d83a807f1c8c1f482f7293'
    def raw(addr,n): return list(rom[16+15*16384+addr-0xC000:16+15*16384+addr-0xC000+n])
    def ref(bank,label): return s.ref(bank,label)
    arrays={k:raw(ad,n) for k,ad,n in [('might',0xD9B9,59),('hp_cost',0xD9F4,48),('weight',0xDA24,48),('hit',0xDA54,48),('critical',0xDA84,48),('effective',0xDAB4,48),('target_flags',0xDAFD,59),('effect_kind',0xDB38,59)]}
    assert arrays['might'][:23]==[0,0,4,8,3,3,3,15,10,20,10,4,8,5,13,15,3,10,7,12,3,5,7]
    name_labels=re.findall(r'\.dw (\w+)',s.block(15,'L0FDCAD'))
    support={35:'recover',36:'fortify',37:'conjure',40:'recover',41:'physic',43:'warp',44:'fortify',45:'invoke',46:'expel'}
    items=[]
    for i in range(59):
        item={'id':i,'name_zh':ZH[i],'name_ja':s.strings(15,name_labels[i])[0], 'kind': 'accessory' if i>=48 else 'support' if i in support else 'spell' if i>=23 else 'weapon'}
        for k,v in arrays.items():
            if i<len(v): item[k]=v[i]
        item['action']=support.get(i,'attack' if i<47 else 'none')
        if i in support:
            item['target']='ally_adjacent' if i in [35,40,43] else 'ally_anywhere' if i==41 else 'all_allies' if i in [36,44] else 'summon' if i in [37,45] else 'terrors'
        items.append(item)
    effects={str(i):s.db(15,label)[:-1] for i,label in [(1,'L0FDAEE'),(2,'L0FDAF4'),(3,'L0FDAF6'),(4,'L0FDAF9')]}
    spell_tables={str(c):raw(0xE199+8*index,8) for index,c in enumerate([11,15,16,17,18,19])}
    enemy_spell_tables={str(c):raw(0xE1C9+8*index,8) for index,c in enumerate([11,15,16,17,18,19])}
    learn=raw(0xE299,0xE360-0xE299); learns={}
    for offset in range(0,len(learn)-1,11):
        record=learn[offset:offset+11]; learns[str(record[0])]=[{'level':record[i],'spell_id':record[i+1]} for i in range(1,11,2) if record[i]>0]
    before=s.db(15,'L0FE3A7')[:-1]; after=s.db(15,'L0FE3B5'); levels=s.db(15,'L0FE3C2')
    promo=[{'from_class':f,'to_class':t,'level':l} for f,t,l in zip(before,after,levels)]
    labels=re.findall(r'\.dw (\w+)',s.block(15,'L0FED04'))
    stats=['strength','skill','speed','luck','defence','max_hp','exp_value']
    bases={str(i+1):dict(zip(stats,s.db(15,l))) for i,l in enumerate(labels)}
    out={'source_commit':'956365ef33c63751e7afd03f05e600d7728549da','source_rom_sha1':hashlib.sha1(rom).hexdigest(),'items':items,'effectiveness_classes':effects,'player_spell_tables':spell_tables,'enemy_spell_tables':enemy_spell_tables,'spell_learning':learns,'promotions':promo,'villager_options':s.db(15,'L0FE3CF'),'promotion_bases':bases,'class_move':raw(0xEDD3,23),'class_resistance':raw(0xEDEA,22),'character_resistance':raw(0xEE00,35),'summon_offsets':[[((v+128)%256)-128 for v in pair] for pair in zip(s.db(3,'L03969F')[0:-1:2],s.db(3,'L03969F')[1:-1:2])], 'provenance':[ref(15,x) for x in ['L0FD9B9','L0FD9F4','L0FDA24','L0FDA54','L0FDA84','L0FDAB4','L0FDAFD','L0FDB38','L0FE199','L0FE299','L0FE3A7','L0FE3B5','L0FE3C2','L0FE3CF','L0FED04']]+[ref(9,x) for x in ['L098125','L09877E','L098922','L098A63','L098CC8']]+[ref(8,'L08A804'),ref(8,'L08A96C'),ref(3,'L039267'),ref(3,'L03956A')], 'notes':{'learning':'A separate magic training counter survives normal promotion; entering Mage from Villager resets it. Displayed character level is not sufficient after promotion.','promotion':'Stats rise to class bases; if none rise, max HP +1 up to52; level1 EXP0. Alm story promotion is a flag, not a new runtime class.','expel':'Entire map; enemy classes3/5/11/17, first enemy slot excluded by original; succeeds if (random_byte &15) < caster strength.','invoke':'Character15 summons soldiers,14 dread fighters,30 pegasus knights. Count floor(random_bounded(strength)/2)+2, limited by free deployment slots/valid cells.','poison':'Poison/swamp is terrain category16 damage5, never below1; no unverified ongoing poison status is invented.','original_limits':'Holy weapon/ring/class recovery and special weapon effects follow original tables; Solar Lance has regeneration, not an on-hit lifesteal effect.'}}
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(f'Extracted {len(items)} items, {len(learns)} personal spell lists, {len(promo)} promotion paths')
if __name__=='__main__': main()
