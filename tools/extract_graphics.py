#!/usr/bin/env python3
"""Decode FE2 source CHR and original OAM tables. No redrawing or raster resampling."""
from pathlib import Path
from PIL import Image, ImageDraw
import re, json, shutil, hashlib, argparse
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets/original/graphics'
DATA = ROOT/'data/graphics.json'
# NES RGB reference palette. Output is an RGB interpretation of palette indices;
# original CHR shape data, source palette indices, and OAM are preserved verbatim.
RGB_HEX = '666666 002a88 1412a7 3b00a4 5c007e 6e0040 6c0700 561d00 333500 0b4800 005200 004f08 00404d 000000 000000 000000 adadad 155fd9 4240ff 7527fe a01acc b71e7b b53120 994e00 6b6d00 388700 0c9300 008f32 007c8d 000000 000000 000000 ffffff 64b0ff 9290ff c676ff f36aff fe6ecc fe8170 ea9e22 bcbe00 88d800 5ce430 45e082 48cdde 4f4f4f 000000 000000 ffffff c0dfff d3d2ff e8c8ff fbc2ff fec4ea feccc5 f7d8a5 e4e594 cfef96 bdf4ab b3f3cc b5ebf2 b8b8b8 000000 000000'
NES=[tuple(bytes.fromhex(s)) for s in RGB_HEX.split()]
PALS = {'ally':[[0x0f,0x20,0x22,0x0f],[0x0f,0x20,0x22,0x0f],[0x0f,0x28,0x17,0x0f],[0x0f,0x0a,0x0b,0x0f]], 'enemy':[[0x0f,0x20,0x16,0x0f],[0x0f,0x20,0x16,0x0f],[0x0f,0x28,0x17,0x0f],[0x0f,0x0a,0x0b,0x0f]]}
def blocks(path):
 result={}; current=None
 for raw in path.read_text().splitlines():
  line=raw.split(';')[0].strip()
  if re.match(r'^\w+:',line):
   current=line.split(':')[0]; result[current]={'db':[],'dw':[]}
  elif current and line.startswith('.db'):
   result[current]['db'] += [int(x,16) for x in re.findall(r'\$([0-9a-fA-F]{2})(?![0-9a-fA-F])',line)]
  elif current and line.startswith('.dw'):
   result[current]['dw'] += re.findall(r'\bL\w+',line)
 return result

def decode(raw):
 tiles=[]
 for i in range(len(raw)//16):
  b=raw[i*16:i*16+16]
  im=Image.new('L',(8,8));p=im.load()
  for y in range(8):
   for x in range(8): p[x,y]=((b[y]>>(7-x))&1)|(((b[y+8]>>(7-x))&1)<<1)
  tiles.append(im)
 return tiles

def color(t,pal,transparent=True):
 im=Image.new('RGBA',t.size); src=t.load();dst=im.load()
 for y in range(t.height):
  for x in range(t.width):
   v=src[x,y]; dst[x,y]=NES[pal[v]&63]+((0 if transparent and v==0 else 255),)
 return im

def oam(data,tiles,pals):
 count=data[0]; assert len(data)>=count*4+1,(count,len(data))
 sprites=[]
 for i in range(count):
  y,t,a,x=data[1+4*i:5+4*i];x=x-256 if x>=128 else x;y=y-256 if y>=128 else y
  im=color(tiles[t],pals[a&3]);
  if a&64:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if a&128:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  sprites.append((x,y,im))
 # A frame centered on source anchor x=0, ground y=32. 80x64 preserves sword reach.
 im=Image.new('RGBA',(80,64));
 for x,y,t in reversed(sprites): im.alpha_composite(t,(x+40,y+24))
 return im

def save(im,path,meta,**info):
 path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True,compress_level=9)
 meta['assets'].append({'path':'res://'+str(path.relative_to(ROOT)),'width':im.width,'height':im.height,'bytes':path.stat().st_size,**info})

VILLAGE_TABLES=['L0A94CB','L0A954F','L0A95D3','L0A9657','L0A96DB','L0A975F']
VILLAGE_IDS={'alm':1,'mycen':3,'lukas':7,'kliff':13,'tobin':12,'gray':14}
VILLAGE_PALETTE=[[0xf,0x13,0x36,0xf],[0xf,0x11,0x36,0xf],[0xf,0x15,0x36,0xf],[0xf,0x17,0x36,0xf]]

