from pathlib import Path
import json,subprocess,concurrent.futures
ROOT=Path('/Users/gcc/gaocc/project/revenge-memories/art-review/hunapu-20261018-v1')
OUT=ROOT/'deliverables'; TEMP=Path('/private/tmp/hunapu-review-render-20261018-v1');TEMP.mkdir(exist_ok=True)
MAGICK='/opt/homebrew/bin/magick';FFMPEG='/opt/homebrew/bin/ffmpeg';FONT='/System/Library/Fonts/STHeiti Medium.ttc'
def run(args):return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
trace=json.loads((ROOT/'reference/original-timeline.json').read_text())['sequence']
for i in range(10):
 for kind,folder in [('original',ROOT/'reference'),('new',OUT)]:
  src=folder/f'pose-{i:03}.png';assert src.exists(),src
  dimensions=run([MAGICK,str(src),'-format','%wx%h','info:']).stdout.decode();assert dimensions=='320x288',(src,dimensions)
  run([MAGICK,str(src),'-flop',str(TEMP/f'{kind}-{i:03}-flip.png')])
base=TEMP/'background.png'
run([MAGICK,'-size','1152x344','xc:#18242c','-font',FONT,'-pointsize','22','-fill','#dfe8ec','-annotate','+24+38','原作动作','-annotate','+616+38','男主重绘样板','-pointsize','14','-fill','#9eafb7','-annotate','+24+327','同步原动作 · 4×尺寸 · 待验收',str(base)])
def frame(t):
 r=trace['frames'][t];p=0 if r['frame']==90 else r['frame'];flip=r['flip'];x=round((176+r['offset'][0]-40+(16 if flip else 0)-44)*4)-100;y=16+r['offset'][1]*4
 src1=TEMP/f'original-{p:03}-flip.png' if flip else ROOT/'reference'/f'pose-{p:03}.png'
 src2=TEMP/f'new-{p:03}-flip.png' if flip else OUT/f'pose-{p:03}.png'
 phase='命中' if t==90 else '动作'
 run([MAGICK,str(base),str(src1),'-geometry',f'{x:+d}{y:+d}','-compose','over','-composite',str(src2),'-geometry',f'{x+592:+d}{y:+d}','-compose','over','-composite','-font',FONT,'-pointsize','14','-fill','#9eafb7','-annotate','+840+327',f'{phase}  {t:03}/202   {t/trace["native_fps"]:.2f}s',str(TEMP/f'frame-{t:03}.png')])
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(frame,range(203)))
run([FFMPEG,'-y','-framerate','60.0988','-i',str(TEMP/'frame-%03d.png'),'-frames:v','203','-c:v','libx264','-crf','15','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'hunapu-attack-comparison.mp4')])
run([FFMPEG,'-y','-framerate','60.0988','-i',str(TEMP/'frame-%03d.png'),'-filter_complex','fps=50,split[a][b];[a]palettegen=stats_mode=diff:max_colors=128[p];[b][p]paletteuse=dither=none:diff_mode=rectangle','-loop','0',str(OUT/'hunapu-attack-comparison.gif')])
keys=[0,3,4,6,8,9]
run([MAGICK,'montage','-font',FONT,*[str(OUT/f'pose-{p:03}.png') for p in keys],'-tile','3x2','-geometry','320x288+0+0','-background','#18242c',str(OUT/'hunapu-six-key-poses.png')])
run([MAGICK,'montage','-font',FONT,*[str(OUT/f'pose-{p:03}.png') for p in keys],'-tile','3x2','-geometry','320x288+0+0','-background','#e7e3d8',str(OUT/'hunapu-six-key-poses-light.png')])
print(json.dumps({'frames':203,'fps':trace['native_fps'],'duration':203/trace['native_fps'],'deliverables':[p.name for p in OUT.iterdir()]},ensure_ascii=False))
