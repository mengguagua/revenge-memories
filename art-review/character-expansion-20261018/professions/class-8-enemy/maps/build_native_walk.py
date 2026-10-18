"""Package ImageGen art against verified tactical CPU8-slot source. No painting."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json,hashlib,shutil,subprocess
P=Path(__file__).parent; ROOT=P.parents[2]
overlay=json.loads((ROOT/'source-input/corrected-tactical-walk/overlay.json').read_text())
source=overlay['records']['class-8-enemy'];assert overlay['source_audit']['status']=='verified_native_tactical'
verification=json.loads((ROOT/'source-input/corrected-tactical-walk/verification.json').read_text());assert verification['passed']
if not(P/'source/previous-map-frame_mapping.json').exists():shutil.copy2(P/'frame_mapping.json',P/'source/previous-map-frame_mapping.json')
configs=[
 (0,'up',1,[0,0,887,887],[92,92],[350,780,500,870],[56,96],[44,84,68,96]),
 (1,'up',1,[887,0,1774,887],[92,92],[400,780,530,880],[70,96],[60,84,80,96]),
 (2,'right',3,[0,0,887,887],[94,94],[520,785,680,850],[74,96],[60,84,88,96]),
 (3,'right',4,[887,0,1774,887],[94,94],[140,780,290,860],[42,96],[32,84,52,96]),
 (4,'down',1,[0,0,887,887],[88,88],[600,810,730,880],[74,96],[60,84,88,96]),
 (5,'down',1,[887,0,1774,887],[88,88],[175,810,325,880],[50,96],[36,84,64,96]),
 (6,'left',1,[0,0,887,887],[81,81],[600,810,740,880],[86,96],[76,84,96,96]),
 (7,'left',1,[887,0,1774,887],[81,81],[260,800,450,880],[58,96],[44,84,72,96]),
]
def mask(im,t=128):return im.getchannel('A').point(lambda x:255 if x>=t else 0)
def bounds(im,roi,t=128):
 b=mask(im.crop(tuple(roi)),t).getbbox()
 if b is None:raise ValueError(roi)
 return [b[0]+roi[0],b[1]+roi[1],b[2]+roi[0],b[3]+roi[1]]
def info(p):return {'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
images={};reg=[]
for n,group,version,crop,size,rawroi,target,source_roi in configs:
 fn=f'source/tactical-{group}-generated-v{version}.png';raw=Image.open(P/fn).convert('RGBA').crop(tuple(crop))
 assert abs(size[0]/raw.width-size[1]/raw.height)<1e-9
 scale=size[0]/raw.width;a=raw.resize(tuple(size),Image.Resampling.NEAREST)
 rb=bounds(raw,rawroi);roi=[round(rawroi[0]*scale),round((rb[3]-18)*scale),round(rawroi[2]*scale),min(a.height,round((rb[3]+3)*scale))]
 b=bounds(a,roi);cx=(b[0]+b[2])/2
 # Grounded boot ROI excludes the visible spear and raised foot.
 visiblebottom=bounds(a,[round(v*scale) for v in rawroi],5)[3]
 xy=[round(target[0]-cx),target[1]-visiblebottom]
 out=Image.new('RGBA',(128,96));out.alpha_composite(a,tuple(xy))
 clipped=[v for k,v in enumerate(a.getchannel('A').getdata()) if v and not(0<=k%a.width+xy[0]<128 and 0<=k//a.width+xy[1]<96)]
 assert max(clipped,default=0)<=4,(n,'visible clipping',max(clipped))
 out.putdata([(0,0,0,0) if v[3]==0 else v for v in out.getdata()]);images[n]=out
 out.save(P/f'tactical-native-frames/frame-{n:03}.png')
 rec={'source_slot':n,'generated_source':fn,'prompt':f'source/tactical-{group}-prompt-v{version}.txt','generated_cell':crop,'uniform_scale':scale,'filter':'Nearest','raw_boot_roi':rawroi,'source_visible_boot_roi':source_roi,'generated_sole_roi_after_scale':roi,'generated_sole_bounds':b,'target_visible_boot_anchor':target,'registered_visible_boot_anchor':[cx+xy[0],visiblebottom+xy[1]],'selected_boot_opaque_bottom':b[3]+xy[1],'registration_offset':xy,'clipped_visible_alpha_gt4_pixels':0,'cropped_near_transparent_alpha_pixels':len(clipped),'maximum_cropped_alpha':max(clipped,default=0),'whole_frame_mirror_x':False,'registration_basis':'Original displayed native slot and manually isolated visible boot/leg endpoint. Actor anchor is separate. X usesalpha>=128; Y uses complete visiblealpha>4 sole, excluding distantalpha1 noise. No alpha threshold applied to retained pixels.'}
 reg.append(rec)
atlas=Image.new('RGBA',(1024,96))
for n in range(8):atlas.alpha_composite(images[n],(128*n,0))
atlas.save(P/'frames/tactical-native-walk.png')
subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',*map(str,(P/'tactical-native-frames').glob('*.png')),str(P/'frames/tactical-native-walk.png')],check=True)
records=[]
for n in range(8):
 r=next(r for r in reg if r['source_slot']==n);row=source['frame_mapping'][n];fn=f'tactical-native-frames/frame-{n:03}.png'
 records.append({'source_index':n,'source_slot':n,'source_frame':n,'output_index':n,'path':fn,'output_path':fn,'direction':row['direction'],'phase':row['phase'],'source_frame_index':row['source_frame_index'],'source_frame_address':row['source_frame_address'],'source_global_flip_already_applied':row['source_global_flip'],'generated_source':r['generated_source'],'prompt':r['prompt'],'registration_record':'source/tactical-native-registration.json','uniform_scale':r['uniform_scale'],'registration_offset':r['registration_offset'],'registered_boot_anchor':r['registered_visible_boot_anchor'],'whole_frame_mirror_x':r['whole_frame_mirror_x'],'derived_from':r.get('derived_from'),'clipped_visible_alpha_gt4_pixels':0,'maximum_cropped_alpha':r['maximum_cropped_alpha'],'compression':'oxipng -o3 lossless',**info(P/fn)})
source_audit={'status':'verified_native_tactical','overlay':'../../../source-input/corrected-tactical-walk/overlay.json','verification':'../../../source-input/corrected-tactical-walk/verification.json','entry':overlay['entry'],'caller':overlay['caller'],'chr':source['source_chr'],'native_actor_origin':source['native_actor_origin'],'anchor_note':source['anchor_note'],'source_rom_sha256':overlay['source_rom_sha256'],'cpu_oam_matches':verification['independent_rom_table_decoder_matches'],'old_source_rejected':'Historical CHR26+village OAM hybrid has no exact source matches and is not used for new art.','art_review_status':'parent_visual_review_passed'}
scenario={'id':'tactical-walk','class_id':8,'original_class_id':8,'source_side':'enemy','character_id':'enemy-mercenary','display_name':'敌方佣兵','source_atlas':'../../../source-input/corrected-tactical-walk/class-8-enemy.png','source_frame_size':[32,24],'source_anchor':[16,24],'output_frame_size':[128,96],'output_anchor':[64,96],'logical_render_scale':.25,'source_frame_count':8,'canonical_count':8,'redraw_count':8,'source_alias_to_canonical':list(range(8)),'exact_mirror_aliases':source['exact_mirror_aliases'],'frame_mapping':records,'output_atlas':'frames/tactical-native-walk.png','output_atlas_bytes':(P/'frames/tactical-native-walk.png').stat().st_size,'directions':source['directions'],'direction_mirror_x':{},'default_facing':'native-rendered-per-slot','static_facing':False,'timing':source['timing'],'idle':{'kind':'hold-current-direction-first-frame','directions':{k:[v[0]] for k,v in source['directions'].items()}},'source_audit':source_audit,'adaptation_note':'Eight distinct native CHR26 slots each independently ImageGen drawn. Up blade appears on viewer right; right/down/left each retain viewer-left blade, hence no mirrored derivatives. Upper-left sleeve/coat obscures the free hand in the original up view; head-side pale points are not inferred fists. No additional direction flips.','preview_dark':'previews/tactical-native-walk-dark.gif','preview_light':'previews/tactical-native-walk-light.gif'}
mapping=json.loads((P/'frame_mapping.json').read_text());mapping['scenarios']=[scenario]+[s for s in mapping['scenarios'] if s['id']!='tactical-walk'];mapping['status']='complete_art_review_ready';mapping['tactical_walk_status']='Corrected verified native CHR26 source; eight independently drawn ImageGen poses, no mirrors. Old hybrid references historical only.';mapping['qa']={
 'native_walk_review':'previews/tactical-native-original-dark-light.png',
 'native_walk_registration':'source/tactical-native-registration.json',
 'static_idle_review':'previews/all-map-original-dark-light.png',
 'identity':'Approved ash/taupe short hair, moss-green fitted high-collar jacket, diagonal strap, one iron shoulder, short ivory-trim hip hems, charcoal trousers, calf wraps, brown boots, one steel sword.',
 'source_correction':'Old village OAM plus fixedCHR26 atlas is historical. Current tactical source is verified bank011 CPU output with correct class/side tables; same CHR number does not imply same OAM.',
 'orientation':'Eight CPU slots already include native directional flips. None are exact full-canvas mirror pairs; eight poses drawn independently. Sword is viewer-right for up, viewer-left for right/down/left.',
 'alpha_policy':'Retained pixels keep ImageGen alpha. Grounded boot ROI excludes weapon. X uses opaque sole alpha>=128; Y visible sole alpha>4. Only outside-canvas noise alpha<=4 may be cropped.',
 'limits':['No exact new clothing-edge/source-pixel claim.','Up head-side pale points are ears/face edges supported by paired placement and unchanged upper body; no high free fist invented.','Down sword tip is around4outputpx above native hair-top, accepted shape residual.','Right2/3 head/chest is corrected to near-front based on original eye/nose/jaw layout; left6/7 retains left nose silhouette. Grounded2 leg gathered and grounded3 back leg extended independently by ImageGen.'],
 'checks':['8 frames load at128x96','8 separate ImageGen poses no mirrored legs','boot XY registered','dark/light alpha inspection','battle/static idle unchanged','raw prompts and failed versions retained'],
 'max_frame_bytes':max(r['bytes'] for r in records)
}
for fn in ['frame_mapping.json','mapping.json']:(P/fn).write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
(P/'source/tactical-native-registration.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
qa=json.loads((P/'qa-summary.json').read_text());qa['status']=mapping['status'];qa['qa']=mapping['qa'];qa['sizes']=[x for x in qa['sizes'] if x['purpose']!='tactical-walk']+[{'path':r['path'],'purpose':'tactical-walk','pixels':r['size'],'bytes':r['bytes']} for r in records];(P/'qa-summary.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
board=Image.new('RGB',(2048,648));draw=ImageDraw.Draw(board)
for row,bg in enumerate([(230,225,216),(35,40,48),(230,225,216)]):
 draw.rectangle((0,row*216,2048,(row+1)*216),fill=bg)
 for n in range(8):
  a=Image.open(P/f'reference/tactical-native-{n:02}.png').convert('RGBA').resize((128,96),Image.Resampling.NEAREST) if row==0 else images[n]
  a=a.resize((256,192),Image.Resampling.NEAREST);board.paste(a,(n*256,row*216+24),a);draw.text((n*256+6,row*216+6),f'{n} '+source['frame_mapping'][n]['direction']+' '+['original','new dark','new light'][row],fill='white' if row==1 else 'black')
board.save(P/'previews/tactical-native-original-dark-light.png',optimize=True)
small=Image.new('RGB',(1024,192))
for row,bg in enumerate([(35,40,48),(230,225,216)]):
 small.paste(bg,(0,row*96,1024,(row+1)*96))
 for n in range(8):small.paste(images[n],(128*n,row*96),images[n])
small.save(P/'previews/tactical-native-actual-size-dark-light.png')
for tone,bg in [('dark',(35,40,48)),('light',(230,225,216))]:
 ims=[]
 for phase in [0,1]:
  canvas=Image.new('RGB',(1024,192),bg)
  for col,direction in enumerate(['up','right','down','left']):
   n=source['directions'][direction][phase];a=images[n].resize((256,192),Image.Resampling.NEAREST);canvas.paste(a,(col*256,0),a)
  ims.append(canvas)
 ims[0].save(P/f'previews/tactical-native-walk-{tone}.gif',save_all=True,append_images=ims[1:],duration=[266,266],loop=0,disposal=2)
print(json.dumps(reg,ensure_ascii=False));print('native walk8frames',min(r['bytes'] for r in records),max(r['bytes'] for r in records))
