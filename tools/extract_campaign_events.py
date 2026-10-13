#!/usr/bin/env python3
"""Recover original battle text and verified campaign-event contracts."""
import json
import re
from pathlib import Path
from extract_campaign import CatalogSource, dump, REVISION

ROOT=Path(__file__).resolve().parents[1]
SRC=Path('/private/tmp/fe2-analysis-20261012')


def battle_pages(src,label):
    mapping={bytes.fromhex(k):v for k,v in [line.rstrip('\n').split('=',1) for line in (SRC/'jp.tbl').read_text().splitlines() if '=' in line]}
    keys=sorted(mapping,key=len,reverse=True)
    raw=src.db(7,label)
    pages=[];text='';speaker=0;face=0;i=4;controls=[]
    def flush():
        nonlocal text
        if text.strip():
            pages.append({'speaker_id':speaker or face,'face_id':face,'text_ja':text.strip(),'source_label':label})
        text=''
    while i<len(raw):
        op=raw[i];i+=1
        if op==0xef:flush();break
        if op in (0xe6,0xee):flush();continue
        if op==0xed:text+='\n';continue
        if op==0xea:
            if text and not text.endswith('\n'):text+='\n'
            continue
        if op==0xe8:
            flush();face=raw[i+2];i+=3
            if not speaker:speaker=face
            continue
        if op==0xf0:flush();speaker=raw[i];i+=1;continue
        if op in (0xe9,0xdf,0xe1):
            controls.append({'opcode':op,'value':raw[i]});i+=1;continue
        if op==0xf1:continue
        candidate=bytes(raw[i-1:i+3])
        key=next((k for k in keys if candidate.startswith(k)),None)
        if key:
            text+=mapping[key];i+=len(key)-1
        else:
            raise ValueError((label,hex(op),i-1))
    return {'pages':pages,'raw':raw,'controls':controls,'source':src.ref(7,label)}


def text_pages(src,bank,label,speaker):
    pages=[];text=[];newline_run=0
    for line in src.block(bank,label).splitlines()[1:]:
        line=line.strip()
        if line.startswith('.STRINGMAP'):
            if newline_run>1 and text:
                pages.append({'speaker_id':speaker,'face_id':speaker,'text_ja':'\n'.join(text),'source_label':label});text=[]
            text.append(json.loads(line.split(',',1)[1].strip()));newline_run=0
        elif line=='NEWLINE':newline_run+=1
        elif line in ('WAIT_CLICK','PAGE') and text:
            pages.append({'speaker_id':speaker,'face_id':speaker,'text_ja':'\n'.join(text),'source_label':label});text=[]
    if text:pages.append({'speaker_id':speaker,'face_id':speaker,'text_ja':'\n'.join(text),'source_label':label})
    return {'pages':pages,'source':src.ref(bank,label)}