def extract_village(src,meta):
 # The village's personal OAM and the tactical moving OAM share the same
 # pointer tables, but do NOT share pattern data. L0DADA0 / L0DADB0 restore
 # CHR 30 into both MMC4 $0000 FD/FE latch banks. CHR 26 is the battlefield
 # movement bank (L0FD3B5); using it here scrambles torsos and walking poses.
 b10=blocks(src/'src/bank010.asm')
 tiles=decode((src/'src/bank015.chr').read_bytes()[:4096])
 meta['assets']=[asset for asset in meta['assets'] if asset.get('kind')!='village_personal_oam']
 meta['village_units']={}
 for name,sprite_id in VILLAGE_IDS.items():
  idx=sprite_id-1;sheet=Image.new('RGBA',(144,24))
  for j,t in enumerate(VILLAGE_TABLES):
   frame=oam(b10[b10[t]['dw'][idx]]['db'],tiles,VILLAGE_PALETTE).crop((36,12,60,36))
   sheet.alpha_composite(frame,(j*24,0))
  save(sheet,OUT/'map_units'/f'village_{name}.png',meta,kind='village_personal_oam',frame_size=[24,24],frame_count=6,source_sprite_id=sprite_id,source_oam_index=idx,source_oam=[b10[t]['dw'][idx] for t in VILLAGE_TABLES],palette_source='bank013:L0D9230',palette_indices=VILLAGE_PALETTE,chr_bank=30,chr_source='bank015.chr:first4KiB',pattern_bank_source='bank013:L0DADA0,L0DADB0',ppu_sprite_size=[8,8])
  meta['village_units'][name]={'path':f'res://assets/original/graphics/map_units/village_{name}.png','frame_size':[24,24],'frames':6,'anchor':[4,20],'tile_origin':[4,4],'directions':{'down':[0,1],'up':[2,3],'side':[4,5]},'sprite_id':sprite_id,'chr_bank':30,'source_rule':'bank015:L0FCC01 decrements character sprite id; bank010:L0A8D33 records opening NPC ids; bank013:L0DADA0,L0DADB0 restore village CHR bank 30.'}

def village_only(src):
 # Rebuild only the six runtime village sheets and their metadata. Other
 # recovered graphics and Chinese font metadata are deliberately retained.
 meta=json.loads(DATA.read_text());extract_village(src,meta)
 meta['portraits']['alm'].update({'source_selection_rule':'bank009:L09AE13-L09AE33: unpromoted character 1 -> L09BDBF[1] = portrait 36; promoted character 36 -> L09BDBF[36] = portrait 0.'})
 meta['portraits']['celica'].update({'source_selection_rule':'bank009:L09AE13-L09AE33: unpromoted character 2 -> L09BDBF[2] = portrait 48; promoted character 37 -> L09BDBF[37] = portrait 16.'})
 DATA.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
 print('Six village sheets rebuilt with original CHR 30; all other graphics retained.')

