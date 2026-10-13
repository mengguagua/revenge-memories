#!/usr/bin/env python3
"""Source-backed FE2 campaign catalog. Extraction is not a claim of runtime parity.

World node IDs, battle-map IDs and enemy-group IDs are deliberately distinct.
Reads the matching reconstructed ROM only for contiguous source tables; the
generated project contains JSON and source references, never executable ROM.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from extract_opening import Source, tilemap

REVISION = '956365ef33c63751e7afd03f05e600d7728549da'
ROM_SHA1 = '2153ae9a7b1c63e8d4d83a807f1c8c1f482f7293'
CHARACTER_KEYS = 'alm celica mycen noma lukas kliff tobin gray clair clive clive_b forsyth mae silque genny boey kamui valbar mathilda python leo atlas jesse forsyth_18 sonya deen saber luthier delthea tatiana catria palla est zeke'.split()
CHARACTER_ZH = '阿尔姆 赛莉卡 麦森 诺玛 卢卡斯 克里夫 托宾 格雷 克莱尔 克莱贝 克莱贝 福尔斯 梅伊 希尔克 洁妮 波伊 卡姆伊 巴尔博 玛蒂尔达 派森 雷欧 阿特拉斯 杰西 福尔斯 索妮娅 迪恩 塞巴 里ュ特 迪ュ特 蒂塔 卡秋娅 帕奥拉 艾丝特 吉克'.replace('里ュ特','琉特').replace('迪ュ特','迪尔德').split()
CLASS_KEYS = 'cavalier knight pegasus_knight paladin falcon_knight soldier gold_knight mercenary myrmidon dread_fighter priestess archer sniper villager mage_m mage_f saint cleric sage bow_knight fighter baron hero princess'.split()
CLASS_ZH = '骑兵 重装兵 天马骑士 圣骑士 隼骑士 士兵 黄金骑士 佣兵 剑士 魔战士 神官 弓箭手 狙击手 村民 男魔道士 女魔道士 圣女 修女 贤者 弓骑士 战士 男爵 勇者 公主'.split()
ENEMY_CLASS_KEYS = {3:'gargoyle',5:'necrodragon',11:'revenant',14:'brigand',15:'arcanist',16:'witch',17:'bonewalker',18:'mogall',19:'cantor',21:'fell_god'}
ENEMY_CLASS_ZH = {3:'石像鬼',5:'龙僵尸',11:'僵尸',14:'山贼',15:'妖术师',16:'魔女',17:'骷髅',18:'魔眼',19:'祈祷师',21:'邪神'}
WORLD_ZH = ['拉姆森林','盗贼森林','拉姆山谷','南方要塞','索菲亚南部一','索菲亚南部二','索菲亚城门','诺瓦墓地','海上一','海上二','海盗要塞','海上三','海之神殿','海上四','海上五','北方城门','索菲亚北部','索菲亚西部','索菲亚海岸','山间墓地','沙漠要塞','沙漠北部','沙漠南部','吉斯要塞','通往米拉的山谷','米拉神殿','索菲亚森林','森林村庄','多哲要塞','索菲亚森林二','森林北部','水门','国境','利盖尔平原','利盖尔山谷','龙之火山口','利盖尔瀑布','利盖尔森林','恐山','努伊巴巴馆','最后要塞','利盖尔城','亡者沼泽','沼泽墓地','多鲁克要塞','迷失森林','多玛之门','多玛沼泽','拉姆村','南方要塞','解放军基地','索菲亚城','修道院','诺瓦港','海盗要塞','海之神殿','索菲亚港','山间村庄','龙之神殿','沙漠要塞','吉斯要塞','沙漠神殿','米拉神殿','森林村庄','多哲要塞','森林神殿','水门','贤者村','利盖尔村','恐山神殿','努伊巴巴馆','秘密神殿','最后要塞','多鲁克要塞','迷失森林','多玛之门','多玛之塔','利盖尔城','龙之火山口','盗贼神殿','多玛祭坛']
NAME_ZH = {'ドゼー':'多哲','ギース':'吉斯','ドルク':'多鲁克','ヌイババ':'努伊巴巴','ルドルフ':'鲁道夫','ジュダ':'朱达','ソニア':'索妮娅','ディーン':'迪恩','マグナム':'马格南','ジェローム':'杰罗姆','ジーク':'吉克','ハンニバル':'汉尼拔','マッセナ':'马塞纳','マーラ':'玛拉','タタラ':'塔塔拉','ジャミル':'加米尔','デューテ':'迪尔德','ガゼル':'加泽尔','ザクソン':'扎克森','スレイダー':'斯雷达','ミカエラ':'米凯拉','ローソン':'罗森','ダッハ':'达哈','ガッハ':'加哈','ブライ':'布莱','シーザス':'西泽斯','ウォルフ':'沃尔夫','リゲルぐん':'利盖尔军','ギースぐん':'吉斯军','ドゼーぐん':'多哲军','ドルクくん':'多鲁克军','まどうぐん':'魔道军','かいぞく':'海盗','さんぞく':'山贼','まもの':'魔物','ドーマ':'多玛','ガルシア':'加西亚','ヘステ':'赫丝特','ミューラー':'穆勒'}
NAME_ZH.update({'サイゾー':'赛藏','ガネフ':'加尼弗','まじん':'魔人','ゴールド':'黄金弓手','はくりゅう':'白龙','リッチー':'巫妖','バルログ':'炎魔','バデス':'巴迪斯','ケルベス':'凯尔贝斯','ベルレス':'贝尔雷斯','マミー':'木乃伊'})
CHAPTER_TITLES = [('ソフィアへ!','前往索菲亚！'),('セリカのたびだち','赛莉卡启程'),('かいほうせんそう','解放战争'),('かなしみのだいち','悲伤的大地'),('さいかい そして…','重逢，然后……')]


class CatalogSource(Source):
    def __init__(self, root):
        super().__init__(root)
        self.files = {i:(root / f'src/bank{i:03}.asm').read_text() for i in range(16)}
        self.rom = (root / 'fe2.nes').read_bytes()
        assert hashlib.sha1(self.rom).hexdigest() == ROM_SHA1

    def ptrs(self, bank, label):
        return re.findall(r'^\.dw (\w+)', self.block(bank, label), re.M)

    def bytes_at(self, bank, label, count):
        addr = int(label[-4:], 16)
        offset = 16 + bank * 0x4000 + addr - (0xc000 if bank == 15 else 0x8000)
        return list(self.rom[offset:offset+count])


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def positions(src, label):
    capacity = src.bytes_at(8,label,1)[0]
    assert 0 < capacity <= 32,(label,capacity)
    # Do not interpret an adjacent unrelated table as extra deployment slots.
    raw = src.db(8,label)[:1+capacity*2]
    # Source unit offset17 is x, offset16 is y. Map headers are height,width.
    return {'label':label, 'capacity':raw[0], 'positions':[[raw[i],raw[i+1]] for i in range(1,len(raw)-1,2)], 'raw':raw}


def battlefield(src, label, filename):
    """Decode the source-matching RLE stream; check the editable TMX separately."""
    raw=src.bytes_at(2,label,8192)
    height,width=raw[0]+1,raw[1]+1
    offset=4
    tiles=[]
    while raw[offset]!=255:
        value=raw[offset];offset+=1
        if value<46:
            count=value;value=raw[offset];offset+=1
        else:
            count=1
        tiles.extend([value]*count)
    assert len(tiles)==width*height,(label,len(tiles),width,height)
    tmx=ET.parse(src.root/'maps'/filename).getroot()
    status='matches_source_matching_ROM'
    try:
        decoded=tilemap(src.root,filename)
        if decoded['tiles']!=tiles or (decoded['width'],decoded['height'])!=(width,height):
            status='TMX_differs_from_original_ROM; original_ROM_used'
    except AssertionError:
        status='TMX_header_dimensions_incorrect; original_ROM_used'
    return {'width':width,'height':height,'tile_size':16,'tileset':tmx.find('tileset').get('source'),
            'tiles':tiles,'source':f'maps/{filename}','source_map_label':label,
            'tile_indexing':'zero_based_original_metatile_ID','tmx_comparison':status,
            'original_camera_origin':[raw[3],raw[2]]}


def extract(src, output):
    first = json.loads((output / 'first_battle.json').read_text())
    class_names = src.ptrs(15,'L0FDB73')
    enemy_class_names = src.ptrs(15,'L0FDC2E')
    char_names = src.ptrs(15,'L0FDEA9')
    enemy_names = src.ptrs(15,'L0FDFBA')
    growth_labels = src.ptrs(9,'L_GROWTH_RATES')
    move_values = src.db(15,'L0FEDD3')
    enemy_resistance = src.bytes_at(15,'L0FEDEA',23)
    player_resistance = src.db(15,'L0FEE00')
    classes = {}
    for index,key in enumerate(CLASS_KEYS):
        cid = index+1
        ja = src.strings(15,class_names[index])[0] if index < len(class_names) else ''
        enemy_ja = src.strings(15,enemy_class_names[index])[0] if index < len(enemy_class_names) else ja
        classes[str(cid)] = {'id':cid,'key':key,'name_ja':ja,'name_zh':CLASS_ZH[index],
                            'enemy_key':ENEMY_CLASS_KEYS.get(cid,key), 'enemy_name_ja':enemy_ja,
                            'enemy_name_zh':ENEMY_CLASS_ZH.get(cid,CLASS_ZH[index]),
                            'move':move_values[index] if index<len(move_values) else None,
                            'enemy_resistance':enemy_resistance[index] if index<len(enemy_resistance) else None,
                            'defined_in_source':True,'runtime_table_defined':index<23}
    characters = {}
    for slot,key in enumerate(CHARACTER_KEYS,1):
        label = f'L08{0x90e2+(slot-1)*12:04X}'
        raw = src.bytes_at(8,label,12)
        cid = raw[0]
        class_id = raw[1]
        ja = src.strings(15,char_names[cid-1])[0]
        characters[key] = {'id':cid,'character_id':cid,'slot_id':slot,'key':key,
            'name_ja':ja,'name_zh':CHARACTER_ZH[slot-1],'class':CLASS_KEYS[class_id-1],
            'class_id':class_id,'level':raw[2],'hp':raw[3],'max_hp':raw[3],'exp':raw[4],
            'strength':raw[5],'skill':raw[6],'speed':raw[7],'luck':raw[8],'defence':raw[9],
            'magic_flags':raw[10],'magic_level':0,'item_id':raw[11],'move':move_values[class_id-1],
            'resistance':player_resistance[cid-1]+(15 if class_id==10 else 0),
            'growths':dict(zip(['strength','skill','speed','luck','defence','hp'],src.db(9,growth_labels[cid-1]))),
            'raw':raw,'provenance':[src.ref(8,label),src.ref(9,growth_labels[cid-1]),src.ref(15,'L0FEE00'),src.ref(6,'L068C0C')],
            'confidence':'source_character_slot_and_runtime_id_indexed_growth_resistance'}
        if slot != cid:
            characters[key]['note'] = 'Original slot has a duplicate character ID; preserve original ID and do not expose as a second recruit.'
    template_labels = src.ptrs(8,'L089A5A')
    group_labels = src.ptrs(8,'L0893C2')
    stat_labels = src.ptrs(15,'L0FED04')
    groups = {}
    for group_id,label in enumerate(group_labels):
        raw = src.db(8,label)
        count,offset = raw[0],1
        records,issues = [],[]
        for n in range(count):
            if offset >= len(raw):
                issues.append(f'declared_count_{count}_exceeds_complete_records_{n}')
                break
            if raw[offset] & 128:
                item = raw[offset:offset+6]
                item_source = label
                offset += 6
            else:
                tindex = raw[offset]
                offset += 1
                if tindex>=len(template_labels):
                    issues.append(f'template_index_{tindex}_out_of_bounds')
                    break
                item_source = template_labels[tindex]
                item = src.db(8,item_source)
            if len(item)!=6 or not 1<=item[1]<=len(stat_labels):
                issues.append('incomplete_or_invalid_enemy_record')
                break
            name_id,cid,level,item_id,flags,magic_flags = item
            base = src.db(15,stat_labels[cid-1])
            increase = (level-1)//2
            hp = base[5] if cid==21 else min(52,base[5]+3*increase)
            ja = src.strings(15,enemy_names[name_id-129])[0] if 129<=name_id<129+len(enemy_names) else ''
            cname = ENEMY_CLASS_KEYS.get(cid,CLASS_KEYS[cid-1])
            class_zh = ENEMY_CLASS_ZH.get(cid,CLASS_ZH[cid-1])
            zh = NAME_ZH.get(ja,class_zh)
            records.append({'id':f'g{group_id:02d}_{n+1:02d}','name_id':name_id,'character_id':name_id,
                'name_ja':ja,'name_zh':zh,'class':cname,'class_id':cid,'class_name_zh':class_zh,
                'level':level,'hp':hp,'max_hp':hp,'exp':0,'strength':base[0]+increase,
                'skill':base[1]+increase,'speed':base[2]+increase,'luck':base[3],
                'defence':base[4]+increase,'resistance':enemy_resistance[cid-1],
                'move':move_values[cid-1],'item_id':item_id,'exp_value':min(255,base[6]+base[6]*(level-1)//10),
                'raw_ai_flags':flags,'raw_magic_flags':magic_flags,'magic_flags':magic_flags,
                'raw_template':item,'group_id':group_id,'record_index':n,
                'provenance':[src.ref(8,label),src.ref(8,item_source),src.ref(15,stat_labels[cid-1]),src.ref(8,'L08A31B')],
                'confidence':'source_count_bounded_template_constructor'})
        groups[str(group_id)] = {'id':group_id,'source_label':label,'declared_count':count,'enemies':records,
            'deployment_priority':0 if group_id<60 else src.bytes_at(8,f'L08{0x9241+group_id:04X}',1)[0],
            'raw':raw,'valid':len(records)==count and not issues,'issues':issues,
            'trailing_bytes_ignored_by_declared_count':raw[offset:], 'provenance':src.ref(8,label)}
    chapter_armies = {}
    group_lists=src.ptrs(8,'L089291')
    node_lists=src.ptrs(8,'L089299')
    for i,(gl,nl) in enumerate(zip(group_lists,node_lists),1):
        g=src.db(8,gl);g=g[:g.index(255)]
        w=src.db(8,nl)
        chapter_armies[str(i)] = [{'group_id':gid,'world_node':node,'map_id':node,
                                  'provenance':[src.ref(8,gl),src.ref(8,nl),src.ref(8,'L089EC6')]}
                                 for gid,node in zip(g,w)]
    initial_by_node={}
    for chapter,armies in chapter_armies.items():
        for a in armies:
            initial_by_node.setdefault(a['world_node'],[]).append((int(chapter),a['group_id']))
    name_labels=src.ptrs(11,'L0BB821')
    world=json.loads((output/'world_map.json').read_text())
    world_nodes=copy.deepcopy(world['nodes'])
    for i in range(1,81):
        world_nodes[str(i)].update({'id':i,'name_ja':src.strings(11,name_labels[i-1])[0],
            'name_zh':WORLD_ZH[i-1],'kind':'battlefield' if i<=48 else 'hub',
            'enemy_group_ids':[gid for chapter,gid in initial_by_node.get(i,[])],
            'chapters':sorted({chapter for chapter,gid in initial_by_node.get(i,[])})})
    routes={'alm':{'leader':'alm','start_world_node':49,
                   'chapter_nodes':{'1':[49,1,2,3,4,50,80,51,5,6,7,52],
                                    '3':[52,16,17,27,28,64,29,65,30,31,32,67,66],
                                    '4':[32,33,34,35,36,37,38,39,40,41,42,69,70,71,72,73,78,79]}},
            'celica':{'leader':'celica','start_world_node':53,
                      'chapter_nodes':{'2':[53,8,54,9,10,11,55,12,13,56,14,15,57,7,52],
                                       '3':[52,18,19,20,21,22,23,24,25,26,58,59,60,61,62,63],
                                       '4':[26,43,44,45,46,47,48,68,74,75,76,77]}},
            'final':{'leader':'alm','chapter_nodes':{'5':[]}}}
    routes_note='Route ownership is a native reconstruction of original world graph geography. Lists describe accessible route regions, NOT a linear progression requirement or exact event gates.'
    terrain_types=src.db(15,'L0FE8DE')
    movement=src.bytes_at(15,'L0FEB0A',23*22)
    terrain={'tile_categories':{str(i):x for i,x in enumerate(terrain_types)},
             'avoid_by_category':src.db(15,'L0FECEE'),
             'movement_by_class_and_category':{str(i):movement[(i-1)*22:i*22] for i in range(1,24)},
             'impassable_movement_value':255,'provenance':[src.ref(15,'L0FE8DE'),src.ref(15,'L0FECEE'),src.ref(15,'L0FEADF')]}
    map_labels=src.ptrs(2,'L_TILEMAPS')
    deployment_labels=src.ptrs(8,'L08AB11')
    dungeon_group_bytes=src.db(8,'L08935B')
    dungeon_map_bytes=src.db(8,'L08939B')
    dungeon_by_map={mid:[g for g in dungeon_group_bytes[n*2:n*2+2] if g!=255] for n,mid in enumerate(dungeon_map_bytes)}
    # Repeated cemetery monsters are selected at chapter setup, not a guessed
    # enemy group whose numeric ID happens to equal the map ID.
    cemetery_choices={8:[8],20:[50,8,44,57,59],44:[44,57,87,52,51]}
    stages={}
    anomalies=[]
    for mid,maplabel in enumerate(map_labels[1:],1):
        bins=re.findall(r'^\.INCBIN "([^"\n]+)\.bin"',src.block(2,maplabel),re.M)
        filename=next((b+'.tmx' for b in bins if (src.root/'maps'/(b+'.tmx')).exists()),None)
        assert filename,(mid,maplabel,bins)
        m=battlefield(src,maplabel,filename)
        dlabel=deployment_labels[mid-1]
        dl=src.ptrs(8,dlabel)
        layouts=[positions(src,p) for p in dl]
        # Many 20-person formations label the second ten coordinate pairs
        # halfway through the first array. That continuation has no count byte.
        primary_end=int(dl[0][-4:],16)+1+layouts[0]['capacity']*2
        if dl[0]!=dl[1] and int(dl[0][-4:],16)<int(dl[1][-4:],16)<primary_end:
            available=min(1+layouts[0]['capacity']*2,len(src.db(8,dl[0]))+len(src.db(8,dl[1])))
            primary=src.bytes_at(8,dl[0],available)
            layouts[0]['raw']=primary
            layouts[0]['positions']=[primary[i:i+2] for i in range(1,len(primary),2)]
            raw=src.db(8,dl[1])[:primary_end-int(dl[1][-4:],16)]
            layouts[1]={'label':dl[1],'capacity':len(raw)//2,'positions':[raw[i:i+2] for i in range(0,len(raw),2)],'raw':raw,'is_continuation_without_count':True}
        assert len(layouts)==4,(mid,dlabel)
        for li,layout in enumerate(layouts):
            if len(layout['positions'])<layout['capacity']:
                anomalies.append({'kind':'declared_deployment_capacity_exceeds_stored_coordinates','map_id':mid,'layout':li,'capacity':layout['capacity'],'actual_positions':len(layout['positions']),'source_label':layout['label']})
            invalid=[p for p in layout['positions'] if not (0<=p[0]<m['width'] and 0<=p[1]<m['height'])]
            if invalid:
                anomalies.append({'kind':'deployment_position_outside_tmx','map_id':mid,'layout':li,'positions':invalid,'source_label':layout['label']})
        armies=initial_by_node.get(mid,[]) if mid<=48 else []
        assignment='source_chapter_army_placement'
        if mid<=48 and not armies:
            assignment='source_no_fixed_army; instantiate_moving_army_at_encounter'
            if mid in cemetery_choices:
                armies=[(2 if mid==8 else 3 if mid==20 else 4,cemetery_choices[mid][0])]
                assignment='source_chapter_cemetery_choice_0; choose_from_random_enemy_group_ids_at_runtime'
            elif mid==32:
                armies=[(3,32)]
                assignment='source_queued_army_0_after_Desaix_death; L08927B_43_20_then_L0FF124'
            elif mid==36:
                armies=[(4,73)]
                assignment='source_dragon_generator_6_first_wave; choose_stage73_to78_by_generator_state'
        if mid>=49:
            armies=[(5 if mid==62 or 72<=mid<=77 else 0,g) for g in dungeon_by_map[mid]]
            assignment='source_dungeon_trigger_group_and_map_pair'
        source_armies=copy.deepcopy(armies)
        if mid<=48 and len(armies)==2:
            if groups[str(armies[0][1])]['deployment_priority']>=groups[str(armies[1][1])]['deployment_priority']:
                armies.reverse()
        enemy_groups=[gid for chapter,gid in armies]
        enemies=[]
        for ai,gid in enumerate(enemy_groups):
            pos=layouts[min(ai+2,3)]['positions']
            records=groups[str(gid)]['enemies']
            # Original one-army deployment can spill to its second formation
            # once the first formation's declared capacity is exhausted.
            capacity=layouts[min(ai+2,3)]['capacity']
            if ai==0 and len(records)>min(capacity,len(pos)):
                pos=pos[:capacity]+layouts[3]['positions']
            for n,enemy in enumerate(records):
                if n>=len(pos):
                    anomalies.append({'kind':'enemy_deployment_incomplete','map_id':mid,'group_id':gid,'record':n})
                    break
                unit=copy.deepcopy(enemy);unit['position']=pos[n];enemies.append(unit)
        chapter=armies[0][0] if armies else (5 if mid in range(72,78) or mid==62 else 0)
        namezh=WORLD_ZH[mid-1] if mid<=48 else {'cave-room.tmx':'洞窟战斗','fear-mountain-shrine.tmx':'恐山神殿战斗','final-battle.tmx':'多玛祭坛决战','lost-treescape-battleground.tmx':'迷失森林战斗'}.get(filename,filename.replace('.tmx','').replace('duma-tower-','多玛之塔第').replace('duma-temple-','多玛地下神殿第')+'层')
        nameja=src.strings(11,name_labels[mid-1])[0] if mid<=48 else ''
        route=next((r for r,rd in routes.items() if any(mid in ns for ns in rd['chapter_nodes'].values()) and mid<=48),'dungeon')
        stage=copy.deepcopy(first)
        stage.update({'schema_version':3,'id':f'stage_{mid:03d}','map_id':mid,'battle_number':mid,'chapter':chapter,
            'route':route,'name_ja':nameja,'name_zh':namezh,'source_commit':REVISION,'map':m,
            'initial_party':[routes.get(route,{}).get('leader','alm')],
            'party_order':[],'party_order_note':'Deploy the current persistent route roster in user-selected order; do not reset to first-battle recruits.',
            'characters':characters,'player_positions':layouts[0]['positions'],
            'player_positions_by_party':[layouts[0]['positions'],layouts[1]['positions']],
            'enemy_positions':[e['position'] for e in enemies],'enemies':enemies,'enemy_group_ids':enemy_groups,
            'source_army_order':[g for ch,g in source_armies],
            'enemy_group_candidates':[mid] if mid in [16,18,35,46] else [],
            'enemy_assignment_confidence':assignment,'random_enemy_group_ids':cemetery_choices.get(mid,[]),
            'deployment':{'layouts':layouts,'layout_order':['player_group_0','player_group_1','enemy_group_0','enemy_group_1'],'source_label':dlabel},
            'terrain':terrain,'coordinate_order':'x,y; original deployment bytes already use this order',
            'battle_identity':{'map_id':mid,'enemy_group_ids':enemy_groups,'map_source':m['source'],
                               'source_map_pointer':maplabel,'deployment_pointer':dlabel},
            'provenance':[src.ref(2,'L_TILEMAPS'),src.ref(2,maplabel),src.ref(8,dlabel)],
            'unverified':['Exact original event gates and AI scheduling','Complete special battle events and victory overrides require native implementation','Map index is not a hub world-node ID for indices49 and above']})
        stage.pop('first_battle_identity',None)
        stage['rules']['defeat']='route_leader_defeated'
        stage['rules']['attack_ranges']={'default_melee':[1,1],'default_bow':[1,3]}
        dump(output/'stages'/f'stage_{mid:03d}.json',stage)
        stages[str(mid)]={'id':mid,'path':f'res://data/stages/stage_{mid:03d}.json','name_ja':nameja,'name_zh':namezh,
                         'width':m['width'],'height':m['height'],'source':m['source'],'chapter':chapter,'route':route,
                         'enemy_group_ids':enemy_groups,'enemy_count':len(enemies),'world_node':mid if mid<=48 else None}
        stages[str(mid)]['enemy_assignment_confidence']=assignment
        stages[str(mid)]['random_enemy_group_ids']=cemetery_choices.get(mid,[])
    dgroups=src.db(8,'L08935B');dmaps=src.db(8,'L08939B')
    dungeon_encounters=[]
    for n,mid in enumerate(dmaps):
        gis=[gid for gid in dgroups[n*2:n*2+2] if gid!=255]
        dungeon_encounters.append({'trigger_index':n,'battle_map_id':mid,'enemy_group_ids':gis,
                                   'groups_valid':all(groups[str(g)]['valid'] for g in gis if str(g) in groups),
                                   'provenance':[src.ref(8,'L08935B'),src.ref(8,'L08939B'),src.ref(8,'L089D93')]})
    random_chapter=[]
    r=src.db(8,'L0892F7')
    for choice in range(5):
        random_chapter.append({'rng_choice':choice,'by_chapter':{str(ch+1):{'group_id':r[choice*8+ch*2],'world_node':r[choice*8+ch*2+1]} for ch in range(4)}})
    reinforcements=[]
    for i,label in enumerate(src.ptrs(8,'L08931F')):
        raw=src.db(8,label)
        reinforcements.append({'generator_index':i,'origin_hub_world_node':src.db(15,'L0FF11B')[i],
            'origin_battle_map_id':src.db(15,'L0FF124')[i],
            'waves':[{'group_id':raw[j],'probability_percent':raw[j+1]} for j in range(0,len(raw)-1,2)],'provenance':src.ref(8,label)})
    death_bytes=src.bytes_at(15,'L0FF18D',0xF20C-0xF18D)
    death_events=[]
    for j in range(0,len(death_bytes)-1,3):
        cid,action,param=death_bytes[j:j+3]
        item={'character_id':cid,'action_code':action,'parameter':param,'cpu_address':hex(0xF18D+j),
              'handler_label':{0:'L098C17',1:'L098C51',2:'L098C5C',3:'L098CAB',4:'L098CBB'}.get(action,'unknown')}
        if action==0:
            item.update({'action':'queue_world_army' if param&128 else 'set_reinforcement_state',
                         'generator_index':(param&127)//8,'generator_state':param&7})
        elif action==1:
            item.update({'action':'set_event_flag','flag_index':param})
        elif action==2:
            follow_label=src.ptrs(15,'L0FF20C')[param]
            follow=src.db(15,follow_label)
            item.update({'action':'dispatch_surviving_unit_battle_event','target_character_id':follow[0],
                         'set_flag_if_not_255':follow[1],'battle_event_id':follow[2]})
        elif action==3:
            item.update({'action':'set_world_branch_bits','bitmask':(param*64)&255})
        elif action==4:
            item.update({'action':'dispatch_battle_event','battle_event_id':param})
        death_events.append(item)
    special_maps=src.db(15,'L0FF150')[:-1]
    special_scripts=src.db(15,'L0FF15E')
    special_map_changes=src.db(15,'L0FF16B')
    catalog={'schema_version':1,'source_project':'https://github.com/minirop/fe2','source_commit':REVISION,'source_rom_sha1':ROM_SHA1,
        'characters':characters,'classes':classes,'enemy_groups':groups,'stages':stages,'world_nodes':world_nodes,
        'chapter_armies':chapter_armies,'routes':routes,'route_note':routes_note,
        'dungeon_encounters':dungeon_encounters,'chapter_random_armies':random_chapter,'reinforcement_generators':reinforcements,
        'character_death_events':death_events,
        'battle_opening_events':[{'map_id':mid,'event_index':n,'script_index':special_scripts[n],'map_change_index':special_map_changes[n]} for n,mid in enumerate(special_maps)],
        'chapters':[{'number':i+1,'title_ja':src.strings(12,['L0CB13D','L0CB146','L0CB152','L0CB15C','L0CB167'][i])[0].strip(),'title_zh':zh} for i,(ja,zh) in enumerate(CHAPTER_TITLES)],
        'coordinate_evidence':{'source_order':'x,y','old_extractor_bug':'Older first/second battle exporters reversed each deployment pair.',
            'proof':['ROM map header is height-1,width-1; L0FCD44 stores these to7440,7441.',
                     'L089E7C stores first position byte to unit17=x, second to unit16=y.',
                     'L08AC49 starts07,11: southern-outpost16x22 requires x7,y17, while x17 is out of bounds.'],
            'provenance':[src.ref(15,'L0FCD44'),src.ref(8,'L089E7C'),src.ref(8,'L08AC49')]},
        'data_anomalies':anomalies,
        'extraction_does_not_verify_runtime_behaviors':['World reinforcement movement and probabilistic spawning','Special event gates/cutscenes and NPC allegiance changes','Dungeon trigger routing, summons and Duma boss mechanics','Final scene, character endings and credits'],
        'counts':{'battle_map_indices':len(stages),'enemy_groups':len(groups),'valid_enemy_groups':sum(g['valid'] for g in groups.values()),'character_slots':len(characters),'world_nodes':len(world_nodes),'dungeon_encounter_triggers':len(dungeon_encounters)}}
    dump(output/'campaign.json',catalog)
    for mid,filename in [(1,'first_battle.json'),(2,'second_battle.json')]:
        old=json.loads((output/filename).read_text())
        generated=json.loads((output/'stages'/f'stage_{mid:03d}.json').read_text())
        old['player_positions']=generated['player_positions']
        old['enemy_positions']=generated['enemy_positions']
        assert len(old['enemies'])==len(generated['enemies'])
        for enemy,new in zip(old['enemies'],generated['enemies']):
            enemy['position']=new['position']
            enemy['resistance']=new['resistance']
            enemy['character_id']=new['character_id']
            enemy['name_id']=new['name_id']
        for key,char in old['characters'].items():
            char.update({'resistance':characters[key]['resistance'],'character_id':characters[key]['character_id']})
        old['coordinate_order']=generated['coordinate_order']
        old['coordinate_correction']=catalog['coordinate_evidence']
        old['legacy_save_note']='Existing in-progress save positions must be retained; corrected source coordinates apply when starting a new battle.'
        dump(output/filename,old)
    return catalog


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,default=Path('/private/tmp/fe2-analysis-20261012'))
    ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    args=ap.parse_args()
    catalog=extract(CatalogSource(args.source),args.output)
    print(json.dumps({'counts':catalog['counts'],'anomalies':catalog['data_anomalies'],'invalid_groups':{k:g['issues'] for k,g in catalog['enemy_groups'].items() if not g['valid']}},ensure_ascii=False))


if __name__=='__main__':
    main()
