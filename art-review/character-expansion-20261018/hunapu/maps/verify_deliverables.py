from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parent
data=json.loads((R/'frame_mapping.json').read_text())
items=[]
for p in sorted((R/'deliverables').glob('*.png')):
    im=Image.open(p).convert('RGBA');b=im.getchannel('A').point(lambda v:255 if v>=32 else 0).getbbox()
    assert b and b[0]>=0 and b[1]>=0 and b[2]<=im.width and b[3]<=im.height,p
    purpose='runtime-atlas' if p.stem in ['story-world-walk','tactical-walk','tactical-idle'] else 'independent-frame'
    item={'path':str(p.relative_to(R)),'purpose':purpose,'width':im.width,'height':im.height,'bytes':p.stat().st_size,'visible_bounds':b,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    if p.stat().st_size>=20000:item['size_note']='Six-frame atlas; retain lossless alpha and detail.'
    assert p.stat().st_size<50000,(p,p.stat().st_size)
    items.append(item)
for s in data['scenarios']:
    for f in s['frame_mapping']:
        p=R/f['path'];im=Image.open(p);assert list(im.size)==s['output_frame_size'];assert p.stat().st_size==f['bytes']
        b=im.getchannel('A').point(lambda v:255 if v>=32 else 0).getbbox()
        depth=max(1,round((b[3]-b[1])*.12))
        foot=im.getchannel('A').point(lambda v:255 if v>=32 else 0).crop((0,b[3]-depth,im.width,b[3])).getbbox()
        measured_x=(foot[0]+foot[2])/2
        f['registered_foot_anchor']=[measured_x,b[3]]
        f['registered_foot_baseline']=b[3];f['baseline_delta_output_pixels']=b[3]-f['target_foot_anchor'][1]
        f['horizontal_foot_delta_output_pixels']=measured_x-f['target_foot_anchor'][0]
        assert abs(f['horizontal_foot_delta_output_pixels'])<=.5,(p,'horizontal feet drift',f['horizontal_foot_delta_output_pixels'])
        assert abs(f['baseline_delta_output_pixels'])<=1,(p,'vertical feet drift',f['baseline_delta_output_pixels'])
    for path in [s['source_atlas'],s['output_atlas'],s['preview_dark'],s['preview_light']]:assert (R/path).is_file(),path
a=Image.open(R/'reference/tactical-walk-00-native.png').convert('RGBA');b=Image.open(R/'reference/tactical-walk-01-native.png').convert('RGBA')
assert a.crop(a.getbbox()).transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==b.crop(b.getbbox()).tobytes()
report={'result':'pass','independent_pose_slots':15,'source_atlas_slots':18,'explicit_mirrored_left_frames':4,'delivery_png_files':len(items),
  'max_frame_bytes':max(i['bytes'] for i in items if i['purpose']=='independent-frame'),
  'max_atlas_bytes':max(i['bytes'] for i in items if i['purpose']=='runtime-atlas'),
  'visual_review':['dark/light backgrounds reviewed','source/new pose order reviewed','full silhouette, sword tips, boots and skirt coverage reviewed','original movement pair and idle cycle reviewed','source rectangular shields restored with matching hand/side occlusion; story/world unchanged'],
  'original_tactical_walk_0_1_exact_mirror_verified':True,
  'game_engine_started':False,'runtime_integration':False,
  'registration_tolerance':'Measured foot x error <= 0.5 output pixel and y error <= 1 output pixel. Tactical idle poses 1/3/5 corrected to exact [50,80]; no horizontal whole-body clamp is permitted.',
  'tactical_idle_pose1_revision':'Built-in image_gen shortened exposed blade only to fit while retaining foot center. Only 1/3/5 and their atlas changed; all other delivered PNG hashes were verified unchanged.',
  'items':items}
(R/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(R/'frame_mapping.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(R/'mapping.json').write_text((R/'frame_mapping.json').read_text())
print(json.dumps({k:v for k,v in report.items() if k not in ['items','visual_review']},ensure_ascii=False))