def main(src):
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'source').mkdir(exist_ok=True)
 meta={'source_repository':'https://github.com/minirop/fe2','source_revision':'956365ef33c63751e7afd03f05e600d7728549da','rgb_palette_note':'NES palette indices decoded using fixed RGB interpretation; display emulator color profiles may differ. No anti-aliasing or resampling.', 'assets':[],'portraits':{},'map_units':{},'battle':{},'font':{}}
 banks=[]
 for b in range(16):
  name=f'bank{b:03}.chr';raw=(src/'src'/name).read_bytes();shutil.copy2(src/'src'/name,OUT/'source'/name)
  tiles=decode(raw);banks.append(tiles)
  im=Image.new('RGBA',(128,256))
  for i,t in enumerate(tiles):im.alpha_composite(color(t,[0x0f,0x00,0x10,0x20],False),((i%16)*8,(i//16)*8))
  save(im,OUT/'atlases'/f'chr_{b:02}.png',meta,kind='chr_atlas',source=name,source_sha256=hashlib.sha256(raw).hexdigest(),tile_size=[8,8])
 for name in ['tileset','buildings','worldtiles']:
  im=Image.open(src/'maps'/f'{name}.png');save(im,OUT/'maps'/f'{name}.png',meta,kind='original_map_tiles',source=f'maps/{name}.png')
 b9=blocks(src/'src/bank009.asm');ptrs=b9['L09AE97']['dw'];palptrs=b9['L09AF6B']['dw'];colptrs=b9['L09BAFD']['dw'];chrids=b9['L09B014']['db']
 portraits=[]
 for i,ptr in enumerate(ptrs):
  data=b9[ptr]['db'];attr=b9[palptrs[i]]['db'];cols=b9[colptrs[i]]['db'];pals=[[0xf]+cols[j*3:j*3+3] for j in range(4)]
  im=Image.new('RGBA',(48,48));bank=chrids[i]//2;offset=(chrids[i]%2)*256
  for j,t in enumerate(data[:36]):
   a=(attr[j//2]>>4) if j%2==0 else (attr[j//2]&15);tile=color(banks[bank][offset+t],pals[a&3]);
   if a&4:tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   if a&8:tile=tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
   im.alpha_composite(tile,((j%6)*8,(j//6)*8))
  portraits.append(im);save(im,OUT/'portraits'/f'portrait_{i:02}.png',meta,kind='portrait',source=f'bank009.asm:{ptr}',palette_indices=pals,chr_bank=chrids[i])
 pcontact=Image.new('RGB',(10*104,6*116),(32,35,40));dr=ImageDraw.Draw(pcontact)
 for i,im in enumerate(portraits):
  x=i%10*104;y=i//10*116;pcontact.paste(im.resize((96,96),Image.Resampling.NEAREST),(x,y+16),im.resize((96,96),Image.Resampling.NEAREST));dr.text((x+3,y+2),str(i),fill='white')
 pcontact.save('/private/tmp/portrait-contact.png')
 # L09BDBF maps character ids to portrait ids. L09AE13-L09AE33 preserve
 # character id 1/2 before promotion -> portrait 36/48. After promotion,
 # character id 36/37 -> portrait 0/16. The portrait order is not story order.
 charmap={'alm':36,'celica':48,'mycen':3,'lukas':4,'kliff':6,'tobin':7,'gray':5}
 for name,i in charmap.items():
  save(portraits[i],OUT/'portraits'/f'{name}.png',meta,kind='portrait_alias',portrait_index=i)
  meta['portraits'][name]={'path':f'res://assets/original/graphics/portraits/{name}.png','source_portrait_index':i,'size':[48,48]}
 # All map OAM frames extracted from the source six-table structure. The original
 # map class lookup is assigned separately after contact sheet verification.
 b10=blocks(src/'src/bank010.asm');tables=['L0A94CB','L0A954F','L0A95D3','L0A9657','L0A96DB','L0A975F']
 mapframes=[];mc=Image.new('RGB',(11*112,6*144),(42,45,48));md=ImageDraw.Draw(mc)
 for i in range(66):
  ims=[oam(b10[b10[t]['dw'][i]]['db'],banks[13][:256],[[0xf,0x20,0x21,0x11]]*4) for t in tables]
  sheet=Image.new('RGBA',(6*80,64))
  for j,im in enumerate(ims):sheet.alpha_composite(im,(j*80,0))
  save(sheet,OUT/'map_units'/f'meta_{i:02}.png',meta,kind='map_oam_frames',frame_size=[80,64],frame_count=6,source=[b10[t]['dw'][i] for t in tables],chr_bank=26)
  mapframes.append(ims);x=i%11*112;y=i//11*144;md.text((x,y),str(i),fill='white');thumb=ims[0].crop((32,16,64,48)).resize((96,96),Image.Resampling.NEAREST);mc.paste(thumb,(x,y+20),thumb)
 mc.save('/private/tmp/map-contact.png')
 extract_village(src,meta)
 # Tactical map units are background metatiles (class*2 / class*2+1),
 # not village OAM actors. L_BANKS_ANIMATIONS cycles CHR 24,25,21,25;
 # L06852C assigns blue/pink palettes and green underlying terrain color.
 # Index 3 is terrain, made transparent for compositing over the Godot map.
 metas=[]
 for line in (src/'src/bank006.asm').read_text().split('L_METATILES_PALETTE_ID:')[0].splitlines():
  if line.strip().startswith('.db'):metas.extend(int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',line.split(';')[0]))
 classes={'fighter':21,'soldier':6,'villager':14,'brigand':14,'mycen':7}
 cycle=[24,25,21,25,24,25]
 for name,cls in classes.items():
  for side,pal in [('ally',[0xf,0x20,0x22,0x1a]),('enemy',[0xf,0x36,0x25,0x1a])]:
   sheet=Image.new('RGBA',(144,24));tile_indices=metas[cls*8:cls*8+4]
   for frame,c in enumerate(cycle):
    for j,tid in enumerate(tile_indices):
     raw=banks[c//2][(c%2)*256+tid];tile=color(raw,pal,False)
     for yy in range(8):
      for xx in range(8):
       if raw.getpixel((xx,yy))==3:tile.putpixel((xx,yy),(0,0,0,0))
     sheet.alpha_composite(tile,(frame*24+4+j%2*8,4+j//2*8))
   save(sheet,OUT/'map_units'/f'{name}_{side}.png',meta,kind='tactical_map_unit',frame_size=[24,24],frame_count=6,class_id=cls,source_metatile=cls*2,source_tile_indices=tile_indices,source_chr_cycle=cycle,palette_indices=pal,palette_source='bank006:L06852C')
   meta['map_units'][f'{name}_{side}']={'path':f'res://assets/original/graphics/map_units/{name}_{side}.png','frame_size':[24,24],'frames':6,'anchor':[12,20],'directions':{'down':[0,1],'up':[2,3],'side':[4,5]},'class_id':cls,'mapping_note':'Exact tactical map metatile composition and CHR cycle. Original battlefield idle sprites do not turn; directions aliases repeat cycle.'}
 b0=blocks(src/'src/bank000.asm');b5=blocks(src/'src/bank005.asm')
 # Battle sprite lookup is directly restored from L0FE436 / L0FE44C (PRG table),
 # L058E98 / L058EAE (CHR bank), and L058EC4 / L058EDA (palette).
 battledefs=[('fighter',b0,'L008064',1,69),('soldier',b9,'L098F7B',2,54),('villager',b9,'L098FCD',2,62),('brigand',b9,'L098FCD',16,84)]
 seqs={'fighter':{'idle':[0],'walk':[1,2,3,4],'attack':[0,4,5,6,7,8,9,0],'hit':[27,28,0],'death':[36,37]},'soldier':{'idle':[0],'walk':[1,2,3],'attack':[0,4,5,6,7,10,11,0],'hit':[8,9,0],'death':[8,9]},'villager':{'idle':[0],'walk':[1,2,3],'attack':[0,1,2,3,4,5,6,7,8,9,0],'hit':[10,11,0],'death':[14,15]},'brigand':{'idle':[0],'walk':[1,2,3],'attack':[0,1,2,3,4,5,6,7,8,9,0],'hit':[10,11,0],'death':[14,15]}}
 for name,b,t,c,p in battledefs:
  refs=b[t]['dw'];palette_ptr=b5['L05BCF1']['dw'][p];pal=b5[palette_ptr]['db'][:4];tiles=banks[c//2][(c%2)*256:((c%2)+1)*256]
  sheet=Image.new('RGBA',(len(refs)*80,64))
  for i,ref in enumerate(refs):sheet.alpha_composite(oam(b[ref]['db'],tiles,[pal]*4),(i*80,0))
  for side in ['ally','enemy']:
   save(sheet,OUT/'battle'/f'{name}_{side}.png',meta,kind='battle_oam_frames',frame_size=[80,64],frame_count=len(refs),source_oam_table=t,source_oam=refs,chr_bank=c,palette_source=palette_ptr,palette_indices=pal)
   meta['battle'][f'{name}_{side}']={'path':f'res://assets/original/graphics/battle/{name}_{side}.png','frame_size':[80,64],'frames':len(refs),'anchor':[40,56],'default_facing':'left','sequences':seqs[name],'frame_seconds':0.08,'animation_note':'Original source frames/CHR/palettes exact; sequence and playback timing inferred for native Godot, original opcode scheduler not yet reconstructed.'}
 # Reconstruct standard melee pose/timer programs. L009F38 runs one timer
 # tick per frame; $FF terminates, $FE loops. Opcode 05 in L05B025 starts
 # this pose program, opcode 03 waits for the contact pose, and opcode 08
 # pauses pose playback while original damage feedback resolves.
 original_attack_specs={'fighter':(15,9,'L05B37E',22,22),'soldier':(5,5,'L05B18A',33,33),'villager':(11,6,'L05B2DC',22,22),'brigand':(12,15,'L05B307',21,34)}
 fps=60.0988
 rompath=src/'fe2.nes';prg0=rompath.read_bytes()[16:16+16384] if rompath.exists() else None
 def movement_steps(program):
  if prg0 is None:return None
  def rb(a):return prg0[a-0x8000]
  def rw(a):return rb(a)+256*rb(a+1)
  ptr=rw(0xae84+program*2);codes=[]
  for _ in range(256):
   v=rb(ptr);ptr+=1
   if v==255:break
   codes.append(v)
  steps=[]
  for c in codes:
   pp=rw(0xb125+c*2)
   for _ in range(512):
    dx=rb(pp)
    if dx==128:break
    dy=rb(pp+1);steps.append([dx-256 if dx>=128 else dx,dy-256 if dy>=128 else dy]);pp+=2
  return {'program_id':program,'vector_ids':codes,'per_tick_delta':steps,'total_delta':[sum(v[0] for v in steps),sum(v[1] for v in steps)],'source_tables':['L00AE84','L00B125'],'native_fps':fps}
 for name,(idx,strike,program,approach,retreat) in original_attack_specs.items():
  pose_ptr=b0['L009FF1']['dw'][idx];timer_ptr=b0['L00A051']['dw'][idx];poses=b0[pose_ptr]['db'];ticks=b0[timer_ptr]['db'][:len(poses)]
  assert len(poses)==len(ticks) and all(0<t<254 for t in ticks)
  strike_index=poses.index(strike);start=sum(ticks[:strike_index]);idle=8 if name=='brigand' else 0
  for side in ['ally','enemy']:
   entry=meta['battle'][f'{name}_{side}'];entry['sequences']['attack']=poses;entry['sequences']['idle']=[idle];entry['sequences']['hit']=[idle];entry['sequences']['death']=[idle]
   if name=='brigand':entry['sequences']['walk']=[11,12,10,9]
   entry['attack_schedule']={'poses':poses,'ticks':ticks,'durations':[round(t/fps,7) for t in ticks],'native_fps':fps,'duration_without_damage_pause':sum(ticks)/fps,'contact_sequence_index':strike_index,'contact_pose':strike,'contact_tick':start,'contact_seconds':start/fps,'hold_at_contact':True,'pose_source':pose_ptr,'timer_source':timer_ptr,'attack_program_source':program,'engine_source':'L009F38-L009FD5; L05957D opcode05/03/08/09','approach':movement_steps(approach),'retreat':movement_steps(retreat),'retreat_mirrors_delta':True,'contact_note':'At contact pose the original program pauses pose playback, resolves damage feedback/HP countdown, then resumes the recovery/return poses. Extra pause duration depends on hit/critical/damage, so duration_without_damage_pause is only the authored pose-program length.'}
   entry['attack_schedule'].update({'approach_when_pose':{'fighter':2,'soldier':0,'villager':2,'brigand':11}[name],'approach_start_tick':{'fighter':16,'soldier':0,'villager':8,'brigand':8}[name],'retreat_when_pose':{'fighter':2,'soldier':4,'villager':1,'brigand':10}[name],'retreat_start_after_contact_resume_ticks':{'fighter':28,'soldier':48,'villager':16,'brigand':16}[name],'minimum_contact_pause_ticks':16,'movement_note':'All source deltas assume the original actor on the right facing left. Mirror X for an actor on the left facing right. Retreat uses same facing basis and negates its X deltas. Y is screen-down. Absolute event timing depends on original opcode scheduling and damage pause.'})
   entry['feedback']={'hit':'Keep current pose; source palette flash and screen displacement. No extra slash or standalone invented hit pose.','death':'Keep current pose; source palette fade followed by removing actor.','death_palette_steps':4,'death_step_ticks':8,'source':'L059CA0/L059C33/L059F35-L059F73'}
   entry['animation_note']='Standard attack pose order and frame counts recovered exactly from original programs. Damage pause/HP feedback and movement start/resume must be handled by game events; compatibility idle/hit/death aliases preserve source standing pose.'
 # The NES side-view area is blank black, not a painted terrain background.
 # L05803C calls L0FC23D (fill nametables with tile FF), and original UI begins
 # at PPU $2201/$2210 (pixel row128) in L01B01D/L01B052. Terrain is named
 # in the stat panel; there is no grass/forest scenery upload in this path.
 background=Image.new('RGBA',(256,128));blank=color(banks[0][0xff],[0xf,0x36,0x24,0x15],False)
 for yy in range(0,128,8):
  for xx in range(0,256,8):background.alpha_composite(blank,(xx,yy))
 save(background,OUT/'battle_background.png',meta,kind='battle_background',source='bank005:L05803C -> bank015:L0FC23D-L0FC284; bank001:L01B01D/L01B052 begin UI at pixel row128',content_note='Native 256x128 blank-black side-view field. No terrain illustration or invented ground strip.')
 meta['battle_background']={'path':'res://assets/original/graphics/battle_background.png','native_size':[256,128],'actor_source_positions':{'ally':[176,96],'enemy':[64,96]},'ground_y':128,'terrain_note':'Original grass/forest side-view background is black; terrain label belongs to the lower status panel. Source nametable clear uses blank FF, lower HUD starts at row128.'}
 # Restore blank original HUD frame and HIT/AT/DF labels from PPU upload
 # commands; health, names, terrain and counts remain dynamic game text.
 b1=blocks(src/'src/bank001.asm');name=[0xff]*1024
 def ppu_upload(data):
  pos=0
  while pos<len(data) and data[pos]:
   addr=data[pos]*256+data[pos+1];cmd=data[pos+2];pos+=3;count=cmd&63;step=32 if cmd&128 else 1
   if cmd&64:values=[data[pos]]*count;pos+=1
   else:values=data[pos:pos+count];pos+=count
   for v in values:
    if 0x2000<=addr<0x2400:name[addr-0x2000]=v
    addr+=step
 for key in ['L05892E','L058959']:ppu_upload(b5[key]['db'])
 for key in ['L01B01D','L01B052','L01B087','L01B0B0','L01B0D9','L01B0DE']:ppu_upload(b1[key]['db'])
 bpal=b5['L05BCCD']['db'][3:19];pals=[bpal[i*4:i*4+4] for i in range(4)]
 # L05BCCD upload header is 3 bytes; all four background groups preserve
 # common color0 black and their next three source color indices.
 palette_raw=b5['L05BCCD']['db'][3:19];pals=[]
 for k in range(4):pals.append(palette_raw[k*4:k*4+4])
 hud=Image.new('RGBA',(256,112),(0,0,0,255))
 for row in range(16,30):
  for col in range(32):
   tid=name[row*32+col];attr=name[960+(row//4)*8+col//4];shift=((row%4)//2)*4+((col%4)//2)*2;palidx=(attr>>shift)&3
   hud.alpha_composite(color(banks[0][tid],pals[palidx],False),(col*8,(row-16)*8))
 save(hud,OUT/'battle_hud_frame.png',meta,kind='battle_hud_source_frame',source='bank001:L01B01D,L01B052,L01B087,L01B0B0; bank005:L05892E,L058959,L05BCCD',content_note='Blank source HUD structure and HIT/AT/DF glyphs; dynamic labels/HP/values are not rasterized.')
 meta['battle_hud']={'path':'res://assets/original/graphics/battle_hud_frame.png','native_size':[256,112],'source_screen_position':[0,128],'dynamic_fields':'names/terrain/class/HP and battle values remain native game text.'}
 # Title logo and title sword are source-defined tiles and OAM positions.
 # Header $53 encodes 19 columns / 2 rows. PPU $21C6 is pixel (48,112).
 # Sprite placement follows L049D17/L049D39/L049D57. This is the final title
 # composition, without the original intro fade/rotation opcode scheduler.
 b4=blocks(src/'src/bank004.asm');title_pal=b4['L049EF2']['db'];logo=Image.new('RGBA',(152,16))
 for j,tid in enumerate(b4['L049EB0']['db'][1:39]):logo.alpha_composite(color(banks[14][256+tid],title_pal[:4]),(j%19*8,j//19*8))
 save(logo,OUT/'title_logo.png',meta,kind='title_logo',source='bank004:L049EB0',chr_bank=29,palette_indices=title_pal[:4],source_screen_position=[48,112])
 title=Image.new('RGBA',(256,240),(0,0,0,255));title.alpha_composite(logo,(48,112));pals=[title_pal[16+i*4:20+i*4] for i in range(4)]
 placements=[('L049FAA',176,111),('L049FE7',176,79),('L04A045',160,103),('L049FEC',176,111)]
 for ptr,px,py in placements:
  d=b4[ptr]['db']
  for i in reversed(range(d[0])):
   yy,tid,attr,xx=d[1+4*i:5+4*i];xx=xx-256 if xx>=128 else xx;yy=yy-256 if yy>=128 else yy;tile=color(banks[11][256+tid],pals[attr&3])
   if attr&64:tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   if attr&128:tile=tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
   title.alpha_composite(tile,(px+xx,py+yy))
 copyright_ids=[0xb9,0x61,0x69,0x69,0x61,0xff,0xa0,0xa1,0xa2,0xa3,0xa4,0xa5]
 for j,tid in enumerate(copyright_ids):title.alpha_composite(color(banks[0][tid],[0xf,0x20,0x21,0x11]),(72+j*8,168))
 save(title,OUT/'title.png',meta,kind='title_screen',source='bank004:L049D17,L049D39,L049D57,L049DBC',content_note='Original title logo, sword source OAM, and copyright. Final static composition; rotation/fade intro not reproduced.')
 meta['title']={'path':'res://assets/original/graphics/title.png','logo':'res://assets/original/graphics/title_logo.png','native_size':[256,240],'logo_position':[48,112],'source_chr_banks':[23,29,0]}
 # Native font is the first CHR bank, preserving one tile for each code byte.
 font=Image.new('RGBA',(128,128))
 for i,t in enumerate(banks[0][:256]):font.alpha_composite(color(t,[0xf,0x20,0x22,0x0f]),((i%16)*8,(i//16)*8))
 save(font,OUT/'font.png',meta,kind='font_atlas',tile_size=[8,8],source='bank000.chr:first4KiB')
 meta['font']={'path':'res://assets/original/graphics/font.png','tile_size':[8,8],'columns':16,'encoding_table':'jp.tbl'}
 # Original voiced kana is a base tile plus a separate mark tile one tile
 # row above the preceding glyph. L0FE584 decrements the glyph index for
 # marker 0F/1F and L0FE5B3 subtracts $20 from the PPU name-table address.
 codes={}
 for line in (src/'jp.tbl').read_text().splitlines():
  if '=' not in line:continue
  code,ch=line.split('=',1)
  if len(ch)==1 and re.fullmatch(r'[0-9A-Fa-f]+',code) and len(code)%2==0:codes[ch]=[int(code[i:i+2],16) for i in range(0,len(code),2)]
 meta['font'].update({'char_codes':codes,'advance':8,'glyph_size':[8,8],'recommended_line_height':16,'combining_mark_bytes':[15,31],'combining_mark_offset':[0,-8],'combining_mark_advance':0,'source_draw_rule':'bank015:L0FE584-L0FE5B3 / bank010 dialogue rendering: marker byte applies above previous base glyph.'})
 shutil.copy2(src/'jp.tbl',OUT/'source/jp.tbl')
 # UI is stored in the *first* 4KiB of CHR0 alongside the font.
 # The second half is Fighter battle graphics, not a UI bank.
 ui=font.copy();save(ui,OUT/'ui.png',meta,kind='ui_and_font_atlas',tile_size=[8,8],source='bank000.chr:first4KiB')
 panel=Image.new('RGBA',(24,24));panel_ids=[0xf5,0xf7,0xf6,0xfd,0xff,0xfe,0xf9,0xf8,0xfa]
 for j,tid in enumerate(panel_ids):panel.alpha_composite(color(banks[0][tid],[0xf,0x20,0x22,0x11],False),(j%3*8,j//3*8))
 save(panel,OUT/'panel.png',meta,kind='ui_nine_patch',source='bank011:L0BA6F5-L0BA782 / bank000.chr',source_tile_ids=panel_ids,stretch_margins=[8,8,8,8],minimum_content_padding=10)
 meta['panel']={'path':'res://assets/original/graphics/panel.png','native_size':[24,24],'nine_patch_margins':[8,8,8,8],'content_padding':10,'center_note':'Uniform black center; fixed original pixel corners/edges. No ornament distortion.'}
 save(color(banks[0][0xf3],[0xf,0x20,0x22,0x11]),OUT/'cursor.png',meta,kind='ui_cursor',source='bank000.chr:tileF3')
 meta['cursor']={'path':'res://assets/original/graphics/cursor.png','native_size':[8,8]}
 DATA.parent.mkdir(parents=True,exist_ok=True);DATA.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
 print(f'{len(meta["assets"])} assets decoded to {OUT}')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('/private/tmp/fe2-analysis-20261012'));p.add_argument('--village-only',action='store_true');a=p.parse_args()
 (village_only if a.village_only else main)(a.source)
