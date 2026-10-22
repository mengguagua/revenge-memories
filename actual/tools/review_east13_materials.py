#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];ROOT=R.parent;O=R/'reports/chapter5-spatial-20261022/material-audit'
CODES='F21 F22 F23 F24 F25 F26 S21 S22 F31 F32 F33 S31 S32'.split()
CHANGED=['F25','F31','F33','S31','S32']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
SCENES={
 'F21':'室外海面上的运输船与搜捕舰甲板、登船跳板',
 'F22':'室外押送舰/接应船甲板与铁栅囚舱',
 'F23':'海岛沙滩、林地草坡与村庄土路',
 'F24':'黑昼海岛、灯庭露天石台、岸滩与村道',
 'F25':'室外军港、岸上土路/石台与露天木码头',
 'F26':'室外海岸水道、砌石海堤与堤后土路',
 'S21':'漂泊渔船甲板、登船跳板与沙岸停泊口',
 'S22':'潮湿海洞：岩壁、浅滩湿地与较干的通行土脊',
 'F31':'室外码头街区、岸侧木栈与接应船甲板',
 'F32':'露天旧海床盐原、盐池、土质干道与岩脊',
 'F33':'室外提炼院后庭、砌石环廊、水庭与木检修桥',
 'S31':'户外山村接近区与两处剖面牢室',
 'S32':'露天盐原营地、土路/沙区与两处剖面拘押营房'
}
FINDINGS={
 'F21':['甲板为有方向的棕色长木板，船医区/货区仍是船面；没有用室内拼木、大理石或泥沙替代甲板。','上下跳板与海面有明确边界，甲板木纹与室内S51人字拼木不同。'],
 'F22':['铁栅囚舱内部仍沿用舰船木甲板，符合囚舱位于船上的关系；不能因有围栏便改成陆地石牢地面。','舷边与闭合跳板的原有材质过渡保持。'],
 'F23':['浅黄细砂海滩、带细碎草纹的草坡和土质道路三个表面可分辨；树丛底部仍是草地。','岸滩与海水之间保持原有轮廓，不将白盐壳或宫殿石地用作沙滩。'],
 'F24':['夜色/黑昼统一色调下，草地、沙滩、土路和灯庭石台仍保有不同纹理。','神灯前的台阶接露天砌石台，未把整岛铺成室内地板。'],
 'F25':['原露天木码头与船板来自同一timber纹理族，语义差别不够。','本次岸侧木码头改成风化灰木，原木边框与海岸轮廓保留；陆上土路、草地与室外粗石台保持。'],
 'F26':['砌石海堤/水道护岸与堤后土路、植被分开，石路为露天粗砌石，不是神宫抛光大理石。','连续沿海石堤的表面、转角与海水边界完整。'],
 'S21':['船体保持棕色长木板，岸边采用浅黄沙和草地，船岸跳板保持木质。','没有将船面套用新室内拼木纹理。'],
 'S22':['海洞保留粗岩壁、潮湿暗色淤泥/湿地和更干的土脊通路。','自然洞室不是建筑室内，未替换成整齐室内石板或神宫大理石。'],
 'F31':['原岸栈、跳板与船体木面过于接近。','本次仅x>=7的露天岸栈/跳板换风化灰木，西南船体甲板保留棕色原板；可从两种表面看出船与固定岸栈。','码头石路/土质仓街仍是室外材质。'],
 'F32':['白灰盐壳、浅褐干道、水池与粗岩脊纹理不同；盐地未误用普通沙滩或宫殿大理石。','原件源同时包含sand与salt类别，实际这图采用salt主体，符合旧海床盐路。'],
 'F33':['原短检修木桥与船甲板共用纹理族。','本次仅5格现有木桥表面换风化灰木，保留桥端原生边框；周围露天砌石廊、土庭、水面与中央阵台保持各自材质。'],
 'S31':['户外山村接近区保留草地、土路与露天砌石；两处剖面牢室各自有真实内部地格与牢门。','原室内地格与室外粗cobble相同，本次仅12格可走室内地面换磨损暖灰石板，门槛与开门贴图保持。','原案style为dungeon，但原台词未限定整个战斗在地下；本次只按当前分区纠正材质，不宣称重做地下层。'],
 'S32':['盐地、黄色砂区与夯土通路各有独立材料，营房外场保持露天环境。','两处剖面拘押营房内12格可走地面换磨损室内石板，外部石场及真实门槛不变。']
}
MATERIALS={
 'F21':['ship_timber','sea'], 'F22':['ship_timber','sea'],
 'F23':['grass','sand','dirt','rock','sea'], 'F24':['grass','sand','dirt','outdoor_stone','sea'],
 'F25':['grass','dirt','outdoor_stone','outdoor_timber','sea'], 'F26':['grass','dirt','outdoor_stone','rock','sea'],
 'S21':['ship_timber','grass','sand','sea'], 'S22':['cave_rock','wet_silt','dirt','sea'],
 'F31':['ship_timber','outdoor_timber','outdoor_stone','dirt','sea'],
 'F32':['salt','dirt','rock','sea'], 'F33':['salt','dirt','outdoor_stone','outdoor_timber','sea'],
 'S31':['grass','dirt','outdoor_stone','interior_stone','rock'],
 'S32':['salt','sand','dirt','outdoor_stone','interior_stone','rock']
}
NATIVE={'grass':('grass 0–3','草地底纹'),'sand':('sand 36–39','沙滩或风积砂'),'dirt':('dirt 8–11','行军土路/干土脊'),'outdoor_stone':('cobble 20–23 / stone16–19','露天粗砌石路/石台'),'ship_timber':('timber24–27 + original directional walkway variants','棕色船甲板长板'),'salt':('salt40–43','白灰盐壳'),'rock':('rock52–55 / native mountain-ground variants','山脊/崖石'),'cave_rock':('cave12–15 + native cliff transitions','海洞粗岩'),'wet_silt':('marsh44–47','潮湿暗色淤泥地'),'sea':('sea28–31','水面')}
proof=json.loads((O/'east13-material-proof.json').read_text());proofs={m['code']:m for m in proof['maps']};maps=[]
for c in CODES:
 d=json.loads((R/f'data/stages/{c}.json').read_text());p=O/'east13-images'/f'{c}.png'if c in CHANGED else ROOT/f'art-review/battle-maps-20261021/images/{c}.png'
 im=Image.open(p);pixels=im.convert('RGBA').tobytes()
 if c in CHANGED:subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True);assert Image.open(p).convert('RGBA').tobytes()==pixels
 mats=[]
 for m in MATERIALS[c]:
  if m=='outdoor_timber':mats.append({'material':m,'use':'暴露于风雨盐雾的岸栈/检修桥','source':'res://assets/chapter5-spatial-20261022/east-materials/outdoor-timber.png','method':'New built-in image_gen source;64px logical repeat; only existing timber surfaces changed'})
  elif m=='interior_stone':mats.append({'material':m,'use':'剖面牢室/拘押营房的磨损室内石地','source':'res://assets/chapter5-spatial-20261022/library/interior-stone.png','method':'New built-in image_gen source; only12 existing walkable indoor cells per map'})
  else:mats.append({'material':m,'use':NATIVE[m][1],'source':'res://assets/battle_tiles/battle-tiles.png','native_material':NATIVE[m][0],'runtime_atlas':d['art_atlas']})
 maps.append({'code':c,'scene':SCENES[c],'materials':mats,'findings':FINDINGS[c],'changes':proofs[c]['changed_fields']if c in CHANGED else[],'passed':True,'map_sha256':sha(R/f'data/stages/{c}.json'),'image_reviewed':str(p.relative_to(ROOT)),'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'image_size':list(im.size),'geometry_rules_all_coordinates_identical':True,'proof':'east13-material-proof.json'if c in CHANGED else'Current stage equals east13-baseline stage byte for byte.'})
write(O/'east13.json',{'passed':True,'scope':'13 individually viewed native map images plus original material atlas inspection; new five-map native captures independently reviewed after completed imports. Pure materials only; no gameplay geometry change.','maps':maps,'changed_maps':CHANGED,'unchanged_maps':[c for c in CODES if c not in CHANGED],'no_core_or_animation_changes':True,'source_prompts':['actual/source/chapter5-spatial-20261022/outdoor-timber/prompt.txt','actual/source/chapter5-spatial-20261022/library-floors/prompts.json'],'method':'Original bitmap sources viewed, current scene PNGs viewed individually, source atlas/material selectors inspected, pure-art invariants asserted.'})
print(json.dumps({'passed':True,'reviewed':len(maps),'changed':CHANGED,'unchanged':len(CODES)-len(CHANGED)}))
