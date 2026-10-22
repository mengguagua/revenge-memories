#!/usr/bin/env python3
"""Evidence-led chapter-five west spatial corrections; frozen baseline input."""
from pathlib import Path
from PIL import Image
import json,copy,hashlib,shutil,subprocess,importlib.util,math
from PIL import ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022';BASE=O/'baseline';ART=R/'assets/chapter5-spatial-20261022/west';SRC=R/'source/chapter5-spatial-20261022'
ART.mkdir(parents=True,exist_ok=True);SRC.mkdir(parents=True,exist_ok=True);(SRC/'.gdignore').touch()
source=Path('/Users/gcc/.codex/generated_images/01a16289-048c-77d3-b870-3bc293412331/exec-98993b28-f46a-4a5f-b727-18386f197784.png')
if not(SRC/'infirmary-cutaway-original.png').exists():shutil.copy2(source,SRC/'infirmary-cutaway-original.png')
im=Image.open(SRC/'infirmary-cutaway-original.png').convert('RGBA');box=im.getbbox();sprite=im.crop(box);sprite.thumbnail((96,96),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(96,96));canvas.alpha_composite(sprite,((96-sprite.width)//2,96-sprite.height));canvas.save(ART/'infirmary-cutaway.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(ART/'infirmary-cutaway.png')],check=True)
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
plan=json.loads((R.parent/'docs2/规划索引.json').read_text());plans={b['id']:b for b in plan['battles']}
reports=[]
for c in ['M51','M52']:
 old=json.loads((BASE/f'{c}.json').read_text());d=copy.deepcopy(old);w=d['map']['width'];g=[list(row)for row in d['logic_grid']];ground=[list(row)for row in d['visual_ground']];changes=[]
 def tile(x,y,ch,value):g[y][x]=ch;d['map']['tiles'][y*w+x]=value
 if c=='M51':
  for origin,patient in [([5,11],'royal_wounded0'),([22,11],'royal_wounded1')]:
   x,y=origin;module=next(m for m in d['art_modules']if m['name']=='infirmary'and m['origin']==origin)
   prop=next(p for p in d['art_props']if p['path']=='res://assets/chapter5/infirmary.png'and p['position']==[x*16,y*16]);prop['path']='res://assets/chapter5-spatial-20261022/west/infirmary-cutaway.png'
   blocked=[];walking=[]
   for dy in range(6):
    for dx in range(6):
     walk=(dx in[2,3]and 1<=dy<=4)or(dx==3 and dy==5)
     tile(x+dx,y+dy,'='if walk else'#',208 if walk else 196);ground[y+dy][x+dx]='='
     d['art_layers'][0][y+dy][x+dx]=old['art_layers'][0][18][8]
     (walking if walk else blocked).append([x+dx,y+dy])
   module.update(name='infirmary_cutaway',cells=blocked,walkable_cells=walking,purpose='剖面病房：北/侧墙与床位阻挡；病人门内候位，唯一南门贯通救护横廊')
   npc=next(n for n in d['npc_units']if n['id']==patient);before=npc['position'];npc['position']=[x+3,y+4]
   changes.append({'id':patient,'before':before,'after':npc['position'],'door':[x+3,y+5],'first_outdoor_cell':[x+3,y+6],'approach_unchanged':[x+3,y+7],'walkable_cells':walking})
  d['tactical_notes']=['北殿与两侧医舍围成室外王都内廷；两间医舍以剖面展示病床和室内候位，屋外庭院、院墙与后撤路的层级清楚。','两组伤兵起初在病房内等待，接应确认后须先经过各自唯一南门，再沿横廊汇入中轴；床位、侧墙与北墙都不可穿行。','两病房南面操作格与南侧后撤路不变。先压住东侧守军再放行更安全；两病房均须确认、至少一组撤离及第4回合来援规则保持。']
  diagnosis='王都内廷为室外，屋顶建筑本身并非错误；旧伤兵站在医舍外，无法呈现从病房南门被接出。以同占地剖面病房与真实南门修复。'
 else:
  # A four-cell margin on each side creates genuine thick rocky abutments.
  # The entire old battlefield is translated by +4x without stretching spans.
  shift=4;oldw=w;w=oldw+shift*2;h=d['map']['height']
  prior_g=g;prior_ground=ground;g=[list('~'*w)for _ in range(h)];ground=[list('~'*w)for _ in range(h)]
  oldlayers=d['art_layers'];d['art_layers']=[[[28+(x+y)%4 if z==0 else None for x in range(w)]for y in range(h)]for z in range(3)]
  tiles=[96]*(w*h)
  for yy in range(h):
   for xx in range(oldw):
    g[yy][xx+shift]=prior_g[yy][xx];ground[yy][xx+shift]=prior_ground[yy][xx];tiles[yy*w+xx+shift]=old['map']['tiles'][yy*oldw+xx]
    for z in range(3):d['art_layers'][z][yy][xx+shift]=oldlayers[z][yy][xx]
  d['map']={'width':w,'height':h,'tiles':tiles}
  d['player_positions']=[[x+shift,y]for x,y in old['player_positions']]
  for group in ['enemies','npc_units','reinforcements','objects']:
   for u in d[group]:
    u['position'][0]+=shift
    for k in ['approach','burn_target']:
     if k in u:u[k][0]+=shift
    for k in ['approaches','opens','open_art_cells']:
     for v in u.get(k,[]):v[0]+=shift
  d['targets']=[[x+shift,y]for x,y in old['targets']];d['exit']=[old['exit'][0]+shift,old['exit'][1]]
  for prop in d['art_props']+d.get('natural_props',[]):prop['position'][0]+=shift*16
  for m in d['art_modules']:
   m['origin'][0]+=shift
   for v in m['cells']:v[0]+=shift
  for route in d.get('tactical_routes',[]):
   for v in route.get('waypoints',[]):v[0]+=shift
  d['nature_layout']['excluded']=[[0,0,w*16,h*16]]
  sp=importlib.util.spec_from_file_location('native_coast',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(sp);sp.loader.exec_module(L);L.ART=ART
  atlas=L.Atlas();im=Image.open(R/old['art_atlas'].removeprefix('res://')).convert('RGBA');meta=json.loads((R/old['art_atlas'].removeprefix('res://')).with_suffix('.json').read_text())
  atlas.cells=[im.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))for i in range(meta['tile_count'])];atlas.original=len(atlas.cells);atlas.add={};atlas.shores={}
  coast=set();left=[(0,0),(7,0),(7,2),(5,5),(5,9),(4,13),(6,18),(9,21),(8,25),(0,25)];right=[(w-1-x,y)for x,y in left]
  for polygon in [left,right]:
   mask=Image.new('1',(w,h));ImageDraw.Draw(mask).polygon(polygon,fill=1)
   for yy in range(h):
    for xx in range(w):
     if mask.getpixel((xx,yy))and g[yy][xx]=='~':coast.add((xx,yy))
  # Whole native outcrops sit inside each continuous bank, never as loose islands.
  for x,y in [(0,1),(2,20),(w-4,1),(w-4,22)]:
   cells=[]
   for yy in range(y,y+4):
    for xx in range(x,x+4):
     assert g[yy][xx]=='~',(xx,yy,g[yy][xx]);coast.add((xx,yy));cells.append([xx,yy])
   d['art_props'].append({'path':'res://assets/battlefield-0.3.0/modules/sea_cliff.png','position':[x*16,y*16]})
   d['art_modules'].append({'name':'bridgehead_shore_foundation','origin':[x,y],'footprint':[4,4],'cells':cells,'logic':'^','runtime_prop':True,'purpose':'完整海崖嵌入宽厚连续岩岸，与既有桥头相接'})
  L.B.PACK['base']['bedrock']=[52,53,54,55]
  for xx,yy in coast:tile(xx,yy,'^',94);ground[yy][xx]='c'
  for xx,yy in coast:
   mask=L.B.mask_at(ground,xx,yy,lambda q:q!='~');edge=any(0<=xx+dx<w and 0<=yy+dy<h and ground[yy+dy][xx+dx]=='~' for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]);d['art_layers'][0][yy][xx]=atlas.edge('bedrock'if edge else'cave','sea',mask,(xx+yy)%4)
  for yy,row in enumerate(ground):
   for xx,ch in enumerate(row):
    if ch not in 'b=':continue
    mat='cobble'if ch=='b'else'stone';mask=L.B.mask_at(ground,xx,yy,lambda q:q in 'b=c')
    d['art_layers'][0][yy][xx]=atlas.edge(mat,'sea',mask,(xx+yy)%4)
  atlas.save();d['art_atlas']='res://assets/chapter5-spatial-20261022/west/terrain.png'
  t=d['terrain'];a=t['tile_categories']['94'];b=t['tile_categories']['96'];assert t['avoid_by_category'][a]==t['avoid_by_category'][b]
  assert all(v[a]==v[b]for v in t['movement_by_class_and_category'].values())
  changes=[{'kind':'rigid_translation','offset':[shift,0],'size_before':[oldw,h],'size_after':[w,h],'all_anchors_and_spans_translated_equally':True},{'kind':'thick_rocky_banks','polygons':[left,right],'rock_cells':len(coast),'walking_routes_added':False}]
  d['tactical_notes']=['登天桥处于室外水域，三段石桥由两处承台支撑；东西两岸有完整宽厚岩基，桥头直接接岸，桥面没有悬空断口。','三个桥锁从西到东位于各段东侧落脚处，以可通行控制标记表示；桥面与承台连续，护栏在三格净通行带外，原先后确认规则保持。','承台南侧支台供整队，飞行者可越水绕侧但不能代替桥锁确认。露天桥面采用风化砌石、承台采用较粗石铺；整图仅横向增加两岸并整体平移，桥跨度、敌我相对距离、移动与回避规则保持。']
  diagnosis='原规划明确室外三段桥；无室内屋顶或假门。旧全水背景与窄岩条无法给桥头提供可信岸基，本次左右各加4列，将整个旧战场整体平移4格，在新增空间形成宽厚连续岩岸，不改变三段桥长度、宽度与战斗相对距离。'
 d['logic_grid']=[''.join(row)for row in g];d['visual_ground']=[''.join(row)for row in ground];d['visual_notes']=d['tactical_notes'].copy();d['tactical_review_version']='0.10.10-spatial';d['art_style_version']='chapter5-spatial-20261022';d['landscape_revision']='Original-story spatial audit: visible ward interior and actual shore-supported bridgeheads'
 for k in ['before','during','after','goal','reinforcement_turn']:assert d[k]==old[k],(c,k)
 if c=='M51':
  for k in ['enemies','reinforcements','player_positions','objects','targets','exit']:assert d[k]==old[k],(c,k)
 else:
  for group in ['enemies','reinforcements','objects']:
   for a,b in zip(old[group],d[group]):
    assert b['position']==[a['position'][0]+4,a['position'][1]]
    assert {k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}
  assert d['player_positions']==[[x+4,y]for x,y in old['player_positions']]
 assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(old['npc_units'],d['npc_units']))
 write(R/f'data/stages/{c}.json',d)
 b=plans[c];reports.append({'code':c,'name':b['name'],'original_story_evidence':{k:b[k]for k in ['style','goal','cause','before','during','after','object_semantics','ai_and_timing']},'evidence_source':'docs2/规划索引.json (not prior redesign notes); unchanged stage dialogue and chapter5_rules.gd before_lines/interact','diagnosis':diagnosis,'repairs':changes,'size':[w,d['map']['height']],'gameplay_fields_preserved':True,'sha256':hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest(),'prior_sha256':hashlib.sha256((BASE/f'{c}.json').read_bytes()).hexdigest()})
write(O/'west-spatial-audit.json',{'status':'implemented, native verification pending','scope':'M51/M52 only; evidence from original planning/dialogue, no core/shared/animation changes','maps':reports,'asset':{'source':'actual/source/chapter5-spatial-20261022/infirmary-cutaway-original.png','runtime':'actual/assets/chapter5-spatial-20261022/west/infirmary-cutaway.png','size':[96,96],'bytes':(ART/'infirmary-cutaway.png').stat().st_size,'method':'built-in imagegen with existing infirmary palette reference; alpha-preserving aspect fit, lossless PNG','opaque_source_bbox':box,'source_size':list(im.size)}})
print(json.dumps([{'code':m['code'],'sha256':m['sha256']}for m in reports]))
