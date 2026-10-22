#!/usr/bin/env python3
"""Evidence-led spatial corrections. Independent atlases; no shared art or rules edited."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageEnhance
import json,hashlib,copy,math,subprocess,importlib.util
spec=importlib.util.spec_from_file_location("native_masks",Path(__file__).resolve().parent/"redesign_ch1_camp_fort.py");N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022';BASE=O/'baseline';ART=R/'assets/chapter5-spatial-20261022/east-finale';ART.mkdir(parents=True,exist_ok=True)
CODES=['F51','F52','J53','J54'];IDS={'.':48,'a':48,'b':48,'=':208,'#':196,'^':94,'~':96,'f':172,'+':218,'s':191,'c':48}
PACK=json.loads((R/'assets/battle_tiles/battle-tiles.json').read_text());NATIVE=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA')
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def tile(im,i):return im.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))
class Atlas:
 def __init__(self,name,src):
  self.name=name;im=Image.open(R/src.removeprefix('res://')).convert('RGBA');self.cells=[im.crop((x,y,x+16,y+16))for y in range(0,im.height,16)for x in range(0,im.width,16)];self.add={};self.source=src
 def new(self,key,im):
  if key not in self.add:self.add[key]=len(self.cells);self.cells.append(im)
  return self.add[key]
 def native(self,i):return self.new('native:'+str(i),tile(NATIVE,i))
 def material(self,name,x,y,background=None,mask=255):
  im=Image.open(ART/(name+'.png')).convert('RGBA');part=im.crop((x%4*16,y%4*16,x%4*16+16,y%4*16+16))
  key=f'material:{name}:{x%4}:{y%4}:{background}:{mask}'
  if background is not None:
   under=self.cells[background].copy();part.putalpha(N.L.W.alpha_mask(mask));under.alpha_composite(part);part=under
  return self.new(key,part)
 def water(self,i,mask,material='courtyard-stone',x=0,y=0):
  key=f'water:{i}:{mask}:{material}:{x%4}:{y%4}'
  if key not in self.add:
   im=self.cells[i].copy();cap=Image.open(ART/(material+'.png')).convert('RGBA').crop((x%4*16,y%4*16,x%4*16+16,y%4*16+4))
   for edge in range(4):
    if not(mask&(1<<edge)):continue
    if edge==0:im.alpha_composite(cap,(0,0))
    elif edge==1:im.alpha_composite(cap.rotate(90,expand=True),(12,0))
    elif edge==2:im.alpha_composite(cap,(0,12))
    else:im.alpha_composite(cap.rotate(90,expand=True),(0,0))
   self.new(key,im)
  return self.add[key]
 def dark(self,v):
  im=tile(NATIVE,PACK['base']['cave'][v]);im=ImageEnhance.Brightness(im).enhance(.4);return self.new('cutaway-rock:'+str(v),im)
 def save(self):
  im=Image.new('RGBA',(512,math.ceil(len(self.cells)/32)*16))
  for i,t in enumerate(self.cells):im.paste(t,(i%32*16,i//32*16))
  p=ART/(self.name+'.png');im.save(p);subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(p)],check=True)
  return {'path':'res://'+str(p.relative_to(R)),'pixels':list(im.size),'bytes':p.stat().st_size,'source':self.source,'original_pixels_preserved':True,'new_tile_count':len(self.add)}
AT={}
def flood(g,p):
 w=len(g[0]);h=len(g);q=deque([tuple(p)]);seen={tuple(p)}
 while q:
  x,y=q.popleft()
  for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
   z=(x+dx,y+dy)
   if 0<z[0]<w-1 and 0<z[1]<h-1 and z not in seen and g[z[1]][z[0]]not in'#^~':seen.add(z);q.append(z)
 return seen
reports=[]
for code in CODES:
 old=json.loads((BASE/(code+'.json')).read_text());d=copy.deepcopy(old);g=[list(row)for row in d['logic_grid']];w=d['map']['width'];h=d['map']['height'];ground=[list(row)for row in d['visual_ground']];base=d['art_layers'][0];top=d['art_layers'][2];kind='east'if code.startswith('F')else'finale'
 if kind not in AT:AT[kind]=Atlas(kind,d['art_atlas'])
 A=AT[kind];notes=[];findings=[];changed=[]
 def change(x,y,ch,visual=None):
  g[y][x]=ch;ground[y][x]=visual or ch
 def wall(x,y,vertical=False):
  change(x,y,'#','b');base[y][x]=A.native(PACK['base']['cobble'][(x+y)%4]);top[y][x]=A.native(463 if vertical else 459);changed.append([x,y])
 def addmodule(name,cells,**kw):
  d['art_modules'].append({'name':name,'cells':cells,'logic':'#','runtime_prop':False,**kw})
 if code=='F51':
  m=next(m for m in d['art_modules']if m['name']=='muted_stair');m['walk_through_cells']=[[x,y]for y in range(1,5)for x in[24,25]];m['purpose']='地下主渠北端的上行楼梯；两格踏步可走，顶端内圈落脚接神术通道，不添加交互规则'
  for x,y in m['walk_through_cells']:change(x,y,'=');base[y][x]=A.native(PACK['base']['cobble'][(x+y)%4])
  # A short native down stair marks the actual south return route. It is floor.
  p=R/'assets/battle_tiles/modules/stairs_down.png';d['art_props'].append({'path':'res://assets/battle_tiles/modules/stairs_down.png','position':[5*16,27*16],'purpose':'通向上层祭所接应点的下行入口；既有返程坐标6,27不变'})
  d['art_modules'].append({'name':'south_return_stair','origin':[5,27],'footprint':[2,2],'cells':[[5,27],[6,27],[5,28],[6,28]],'logic':'inherits_ground','walk_through_cells':[[5,27],[6,27],[5,28],[6,28]],'runtime_prop':True})
  findings=['原北阶梯整幅为墙，踏步不可走；这与进入下一层的观感冲突。','原主渠为贯穿上下边界的人工水渠，水路本身连续；两岸设备与维修工班用途相符。']
  notes=['祭所底层是剖顶表现的地下水工层：两处装置、石砌工作间和贯通主渠保留；不摆屋顶房舍或室外树木。','北端楼梯中央两格为真实踏步，栏柱仍阻挡；南侧返回阶梯连接原接应口，战斗胜利仍按两处交接、各保护一回合和首领处理。','两座检修桥的两端都落在可走岸上；主渠边补石砌渠沿，区别于地表自然河流。']
 elif code=='F52':
  old_m=next(m for m in d['art_modules']if m['name']=='muted_palace');d['art_modules'].remove(old_m);d['art_props']=[p for p in d['art_props']if p['path']!='res://assets/chapter5/palace.png']
  # Cutaway floor, not a roofed house standing inside another building.
  for y in range(h):
   for x in range(w):
    inside=(2<=x<=33 and 2<=y<=25)or(3<=x<=30 and 26<=y<=28)
    if not inside and not(14<=x<=20 and 1<=y<=7):
     change(x,y,'#');base[y][x]=A.dark((x+y)%4);top[y][x]=None
    elif ground[y][x]=='a':base[y][x]=A.native(PACK['base']['cobble'][(x+y)%4]);ground[y][x]='c'
  for y in range(1,8):
   for x in range(14,21):
    change(x,y,'#','c');base[y][x]=A.native(PACK['base']['cobble'][(x+y)%4]);top[y][x]=None
  for y in range(3,8):
   for x in range(16,19):change(x,y,'b');base[y][x]=A.native(PACK['base']['cobble'][(x+y)%4])
  for x in[14,20]:
   for y in range(1,8):wall(x,y,True)
  for x in range(14,21):wall(x,1)
  d['art_props'].append({'path':'res://assets/chapter5/sun_gate.png','position':[15*16,1*16],'purpose':'日宫下层的北门厅门框，不是独栋屋顶宫殿；门洞内可走，战后前往前庭'})
  d['art_modules'].append({'name':'roofless_north_gate','origin':[15,1],'footprint':[5,6],'cells':[[x,y]for y in range(1,7)for x in range(15,20)],'logic':'mixed','walk_through_cells':[[x,y]for y in range(3,7)for x in range(16,19)],'runtime_prop':True,'purpose':'门框柱脚实体阻挡，中央门洞连接北通廊'})
  # South entrance connects to the shared lower-level antechamber, not salt ground.
  for x in range(3,31):
   for y in range(26,29):
    if g[y][x]=='a':ground[y][x]='c';base[y][x]=A.native(PACK['base']['cobble'][(x+y)%4])
  d['nature_layout']={'biome':'rock','props':[],'excluded':[[0,0,w*16,h*16]]};d['surroundings']='cave'
  findings=['北侧带完整屋顶的宫殿位图嵌在下层围墙/地板中，形成室内摆外屋的误读。','原外围用盐地材质且可绕院墙，日宫下层与旧书库/前庭之间的内部通道关系不清。']
  notes=['从祭所神术通道进入日宫下层门厅；采用剖顶石地板、完整外墙、北门框与两翼控制间，不再在室内摆独栋屋顶宫殿。','南端入口前室接原部署与返程口；北侧门洞通往前庭方向，门阵仍分别在各装置南面确认。','中央水池是室内蓄水庭，石沿围合；两格石桥接两端地板，侧廊可回转。两门阵与神官判定、所有单位及操作坐标保持。']
 elif code=='J53':
  m=next(m for m in d['art_modules']if m['name']=='stair');d['art_modules'].remove(m);d['art_props']=[p for p in d['art_props']if not(p['path']=='res://assets/chapter5/stair.png'and p['position']==[256,224])]
  rails=[]
  for y in range(14,18):
   for x in[16,19]:wall(x,y,True);rails.append([x,y])
   for x in[17,18]:base[y][x]=A.native(PACK['base']['cobble'][(x+y)%4]);ground[y][x]='b'
  addmodule('level_stone_bridge_parapets',rails,origin=[16,14],footprint=[4,4],purpose='同层人工池石桥；两格桥面、两侧完整护栏，替换只有单侧抬升的孤立高楼梯')
  findings=['前庭是室外，正殿屋顶和庭树有原始空间语义支持，保留。','中轴单向高楼梯原本跨平面水池，两端缺少高差解释；改同层石桥即可保留通路并消除矛盾。']
  notes=['两军从西南、东南庭道进入室外神宫前庭；北端正殿外观、两翼门阵与园林保留。','中轴跨池处改为同层双格石桥，护栏与原阻挡格一致；前庭不再凭一座孤立楼梯制造无法解释的高差。','水池补完整人工石沿；两军二十候选格、所有单位与交互坐标、地形通行成本完全不变。']
 else:
  ledge=[]
  for x in list(range(1,14))+list(range(18,33)):
   if x in[9,10,23,24]:continue
   wall(x,18);ledge.append([x,18])
  for y in[16,17]:
   for x in[13,18]:wall(x,y,True);ledge.append([x,y])
  for x in[13,14,17,18]:wall(x,16);ledge.append([x,16])
  addmodule('upper_terrace_retaining_face',ledge,origin=[1,16],footprint=[32,3],purpose='高台前沿连续石砌立面，中央阶口前凸、两翼阶口稍后；只能沿三座真实踏步跨越高差')
  findings=['原文本未规定神座必须封闭室内；露天神座与自然天空结局不冲突，不强行新增屋顶。','原高台没有连续挡墙，单位可绕草地走过阶梯旁，视觉高差与通行冲突。']
  notes=['神座采用露天台地而非室内草坪：北侧神座、上庭园林和中轴平台共同位于上层，下庭为联军进入与退守区。','在三座阶口之间补连续石砌挡墙；中央踏步与两翼踏步是真正跨层通路，不能再从旁边草地绕过高差。','人工池岸明确；首领与固定16,10召唤点、两军二十部署、两处恢复格以及全部单位坐标保持；半血一次强化/召唤和结局规则不变。']
 # Apply coherent authored 64px material fields in world-space, not random rotated
 # single cells, so slab direction and joins continue over every 16px tile split.
 for y in range(h):
  for x in range(w):
   q=ground[y][x]
   if code=='F52' and q in 'abc=':
    base[y][x]=A.material('palace-marble',x,y)
   elif code in ['J53','J54'] and q in 'b=':
    mat='palace-marble' if code=='J54' and y<=15 else 'courtyard-stone'
    mask=N.B.mask_at(ground,x,y,lambda z:z in 'b=~+#')
    # Existing native mask keeps original soft paving perimeter; underlying grass
    # is a complete native grass tile, never the old floor texture.
    base[y][x]=A.material(mat,x,y,A.native(PACK['base']['grass'][(x+y)%4]),mask)
 # Stone coping is inside water cells; it changes no walkable footprint or rules.
 for y in range(h):
  for x in range(w):
   if g[y][x]!='~':continue
   mask=0
   for k,(dx,dy)in enumerate([(0,-1),(1,0),(0,1),(-1,0)]):
    xx=x+dx;yy=y+dy
    if 0<=xx<w and 0<=yy<h and g[yy][xx] not in'~^#':mask|=1<<k
   if mask and code!='F51':base[y][x]=A.water(base[y][x],mask,'palace-marble'if code=='F52'else'courtyard-stone',x,y)
 d.update(logic_grid=[''.join(row)for row in g],visual_ground=[''.join(row)for row in ground],map={'width':w,'height':h,'tiles':[IDS[ch]for row in g for ch in row]},tactical_review_version='0.10.10-spatial',art_style_version='chapter5-spatial-20261022',tactical_notes=notes,visual_notes=notes)
 d['art_atlas']='res://assets/chapter5-spatial-20261022/east-finale/'+kind+'.png'
 if 'production_anchors'in d:d['production_anchors']['revision']='0.10.10-spatial'
 seen=flood(g,d['player_positions'][0]);anchors=d['player_positions']+[u['position']for u in d['enemies']+d['npc_units']+d['reinforcements']]+[d['exit']]+[o.get('approach',o['position'])for o in d['objects']]
 for p in anchors:assert tuple(p)in seen,(code,'blocked/disconnected anchor',p)
 for group in['enemies','npc_units','reinforcements','objects','player_positions','targets','exit','player_positions_by_route','terrain','goal','before','during','after','summon_template']:
  assert old.get(group)==d.get(group),(code,'contract/position changed',group)
 if code=='J53':assert old['map']==d['map'],('J53 actual navigation changed')
 if code=='J54':assert(16,10)in seen
 changes=[{'position':[x,y],'before':old['logic_grid'][y][x],'after':g[y][x]}for y in range(h)for x in range(w)if old['logic_grid'][y][x]!=g[y][x]]
 write(R/f'data/stages/{code}.json',d)
 reports.append({'code':code,'findings':findings,'actions':notes,'original_source_evidence':{'planning':'docs2/规划索引.json, id='+code,'style':{'F51':'shrine_depth','F52':'sun_lower','J53':'forecourt','J54':'god'}[code],'story':'docs2/完整故事剧情.md §八','dialogue':'docs2/完整台词汇总.md '+code,'before_quote':old['before'],'after_quote':old['after']},'interpretation_is_inference':code in['F52','J54'],'inference_note':{'F51':'底层/深入与上层岸上对白明确区分；按地下水工层表现。','F52':'原文只说下层，未逐字规定屋顶；结合由祭所神术通道进入、邻接旧书库、再到前庭，采用剖顶门厅是空间解释，不伪称为原文直述。','J53':'前庭本身是室外院落语义，正殿外立面合理。','J54':'原文没有规定封闭屋顶；保留既有露天神座，只修高差与通行的真实矛盾。'}[code],'runtime_changes':changes,'all_actor_deployment_object_and_exit_coordinates_unchanged':True,'all_stats_story_timing_rules_unchanged':True,'all_anchors_connected':True,'connected_cells':len(seen),'stage_sha256':hashlib.sha256((R/f'data/stages/{code}.json').read_bytes()).hexdigest()})
assets=[a.save()for a in AT.values()];write(O/'east-finale-spatial-audit.json',{'passed':True,'scope':'Four maps independently reviewed against pre-redesign dialogue, story and original planning. Previous tactical notes were not used as narrative evidence.','maps':reports,'assets':assets,'visual_review_pending':True,'material_generation':{'tool':'built-in image_gen','source_directory':'reports/chapter5-spatial-20261022/east-finale/source/','runtime_textures':['assets/chapter5-spatial-20261022/east-finale/palace-marble.png','assets/chapter5-spatial-20261022/east-finale/courtyard-stone.png'],'sampling':'Whole square uniformly reduced to64px then split16px without independent rotation or random offset; one global XY phase keeps slab seams coherent.','uses':{'F51':'Existing coarse underground stone / timber maintenance bridge, retained','F52':'Indoor pearl/ivory marble throughout the cutaway room and pool coping','J53':'Weathered outdoor limestone paving and same stone pool coping','J54':'Marble upper divine platform, weathered exterior limestone approach and matching pool edge/retaining face'}}});print(json.dumps([{'code':r['code'],'changed_cells':len(r['runtime_changes']),'sha256':r['stage_sha256']}for r in reports],ensure_ascii=False))