def main():
    src=CatalogSource(SRC)
    dialogs={str(i):battle_pages(src,label) for i,label in enumerate(src.ptrs(7,'L07AE70'))}
    quote_labels=src.ptrs(1,'L01B8A0')
    death_quotes={str(i):text_pages(src,1,label,i-13 if i<48 else 0) for i,label in enumerate(quote_labels) if i>=14}
    dump(ROOT/'data/battle_event_dialogues.json',{'source_revision':REVISION,'events':dialogs,'death_quotes':death_quotes})
    catalog=json.loads((ROOT/'data/campaign.json').read_text())
    hubs=json.loads((ROOT/'data/hubs.json').read_text())
    ref=lambda bank,label:src.ref(bank,label)
    events={
      'desert_choice':{
        'route':'celica','chapter':3,
        'branches':[
          {'defeat_character_id':136,'defeat_map_id':22,'set_event_flag':28,'set_world_branch_bits':128,
           'surviving_group_id':23,'retire_group_to_world_node':61,'recruit_character_id':25,'recruit_key':'sonya','hub_script_id':25},
          {'defeat_character_id':157,'defeat_map_id':23,'set_event_flag':29,'set_world_branch_bits':64,
           'surviving_group_id':22,'retire_group_to_world_node':61,'recruit_character_id':26,'recruit_key':'deen','hub_script_id':24}],
        'behavior_zh':'击败迪恩后索妮娅撤往吉斯要塞并可招募；击败索妮娅后迪恩可招募。撤退者不算死亡，不获得击杀经验。另一侧道路仍可通行，但不再生成原首领军。',
        'recruitment':'Only at liberated Grieth stronghold through the original survivor dialogue; never recruit both through this branch.',
        'sources':[ref(9,'L098CAB'),ref(7,'L07A47C'),ref(7,'L07A478'),ref(13,'L0DB795'),ref(13,'L0DB79F')]},
      'tatiana_zeke':{
        'map_id':34,'required_enemy_groups':[34,35],'required_event_flag':31,
        'source_bit':{'address':'6DB2','mask':1},
        'flag_set_by':{'hub_id':23,'hub_script_id':43,'recruit_character_id':30},
        'friendly_group_id':34,'hostile_group_id':35,'friendly_side':'npc',
        'npc_name_id_map':{'139':39,'196':40,'183':41,'180':42},'npc_ai_flags_or':4,
        'deployment_groups_after_conversion':{'enemy_layout_0':35,'npc_layout_1':34},
        'player_controlled_on_conversion':False,
        'recruitment':{'hub_id':21,'hub_script_id':45,'character_id':34,'key':'zeke','requires_surviving_zeke':True},
        'behavior_zh':'救出并招募蒂塔后，吉克军在利盖尔平原改为自动行动的盟军，战后前往利盖尔村招募吉克。原判定使用持久旗帜，不额外要求蒂塔当前存活。',
        'sources':[ref(7,'L079F7D'),ref(8,'L08A14F'),ref(8,'L08A29D'),ref(8,'L08A2B7'),ref(8,'L08A2BB'),ref(13,'L0DB88C'),ref(13,'L0DB8A2')]},
      'delthea_rescue':{
        'map_id':32,'controller_character_id':143,'captive_enemy_character_id':145,
        'when':'controller_dies_and_captive_is_alive','battle_event_id':12,
        'effects':[{'type':'remove_enemy_without_death','character_id':145},
                   {'type':'mark_rescued','character_key':'delthea'}],
        'captive_dies_instead':{'event_flag':34,'recruitment_allowed':False},
        'recruitment':{'hub_id':19,'hub_script_id':29,'character_id':29,'key':'delthea','requires_rescued':True},
        'behavior_zh':'先击败塔塔拉且迪尔德仍存活，播放恢复神智对白并让她离开敌阵；她不计为被杀，不掉落戒指，不给击杀经验。水门据点对话后加入。',
        'sources':[ref(9,'L098C5C'),ref(15,'L0FF21F'),ref(6,'L069E48'),ref(6,'L069E82'),ref(13,'L0DB7C7')]},
      'zofia_body_double':{
        'map_id':7,'real_desaix_character_id':129,'body_double_character_id':155,'slayde_character_id':147,
        'branches':[{'defeated':147,'surviving_target':155,'battle_event_id':1},
                    {'defeated':155,'surviving_target':147,'battle_event_id':10}],
        'effect':'Remove every surviving enemy record matching target character ID as retreat, not as a kill.',
        'behavior_zh':'斯雷达倒下时多哲替身撤退；主动击倒替身会触发斯雷达承认替身并撤退。真正的多哲ID129仍在第三章。',
        'sources':[ref(9,'L098C5C'),ref(15,'L0FF216'),ref(15,'L0FF219'),ref(6,'L069E82')]},
      'pirate_leader_retreat':{
        'map_id':11,'defeated_character_id':150,'surviving_target_character_id':190,'battle_event_id':11,
        'effect':'Remove surviving matching brigands without EXP or loot; other enemy classes remain.',
        'sources':[ref(15,'L0FF21C'),ref(6,'L069E67')]},
      'rudolf':{
        'map_id':42,'character_id':133,'alm_character_id':1,
        'combat':'Rudolf does not attack Alm in melee; apply Rules.attack_blocked.',
        'death_quote_index':53,
        'death_effects':[{'type':'battle_victory','reason':'commander_defeated'},
                        {'type':'retire_remaining_enemy_armies','award_kill_exp':False,'award_items':False}],
        'victory_requires_defeating_every_enemy':False,
        'next':{'world_node':78,'hub_id':30,'hub_script_id':53},
        'behavior_zh':'鲁道夫战死即结束战斗，剩余军队投降；遗言揭示阿尔姆身世。进利盖尔城与麦森交谈，麦森加入后进入地下终章。',
        'sources':[ref(9,'L098D25'),ref(6,'L069F2F'),ref(6,'L06B706'),ref(1,'L01BDC4'),ref(13,'L0DB902')]},
      'jedah':{
        'character_id':134,'vulnerable_turn_modulus':4,'vulnerable_turn_remainder':0,
        'rule_api':'Rules.boss_guard(unit, turn)',
        'behavior_zh':'朱达仅在第4、8、12等回合能受到普通命中；这按回合计数，不是累计攻击次数。',
        'sources':[ref(9,'L098D25')]},
      'dragon_valley':{
        'world_node':36,'generator_index':6,'origin_hub_world_node':79,
        'group_progression':[73,74,75,76,77,78],'probabilities_percent':[100,100,100,50,30,10],
        'force_generator_while_gate_bit_5_set':True,
        'release':{'when':'celica_enters_altar_alone_after_jedah_special_5','battle_map_id':62,
                   'required_story_phase':3,'required_player_party_count':1,'required_party':'celica',
                   'clear_world_gate_bits':33,'set_global_story_bit':{'address':'6E5C','mask':128},'activate_route':'alm'},
        'behavior_zh':'龙谷军由独立生成器逐步加强。赛莉卡接受朱达条件并独自抵达祭坛时，原流程切回阿尔姆，同时解除龙谷两端封锁及强制龙群生成。不能以击败一队龙群永久代替这个剧情条件。',
        'sources':[ref(8,'L089F4A'),ref(8,'L089349'),ref(6,'L068DFB'),ref(13,'L0D9633')]},
      'falchion':{
        'item_id':17,'name_zh':'法尔西昂','hub_id':40,'treasure_position':[7,2],
        'approach_positions':[[7,3],[8,3]],'hub_script_id':52,
        'script_effects':[{'special_id':7,'action':'show_captive_celica_scene'},
                          {'special_id':6,'action':'snapshot_celica_party_hp'}],
        'take_treasure':'Grant item17 through existing inventory/treasure flow; do not grant it merely for entering final chapter.',
        'sources':[ref(13,'L0DB8F5'),ref(13,'L0D96CC'),ref(13,'L0D9751')]},
      'final_merge':{
        'battle_map_id':62,'enemy_group_ids':[86],'hub_script_id':55,'special_id':8,
        'required_state':'Celica is held at altar (story_phase3), Alm reaches final entrance after the underground route.',
        'effects':[{'type':'merge_for_battle_only','party_order':['celica','alm'],'keep_rosters_separate':True},
                   {'type':'set_story_phase','value':4}],
        'deployment':{'celica_layout_index':0,'alm_layout_index':1,'max_per_route':10,'retain_user_party_order':True},
        'opening_battle_event_id':14,
        'celica_hp':'Use the captive party HP snapshot from special6 when source party state is4; other living entries use normal deployment healing.',
        'behavior_zh':'最终战两支队伍各部署最多10人，赛莉卡使用第一玩家队形、阿尔姆使用第二玩家队形。合流后可共同作战，但不能将两队名单互相覆盖。',
        'sources':[ref(13,'L0DB91E'),ref(13,'L0D9698'),ref(6,'L068BD5'),ref(6,'L068DA3'),ref(8,'L08BB73')]},
      'duma_ending':{
        'battle_map_id':62,'character_id':167,'class_id':21,'initial_hp':182,
        'final_phase_hp_below':52,'allowed_final_phase_weapon_ids':[17,42],
        'when':'duma_true_hp_reaches_zero','priority':'after_Alm_and_Celica_survival_check',
        'requires_killing_other_enemies':False,
        'effects':[{'type':'stop_battle_inputs_and_enemy_ai'},{'type':'persist_campaign_complete'},
                   {'type':'show_final_scene'},{'type':'show_character_endings','preserve_death_and_relationship_flags':True},
                   {'type':'show_credits'}],
        'behavior_zh':'多玛倒下即进入结局，不能继续要求清光杂兵；保留全部角色的生死与关系状态用于分支尾声。',
        'sources':[ref(9,'L098D58'),ref(9,'L098D06'),ref(5,'L058519'),ref(5,'L0583D8')]},
      'victory_experience':{
        'when':'ordinary_victory_or_Rudolf_commander_victory','base_enemy_exp_value':20,
        'formula':'ceil(class_coefficient * level_coefficient * 20 / 100), easy_mode doubles then cap100',
        'eligible':'living deployed player units; exclude AI flag4 NPCs and level20 units',
        'result_exp':'min(99, current_exp + award)','can_level_up':False,
        'sources':[ref(6,'L06B74B'),ref(9,'L098B74')]}}
    npcs=[]
    for mid,table,characters in [(29,'L0FF17E',[19]),(19,'L0FF181',[32,31]),(11,'L0FF186',[18,17,21])]:
        stage=json.loads((ROOT/'data/stages'/f'stage_{mid:03d}.json').read_text())
        layout=stage['deployment']['layouts'][0]
        addr=int(layout['label'][-4:],16)+1+layout['capacity']*2
        ps=src.bytes_at(8,f'L08{addr:04X}',len(characters)*2)
        records=src.bytes_at(15,table,len(characters)*2)
        for i,cid in enumerate(characters):
            assert records[i*2]==cid
            npcs.append({'map_id':mid,'character_id':cid,'position':ps[i*2:i*2+2],'side':'npc','ai_flags':records[i*2+1],
                         'player_controlled':False,'only_first_visit_opening_event':True,
                         'death_is_persistent':True,'sources':[ref(6,'L068B48'),ref(15,table)]})
    transitions={
      '1':{'trigger_hub_script':16,'from_chapter':1,'to_display_chapter':2,'source_chapter_counter':2,'destination_hub':5,
           'active_route':'celica','freeze_routes':['alm'],'initial_new_route_party':['celica'],
           'world_gate_and_mask':251,'world_gate_or_mask':0,'initialize_chapter_armies':2,'source':ref(12,'L0CABD3')},
      '2':{'trigger_hub_script':19,'from_chapter':2,'to_display_chapter':3,'source_chapter_counter':3,'destination_hub':44,
           'active_route':'alm','unfreeze_routes':['alm','celica'],'route_world_nodes':{'alm':16,'celica':18},
           'world_gate_and_mask':239,'world_gate_or_mask':4,'initialize_chapter_armies':3,
           'feature_state_updates':[{'hub_id':9,'index':0,'consumed':False},{'hub_id':9,'index':1,'consumed':True}],
           'feature_state_source':'L0CAC05: $6E08=($6E08&254)|2; feature bits at $6E00+hub_id-1',
           'source':ref(12,'L0CAC05')},
      '3':{'trigger_hub_script':38,'from_chapter':3,'to_display_chapter':4,'source_chapter_counter':4,'destination_hub':19,
           'requires_hub_trigger_enabled_by_event_flag':48,'flag48_set_by_hub_script':36,
           'active_route':'alm','world_gate_and_mask':4,'world_gate_or_mask':0,'initialize_chapter_armies':4,
           'feature_state_updates':[{'hub_id':15,'index':0,'consumed':True}],
           'feature_state_source':'L0CAC4B: $6E0E|=1; hub15 sluice pattern',
           'source':ref(12,'L0CAC4B')},
      '4':{'trigger_hub_script':53,'from_chapter':4,'to_display_chapter':5,'source_chapter_counter':4,'destination_hub':30,
           'recruit_character_id':3,'active_route':'alm','initialize_chapter_armies':None,'preserve_other_route_progress':True,
           'source':ref(12,'L0CAC6A')}}
    gate_a=src.db(7,'L078A2B');gate_b=src.db(7,'L078A33')[:8]
    out={'schema_version':1,'source_revision':REVISION,'events':events,'battle_allied_npcs':npcs,
      'chapter_transitions':transitions,'world_blocked_edge_bits':[{'bit':i,'mask':1<<i,'edge':[a,b]} for i,(a,b) in enumerate(zip(gate_a,gate_b))],
      'initial_world_gate_bits':22,'deployment_sort':{'field':'enemy_groups[group_id].deployment_priority','swap_two_groups_if':'first_priority >= second_priority','source':ref(7,'L079F39')},
      'army_movement_paths':[src.db(15,label)[:-1] for label in src.ptrs(15,'L0FE360')],
      'queued_world_armies':[{'queue_bit':i//2,'group_id':raw[i+1],'origin_world_node':raw[i]} for raw in [src.db(8,'L08927B')[:4]] for i in range(0,len(raw),2)],
      'chapter_armies':catalog['chapter_armies'],'reinforcement_generators':catalog['reinforcement_generators'],
      'battle_opening_events':catalog['battle_opening_events'],'character_death_events':catalog['character_death_events'],
      'transit_battlefields':{'map_ids':[16,18,35,46],'fixed_armies':[],
          'behavior':'No fixed army is created by chapter tables. A moving army chooses this terrain only when colliding with the player.'},
      'event_flag_indexing':'One-based: event_flag N applies hubs.flag_updates[N-1] via L0FFACC.',
      'remaining_runtime_parity_limits':['Exact original world AI tie breaking and schedule/frame RNG coupling','Frame-exact cinematic movement and timing','Original malformed enemy group66 is retained but not instantiated'],
      'source_contract_note':'Pure data contracts, not a claim that every native consumer or visual sequence is implemented.'}
    dump(ROOT/'data/campaign_events.json',out)
    print(json.dumps({'battle_events':len(dialogs),'battle_pages':sum(len(x['pages']) for x in dialogs.values()),
                      'death_quotes':len(death_quotes),'death_pages':sum(len(x['pages']) for x in death_quotes.values()),'campaign_event_contracts':len(events)}))


if __name__=='__main__':main()
