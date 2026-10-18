"""Static native idle only; old village/world movement is deliberately excluded."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,subprocess
P=Path(__file__).parent
raw=Image.open(P/'source/idle-generated-v1.png').convert('RGBA')
targets=[(62,80),(52,80),(42,80)]
rawrois=[(470,620,610,680),(270,620,650,680),(220,620,330,680)]
sourcerois=[[(56,68,68,80)],[(36,68,48,80),(56,68,68,80)],[(36,68,48,80)]]
selected=[];reg=[]
def mb(im):return im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()
def info(p):return {'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for i in range(3):
 cell=raw.crop((724*i,0,724*(i+1),724));a=cell.resize((82,82),Image.Resampling.NEAREST)
 roi=rawrois[i];q=cell.crop(roi);b=mb(q);b=[b[0]+roi[0],b[1]+roi[1],b[2]+roi[0],b[3]+roi[1]]
 rr=[round(roi[0]*82/724),round((b[3]-18)*82/724),round(roi[2]*82/724),min(82,round((b[3]+3)*82/724))]
 bb=mb(a.crop(tuple(rr)));bb=[bb[0]+rr[0],bb[1]+rr[1],bb[2]+rr[0],bb[3]+rr[1]]
 cx=(bb[0]+bb[2])/2
 # All generated idle sprites have the verified grounded hoof/hooves lowest.
 bottom=a.getchannel('A').point(lambda v:255 if v>4 else 0).getbbox()[3]
 xy=[round(targets[i][0]-cx),targets[i][1]-bottom]
 out=Image.new('RGBA',(96,96));out.alpha_composite(a,tuple(xy))
 assert sum(v>0 for v in a.getchannel('A').getdata())==sum(v>0 for v in out.getchannel('A').getdata())
 out.putdata([(0,0,0,0) if v[3]==0 else v for v in out.getdata()])
 out.save(P/f'source/idle-selected-{i:02}.png');selected.append(out)
 reg.append({'canonical_index':i,'generated_source':'source/idle-generated-v1.png','generated_cell':[724*i,0,724,724],'uniform_scale':82/724,'filter':'Nearest, to retain clear deliberately pixelated detail at96x96','raw_grounded_hoof_roi':list(roi),'generated_sole_roi_after_scale':rr,'generated_sole_bounds':bb,'source_grounded_hoof_rois':sourcerois[i],'source_hoof_anchor':list(targets[i]),'whole_frame_translation':xy,'registered_hoof_anchor':[cx+xy[0],bottom+xy[1]],'clipped_nonzero_alpha_pixels':0,'registration_basis':['idle0 grounded hind; lifted front not an anchor','idle1 paired grounded front/hind groups','idle2 grounded front; lifted hind not an anchor'][i]})
aliases=[0,1,2,1,0,1];atlas=Image.new('RGBA',(576,96))
for slot,c in enumerate(aliases):
 selected[c].save(P/f'deliverables/tactical-idle-{slot:02}.png');atlas.alpha_composite(selected[c],(96*slot,0))
atlas.save(P/'deliverables/tactical-idle.png')
subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',*map(str,(P/'deliverables').glob('tactical-idle*.png'))],check=True)
rows=[]
for slot,c in enumerate(aliases):
 fn=f'deliverables/tactical-idle-{slot:02}.png'
 rows.append({'source_index':slot,'canonical_source_index':c,'output_index':slot,'path':fn,'output_path':fn,'selected_source':f'source/idle-selected-{c:02}.png','generated_source':'source/idle-generated-v1.png','prompt':'source/idle-prompt-v1.txt','registration_record':'source/idle-registration.json','whole_frame_mirror_x':False,'registration_offset':reg[c]['whole_frame_translation'],'registered_hoof_anchor':reg[c]['registered_hoof_anchor'],'clipped_nonzero_alpha_pixels':0,'compression':'oxipng -o3 lossless',**info(P/fn)})
s={'id':'tactical-idle','class_id':7,'original_class_id':7,'source_side':'enemy','character_id':'enemy-gold-knight','display_name':'敌方黄金骑士','source_atlas':'reference/idle-source-atlas.png','original_source_path':'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_7_enemy.png','source_frame_size':[24,24],'source_anchor':[12,20],'output_atlas':'deliverables/tactical-idle.png','output_frame_size':[96,96],'output_anchor':[48,80],'logical_render_scale':.25,'canonical_count':3,'source_alias_to_canonical':aliases,'frame_mapping':rows,'directions':{'all':[0,1,2,1]},'direction_mirror_x':{},'default_facing':'fixed','static_facing':True,'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]},'adaptation_note':'Mounted left-facing native static idle; lifted forehoof / paired support / lifted hindhoof phases. Diagonal lance is distinct from legs; bottom black strip not treated as all hoof soles.','preview_dark':'previews/tactical-idle-dark.gif','preview_light':'previews/tactical-idle-light.gif'}
d={'schema_version':1,'actor_id':'enemy-gold-knight','character_id':'enemy-gold-knight','display_name':'敌方黄金骑士','class_id':7,'original_class_id':7,'source_side':'enemy','width_height_scale':4,'status':'idle_complete_tactical_walk_pending_source_audit','runtime_integrated':False,'source_originals_unchanged':True,'identity_reference':'../battle/frames/frame-000.png','art_mode':'Built-in ImageGen; crop, uniform nearest scale, whole-frame translation and lossless compression only. No procedural character drawing.','scenarios':[s],'tactical_walk_status':'Old original-walk-7.png derives from village/world route and is NOT accepted as native tactical source. References retained only as history; no walk art has been generated from it. Await corrected CPU extraction and independent audit.','qa':{'review':'previews/idle-original-dark-light.png','registration':'source/idle-registration.json','checks':['All6static slotsRGBA96x96','Exact original aliases0/4,1/3/5,2','Visible hoof ROIs exclude lance and broad black source baseline','Complete alpha silhouette preserved without clipping','Fixed original facing; no map enemy battle mirror applied','No runtime integration or source modification']}}
for fn in ['mapping.json','frame_mapping.json']:(P/fn).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(P/'source/idle-registration.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
(P/'qa-summary.json').write_text(json.dumps({'status':d['status'],'class_id':7,'source_side':'enemy','character_id':d['character_id'],'qa':d['qa'],'sizes':[{'path':x['path'],'purpose':'tactical-idle','pixels':x['size'],'bytes':x['bytes']} for x in rows]},ensure_ascii=False,indent=2)+'\n')
board=Image.new('RGB',(864,960));draw=ImageDraw.Draw(board)
for row,bg in enumerate([(230,225,216),(35,40,48),(230,225,216)]):
 draw.rectangle((0,320*row,864,320*(row+1)),fill=bg)
 for i in range(3):
  a=Image.open(P/f'reference/idle-source-{i:02}.png').convert('RGBA').resize((96,96),Image.Resampling.NEAREST) if row==0 else selected[i]
  a=a.resize((288,288),Image.Resampling.NEAREST);board.paste(a,(288*i,320*row+24),a);draw.text((288*i+8,320*row+5),f'idle{i} '+['original','new dark','new light'][row],fill='white' if row==1 else 'black')
board.save(P/'previews/idle-original-dark-light.png',optimize=True)
small=Image.new('RGB',(288,192))
for row,bg in enumerate([(35,40,48),(230,225,216)]):
 small.paste(bg,(0,row*96,288,(row+1)*96))
 for i,a in enumerate(selected):small.paste(a,(96*i,96*row),a)
small.save(P/'previews/idle-actual-size-dark-light.png')
for tone,bg in [('dark',(35,40,48)),('light',(230,225,216))]:
 ims=[]
 for i in [0,1,2,1]:
  a=selected[i].resize((288,288),Image.Resampling.NEAREST);q=Image.new('RGB',(288,288),bg);q.paste(a,(0,0),a);ims.append(q)
 ims[0].save(P/f'previews/tactical-idle-{tone}.gif',save_all=True,append_images=ims[1:],duration=[233,133,233,133],loop=0,disposal=2)
print(json.dumps(reg,ensure_ascii=False));print('idle frame bytes',min(r['bytes'] for r in rows),max(r['bytes'] for r in rows))
