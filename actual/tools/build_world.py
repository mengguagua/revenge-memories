#!/usr/bin/env python3
"""Extract generated art without hand redrawing; assemble authored map layers."""
from pathlib import Path
from collections import deque
import json, math, subprocess, html
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MAGICK = '/opt/homebrew/bin/magick'
PLAN = json.loads((ROOT.parent / 'docs2/规划索引.json').read_text())
SIZE = (1176, 1344)

# Scene positions follow the new shorelines; source grid coordinates stay recorded.
POS = {
 'W01':(216,1160), 'W02':(305,998), 'W03':(176,835), 'W04':(435,909),
 'W05':(410,793), 'W06':(539,697), 'W07':(398,578), 'W08':(576,540),
 'W09':(593,489), 'W10':(313,428), 'W11':(235,367), 'W12':(360,321),
 'W13':(427,220), 'W14':(522,173), 'W15':(574,158), 'W16':(660,100),
 'E01':(972,1220), 'E02':(834,1134), 'E03':(762,1030), 'E04':(906,955),
 'E05':(1085,848), 'E06':(1028,688), 'E07':(806,800), 'E08':(774,614),
 'E09':(783,469), 'E10':(973,584), 'E11':(1043,488), 'E12':(921,380),
 'E13':(937,277), 'E14':(834,179), 'S01':(148,1027), 'S02':(427,1008),
 'S03':(717,1205), 'S04':(1095,1044), 'S05':(454,640), 'S06':(1082,602),
 'S07':(118,470), 'S08':(814,348), 'S09':(1043,163),
}
ART = {
 'W01':'snow_village','W02':'forest_camp','W03':'granary','W04':'prison',
 'W05':'military_camp','W06':'harbor','W07':'military_camp','W08':'coastal_fort',
 'W09':'forest_camp','W10':'snow_village','W11':'snow_gate','W12':'sun_tower',
 'W13':'capital','W14':'causeway','W15':'sanctuary','W16':'sun_palace',
 'E01':'island_village','E02':'cutter','E03':'galleon','E04':'island_village',
 'E05':'lighthouse','E06':'coastal_fort','E07':'causeway','E08':'forest_camp',
 'E09':'granary','E10':'oasis','E11':'observatory','E12':'marsh_hut',
 'E13':'sanctuary','E14':'library','S01':'mine','S02':'clinic','S03':'cutter',
 'S04':None,'S05':'prison','S06':'military_camp','S07':'bell_village',
 'S08':'marsh_hut','S09':'library',
}
DESC = {
 'W01':'胡纳普从兄长的墓前出发。雪谷与林路之间，是第一章的故乡。',
 'W02':'押送兵正在追赶流民。先送他们走，村民的支持由这次救援开始。',
 'W03':'科兰扣留赈灾粮。夺回粮站，救出芙拉，再把粮食送回村庄。',
 'W04':'蕾娜因拒绝交出流民家庭而被囚禁。营救她，也救出被押送的居民。',
 'W05':'通往旧塔堡的外营。教团的援兵在此加入，首先保护被征调者。',
 'W06':'旧塔堡与凯旋广场所在的港城。复仇、庆典、重逢和两队脱围都发生在这里。',
 'W07':'军队输送原料和援兵的道路。截运会削弱神令对两地的控制。',
 'W08':'格曼与部下驻守的沿海石堡。投降后还需要交出记录，并留下作证。',
 'W09':'两队共同会谈的安全营站。双方取得战果后，在此交换停塔与地脉调查的消息。',
 'W10':'神令撤去庇护后，村民被困在雪峡。先护送居民走出封锁线。',
 'W11':'铁骑控制军路，并向群岛投送援军。夺取运输道路，减轻东线的压力。',
 'W12':'日塔仍在供给北境居民。先夺控制室，等待东线观测记录，再安全停用。',
 'W13':'赫兰带着曾经帮助胡纳普的人守城。双方都知道东群岛仍有人活着。',
 'W14':'第五章开放的登天通道。通过王都与东线战果解锁，不能从开篇自由前往。',
 'W15':'两队入口齐备并完成整备后合军。实际招募与存活的成员在此前庭汇合。',
 'W16':'太阳神乌库布·卡基亲自迎战。两地替代保护已经建立，众人不再接受他的安排。',
 'E01':'艾琳与学舍同伴出航的岛屿。港湾、航灯和引航者维系着群岛生活。',
 'E02':'潮狩军封锁航路。船团需要在礁区与巡逻舰之间找到通行的机会。',
 'E03':'被抓走的船员与工匠困在押送舰上。洛德帮助拆除囚禁设施。',
 'E04':'罗恩守着自己的渔船与岛民。登岸救援，不能征走全部渔船。',
 'E05':'希雅首先对海灯岛负责。保护航灯、安置居民后，她才决定远征。',
 'E06':'裴萨的潮狩军港。艾琳在此讨伐母亲的仇敌，取回薇娅的航图。',
 'E07':'断裂前留下的旧航路，可以穿过局部神幕，通往海峡城。',
 'E08':'盐地运输线连接被围的居民和设施。突破封锁，为后续调查打开道路。',
 'E09':'调查集中庇护的原料与设施。东线取得证据后，才能完成会合营站的共同会谈。',
 'E10':'沙城的水井不能随军放弃。保护居民与水源，建立继续北行的安全据点。',
 'E11':'萨弥准备销毁地脉调节记录。保护记录，向西队传回安全停塔的方法。',
 'E12':'被潮水侵蚀的沼泽通道。队伍要为仍留在岸边的人开出撤离道路。',
 'E13':'地脉修复的关键祭所。西线截断运输会减少援军，两队战果在此互相支持。',
 'E14':'祭所连接的神术通道。第五章从东侧进入日宫，与西队汇合。',
 'S01':'旧矿工与学徒贝克困在塌道后。工具和被押送者的遗物仍留在深处。',
 'S02':'赫维不肯离开病人。先送药、清道路，再邀请他同行。',
 'S03':'受伤渔民被拒绝靠岸。保护船只与居民，取得航路消息和有限物资。',
 'S04':'卡洛的旧同伴保存着失踪船员的遗物。护送他们面对家属，完成未尽的承诺。',
 'S05':'蕾娜过去保护的家庭再次被拘押。解救居民，面对旧部的选择。',
 'S06':'诺娅与弟弟受神军控制。营救之后仍需交代泄露船团位置的责任。',
 'S07':'村里保存着封路中的失踪名册。保护居民与记录，让投降者接受审查。',
 'S08':'赛琳守着无法步行撤离的病人。先安排他们的去处，再谈是否同行。',
 'S09':'旧书库保留太阳神最初救人的记录与试错。补充真实恩情，不提供唯一终结道具。',
}

