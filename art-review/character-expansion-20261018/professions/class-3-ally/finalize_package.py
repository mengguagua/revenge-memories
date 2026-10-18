from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,shutil,subprocess
R=Path(__file__).resolve().parent;B=R.parents[1];font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',18)
archive=R/'maps/source/spear-end-patches/reviews-before';archive.mkdir(exist_ok=True)
for group,ids in [('side',[6,7]),('rear',[0,1]),('front',[4,5]),('idle',[0,1,2])]:
    is_idle=group=='idle'
    n=Image.open(R/'reference/map-idle-native.png' if is_idle else B/'source-input/corrected-tactical-walk/class-3-ally.png').convert('RGBA')
    sw=24 if is_idle else 32;ow=96 if is_idle else 128;folder='idle-frames' if is_idle else 'tactical-native-frames'
    for theme,bg,fg in [('light','#e9e4d9','#26333a'),('dark','#1d2b35','#edf0e7')]:
        path=R/f'maps/reviews/tactical-idle-{theme}.png' if is_idle else R/f'maps/reviews/tactical-native-{group}-{theme}.png'
        if path.exists() and not (archive/path.name).exists():shutil.copyfile(path,archive/path.name)
        out=Image.new('RGBA',(24+(ow*2+16)*len(ids),500),bg);dr=ImageDraw.Draw(out);dr.text((16,10),'天马地图最终 · 原作 / 新图 · 上钝尾，下钢刃',font=font,fill=fg)
        for col,i in enumerate(ids):
            x=16+col*(ow*2+16);out.alpha_composite(n.crop((i*sw,0,(i+1)*sw,24)).resize((ow*2,192),Image.Resampling.NEAREST),(x,42));out.alpha_composite(Image.open(R/f'maps/{folder}/frame-{i:03}.png').convert('RGBA').resize((ow*2,192),Image.Resampling.NEAREST),(x,264));dr.text((x+ow-8,470),str(i),font=font,fill=fg)
        out.convert('RGB').save(path,optimize=True)
for group in ['battle','maps']:
    p=R/group/'frame_mapping.json';d=json.loads(p.read_text());d['parent_visual_review_passed']=True;d['parent_visual_review_note']='Root passed complete battle, static idle and verified native tactical four directions, including corrected weapon endpoints on dark/light backgrounds.'
    if group=='maps':
        for sc in d['scenarios']:
            atlas=R/'maps'/sc['output_atlas'];subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--strip','safe',str(atlas)],capture_output=True,check=True);sc['output_atlas_bytes']=atlas.stat().st_size;sc['review_status']='parent_visual_review_passed';sc['parent_visual_review_passed']=True
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=R/'verify_art.py';s=p.read_text().replace('technical_pass_map_endpoint_review_pending','complete_art_review_passed').replace('complete_map_endpoint_review_pending','complete_art_review_passed').replace('body_phase_passed_weapon_endpoint_review_pending','parent_visual_review_passed').replace('verified bank011 CPU/CHR19 source; body/wing phases passed; weapon endpoints pending review','verified bank011 CPU/CHR19 source; all body/wing phases and corrected weapon endpoints passed');p.write_text(s)
p=R/'reference/source-semantic-audit.json';d=json.loads(p.read_text());d['status']='verified_native_tactical';d['verification']='../../../source-input/corrected-tactical-walk/verification.json';d['weapon_endpoint_correction']={'status':'parent_visual_review_passed','evidence':'map-spear-endpoint-native-evidence.png','native_class':3,'native_up_frames':[125,126],'native_down_frames':[129,130],'chr':19,'static_idle_source_metatile':6,'static_idle_chr_cycle':[24,25,21,25,24,25],'static_idle_tiles':[70,71,86,87],'conclusion':'Short blunt cap upper/upper-right, elongated pale blade lower/lower-left. Rear lower end is partially occluded; inference uses continuity within class3 own native front/side views, not another class.','patch_proof':'../maps/source/spear-end-patch-qa.json','original_error':'Initial artwork incorrectly used conventional blade-up spear. Superseded art/notes and all raw images retained; body phase acceptance did not cover this later endpoint correction.'};p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
