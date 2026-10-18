"""Publish only the male map review revision into the isolated comparison gallery."""
from pathlib import Path
from PIL import Image
import json,hashlib,subprocess,os

V=Path(__file__).resolve().parents[1];R=V.parent;M=R/'hunapu/maps'
mapping=json.loads((M/'frame_mapping.json').read_text())
before=json.loads((V/'reference/hunapu-mapping-before.json').read_text())
qa=json.loads((V/'fixed-layer-qa.json').read_text())
G='/opt/homebrew/bin/magick'
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def info(p):return {'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
specs={'story':('hunapu-story',[0,1,2,3,4,5]),'tactical-walk':('hunapu',list(range(8))),'tactical-idle':('hunapu',[8,9,10,9,8,9])}
notes={'story':'男主地图修订：4种主体色；头部与身体固定，仅四肢局部动画，地面阴影独立且固定。',
       'tactical-walk':'男主地图修订：4种主体色；头部、身体、剑与持剑手固定，仅腿脚、持盾手和盾变化；保留原生方向/时序。',
       'tactical-idle':'男主地图修订：4种主体色；待机各帧统一缩至约90%，可见高度64像素，与原作四倍高度一致，脚底基准不变。身体、腿脚及头部底图固定，仅双臂、剑、盾变化。'}
inventory=[]
for sc in mapping['scenarios']:
    if sc['id']not in specs:continue
    key,slots=specs[sc['id']];records=[]
    idle=sc['id']=='tactical-idle'
    folder='hunapu-idle-size2' if idle else key
    revision='hero-map-four-color-v2-idle-size2' if idle else 'hero-map-four-color-v2'
    for f,slot in enumerate(slots):
        p=V/'deliverables'/folder/f'frame-{slot:02}.png'
        subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(p)],capture_output=True,check=True)
        rel=os.path.relpath(p,M);records.append({'source_index':f,'source_frame':f,'path':rel,'output_path':rel,'revision':revision,'art_review_status':'awaiting_user_review','generated_sheet':os.path.relpath(V/'source'/f'{key}-four-color.png',M),'generated_slot':slot,'fixed_layer_contract':os.path.relpath(V/'layer-contract.json',M),**info(p)})
        inventory.append({'purpose':sc['id'],'frame':f,'path':str(p.relative_to(R)),**info(p)})
    atlas=V/'deliverables'/f'{sc["id"]}-atlas{"-size2" if idle else ""}.png';run(*[V/'deliverables'/folder/f'frame-{slot:02}.png'for slot in slots],'+append',atlas)
    subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(atlas)],capture_output=True,check=True)
    sc.update({'frame_mapping':records,'output_atlas':os.path.relpath(atlas,M),'output_atlas_bytes':atlas.stat().st_size,'revision':revision,'review_note':notes[sc['id']],'art_review_status':'awaiting_user_review','palette':['#172638','#3976B5','#E4E1C8','#DDA77D'],'preview_ground':str((V/'reference/native-map-ground.png').relative_to(R)),'ground_shadow':{'path':str((V/'reference/ground-shadow.png').relative_to(R)),'size':[14,2],'offset':[1 if sc['id']=='tactical-idle'else 0,0],'alpha':0.58,'kind':'separate_fixed_ground_layer','source':'Original Pegasus14x2 projected-ground bitmap reused; character artwork unchanged by this layer.'},'motion_review':str((V/('idle-size-qa.json' if idle else 'fixed-layer-qa.json')).relative_to(R))})
    inventory.append({'purpose':sc['id']+' atlas','path':str(atlas.relative_to(R)),**info(atlas)})
assert next(s for s in mapping['scenarios']if s['id']=='world')==next(s for s in before['scenarios']if s['id']=='world')
mapping['latest_map_revision']={'id':'hero-map-four-color-v2-idle-size2','status':'awaiting_user_review','scope':list(specs),'record':'../../map-motion-review-v2/README.md','world_profile_unchanged':True,'battle_scene_unchanged':True}
mapping['parent_visual_review_passed']=False
(M/'frame_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
(V/'image-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print('Published3 male map scenarios; world and all other actor mappings untouched.')