# Hand-authored corridors follow valleys, the lake edge, harbor approaches and reefs.
MID = {
 'W01-W02':[(248,1114),(272,1054)], 'W02-W03':[(257,956),(223,895)],
 'W03-W04':[(264,857),(342,883)], 'W04-W05':[(454,869),(457,828)],
 'W05-W06':[(476,766),(510,734)], 'W06-W07':[(502,686),(453,682),(425,632)],
 'W07-W08':[(431,563),(491,563),(540,552)], 'W08-W09':[(593,518)],
 'W09-W10':[(546,474),(475,471),(402,454),(356,437)],
 'W10-W11':[(287,419),(265,392)], 'W11-W12':[(264,343),(309,336)],
 'W12-W13':[(374,295),(410,274)], 'W13-W14':[(471,215),(502,190)],
 'W14-W15':[(552,153),(558,159)], 'W15-W16':[(608,152),(648,127)],
 'E01-E02':[(939,1163),(884,1153)], 'E02-E03':[(791,1094)],
 'E03-E04':[(805,1003),(843,979)], 'E04-E05':[(958,937),(1018,924),(1067,883)],
 'E05-E06':[(1104,800),(1090,749),(1044,725)],
 'E06-E07':[(1003,746),(932,786),(858,807)],
 'E07-W06':[(743,801),(699,770),(651,740),(598,719)],
 'W06-E08':[(607,687),(669,674),(715,650)], 'E08-E09':[(752,572),(754,520)],
 'E09-W09':[(733,482),(677,487),(635,494)],
 'W09-E10':[(646,542),(699,576),(751,653),(820,672),(912,640)],
 'E10-E11':[(1007,554),(1023,518)], 'E11-E12':[(1009,447),(965,420)],
 'E12-E13':[(949,346),(962,318)], 'E13-E14':[(912,245),(869,214)],
 'E14-W15':[(777,160),(728,144),(674,137)],
 'W02-S01':[(251,1017),(200,1014)], 'W02-S02':[(358,996),(392,1006)],
 'E02-S03':[(786,1178)], 'E04-S04':[(975,1009),(1033,1033)],
 'W07-S05':[(420,606)], 'E08-S06':[(835,648),(912,632),(1030,624)],
 'W10-S07':[(255,447),(193,461)], 'E12-S08':[(871,366)],
 'E14-S09':[(902,175),(970,171)],
}

def run(*args):
 subprocess.run([MAGICK, *map(str,args)], check=True, capture_output=True)

def components(path):
 """Alpha component bounds avoid grid slicing through tall roofs or tower tips."""
 im=Image.open(path).convert('RGBA'); w,h=im.size
 mask=bytearray(a>64 for a in im.getchannel('A').getdata()); found=[]
 for j in range(w*h):
  if not mask[j]: continue
  q=deque([j]);mask[j]=0;count=0;box=[w,h,0,0]
  while q:
   p=q.popleft();x=p%w;y=p//w;count+=1
   box=[min(box[0],x),min(box[1],y),max(box[2],x+1),max(box[3],y+1)]
   for n in [p-1 if x else -1,p+1 if x<w-1 else -1,p-w if y else -1,p+w if y<h-1 else -1]:
    if n>=0 and mask[n]:mask[n]=0;q.append(n)
  if count>1500:found.append(box)
 return im.size,found

def extract(source,names,rows):
 (w,h),boxes=components(source)
 assert len(boxes)==len(names), (source,len(boxes))
 boxes.sort(key=lambda b:(min(rows-1,int((b[1]+b[3])/2/(h/rows))),b[0]))
 for name,b in zip(names,boxes):
  out=ROOT/'assets/landmarks'/f'{name}.png'
  size=96 if name in {'capital','harbor','sun_palace'} else 64
  x,y,xx,yy=b
  # Discard nearly transparent chromakey fringe; point sampling preserves clusters.
  run(source,'-channel','A','-threshold','25%','+channel','-crop',f'{xx-x}x{yy-y}+{x}+{y}',
      '+repage','-filter','point','-resize',f'{size-8}x{size-8}',
      '-gravity','center','-background','none','-extent',f'{size}x{size}',out)

def smooth(points):
 """Sample rounded corners; exported paths are shared by browser and Godot."""
 out=[points[0]]
 for i in range(1,len(points)-1):
  a,b,c=points[i-1:i+2]
  r=min(16,math.dist(a,b)*.3,math.dist(b,c)*.3)
  def near(p):
   d=math.dist(p,b);return [b[k]+(p[k]-b[k])*r/d for k in (0,1)]
  u,v=near(a),near(c);out.append(u)
  for t in [j/6 for j in range(1,7)]:
   out.append([(1-t)**2*u[k]+2*(1-t)*t*b[k]+t*t*v[k] for k in (0,1)])
 out.append(points[-1]);return [[round(v,2) for v in p] for p in out]

def main():
 extract(ROOT/'source/landmarks-generated.png',[
  'snow_village','forest_camp','granary','prison','military_camp','harbor','coastal_fort',
  'snow_gate','sun_tower','capital','cutter','galleon','oasis','observatory','sanctuary','sun_palace'],4)
 extract(ROOT/'source/supplement-generated.png',[
  'mine','clinic','bell_village','causeway','island_village','marsh_hut','library','lighthouse'],2)
 # Defined native map size, near identical aspect ratio; never stretch reusable art.
 run(ROOT/'source/terrain-generated.png','-filter','point','-resize','1176x1344',
     '-gravity','center','-background','#135475','-extent','1176x1344',ROOT/'assets/world/terrain.png')
 nodes=[]
 for n in PLAN['world']['nodes']:
  art=ART[n['id']]
  nodes.append({**{k:n[k] for k in ('id','name','region','kind','chapter')},
    'source_grid':[n['x'],n['y']], 'position':list(POS[n['id']]),
    'sprite':f'assets/landmarks/{art}.png' if art else '', 'description':DESC[n['id']]})
 edges=[]
 paths=[]
 for e in PLAN['world']['edges']:
  key=f"{e['a']}-{e['b']}";assert key in MID,key
  pts=smooth([POS[e['a']],*MID[key],POS[e['b']]])
  kind='sacred' if e['chapter']=='5' else ('side' if e['b'].startswith('S') else ('sea' if e['mode']!='陆路' else 'land'))
  edges.append({**{k:e[k] for k in ('a','b','mode','gate','chapter')},'style':kind,'points':pts})
  color={'land':'#e3be80','side':'#cab593','sea':'#b7e7e6','sacred':'#ffe3a0'}[kind]
  dash=' stroke-dasharray="3 9"' if kind in ('sea','side','sacred') else ''
  p=' '.join(f'{x},{y}' for x,y in pts)
  paths.append(f'<polyline points="{p}" fill="none" stroke="#133e44" stroke-width="6" opacity=".45" stroke-linecap="round" stroke-linejoin="round"/>')
  paths.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="3" opacity=".78" stroke-linecap="round" stroke-linejoin="round"{dash}/>')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1176" height="1344">{"".join(paths)}</svg>'
 (ROOT/'source/routes.svg').write_text(svg)
 # Draw authored route geometry directly. ImageMagick's native SVG renderer can
 # incorrectly fill open polylines; these paths intentionally have no fill.
 route_layer=Image.new('RGBA',SIZE)
 rd=ImageDraw.Draw(route_layer)
 for e in edges:
  pts=[tuple(p) for p in e['points']]
  rd.line(pts,fill=(11,51,58,110),width=6,joint='curve')
  color={'land':(227,190,128,215),'side':(202,181,147,185),
         'sea':(183,231,230,205),'sacred':(255,227,160,225)}[e['style']]
  if e['style']=='land':rd.line(pts,fill=color,width=3,joint='curve')
  else:
   distance=0
   for a,b in zip(pts,pts[1:]):
    length=math.dist(a,b)
    for j in range(max(1,int(length))):
     if int(distance+j)%12<3:
      t=j/max(length,1);x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
      rd.ellipse((x-1,y-1,x+1,y+1),fill=color)
    distance+=length
 route_layer.save(ROOT/'assets/world/routes.png',optimize=True)
 world={'schema':1,'campaign_id':'revenge_memories_rebuild','stage':'world_art_review',
  'native_size':list(SIZE),'terrain':'assets/world/terrain.png','routes':'assets/world/routes.png',
  'nodes':nodes,'edges':edges,'source_design':'../docs2/规划索引.json',
  'note':'美术审阅地图。章筛选用于查看设计，不代表已实现战役解锁或战斗。'}
 (ROOT/'data/world_map.json').write_text(json.dumps(world,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'data/world_map.js').write_text('window.WORLD_MAP = '+json.dumps(world,ensure_ascii=False)+';\n')
 # Reusable terrain, routes and landmark files stay separate; image is an export.
 cmd=[str(ROOT/'assets/world/terrain.png')]
 for n in nodes:
  if not n['sprite']:continue
  p=ROOT/n['sprite'];w,h=Image.open(p).size;x,y=n['position']
  cmd += ['(',str(p),')','-geometry',f'+{x-w//2}+{y-h+10}','-compose','over','-composite']
 run(*cmd,ROOT/'assets/world/world-geography.png')
 run(ROOT/'assets/world/terrain.png',ROOT/'assets/world/routes.png','-compose','over','-composite',
     *cmd[1:],ROOT/'assets/world/world-routes.png')
 # Lossless WebP copies have exactly identical pixels; all PNG masters retained.
 for name in ('terrain','world-geography','world-routes'):
  run(ROOT/f'assets/world/{name}.png','-define','webp:lossless=true',ROOT/f'assets/world/{name}.webp')
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',
                 *map(str,(ROOT/'assets').rglob('*.png'))],check=True,capture_output=True)
 report=[]
 for p in sorted((ROOT/'assets').rglob('*')):
  if p.suffix not in ('.png','.webp'):continue
  im=Image.open(p);sz=p.stat().st_size
  report.append({'path':str(p.relative_to(ROOT)),'purpose':'世界地图固定比例专用背景' if p.parent.name=='world' else '世界地点独立图标',
   'pixels':list(im.size),'bytes':sz,'alpha':im.mode=='RGBA',
   'quality_note':'保留复杂地形与细小像素轮廓；不降低地图分辨率追求参考体积。' if sz>=200000 else ''})
 (ROOT/'reports/asset-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'nodes':len(nodes),'edges':len(edges),'landmark_types':24,'assets':len(report)},ensure_ascii=False))

if __name__=='__main__':main()
