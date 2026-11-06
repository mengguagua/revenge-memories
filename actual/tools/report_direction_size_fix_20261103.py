# -*- coding: utf-8 -*-
from pathlib import Path
import json,hashlib,shutil,subprocess,html
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'actual/reports/direction-size-fix-20261103'
RAW=ROOT/'source/direction-size-fix-20261103/screenshots';RAW.mkdir(parents=True,exist_ok=True)
logic=json.loads((OUT/'logic.json').read_text());visual=json.loads((OUT/'visual.json').read_text());assert not logic['errors'] and not visual['errors']
images=[]
for name in visual['screenshots']:
    p=OUT/name;raw=RAW/name
    if p.exists():shutil.copy2(p,raw)
    out=OUT/(Path(name).stem+'.webp');subprocess.run(['/opt/homebrew/bin/magick',str(raw),'-define','webp:lossless=true',str(out)],check=True)
    pixels=subprocess.check_output(['/opt/homebrew/bin/magick','identify','-format','%wx%h',str(out)],text=True)
    images.append({'file':out.name,'pixels':pixels,'bytes':out.stat().st_size,'usage':'后台实际截图／无损WebP'})
    if p.exists():p.unlink()
old=json.loads((ROOT/'actual/reports/weapon-rescue-square-20261103/verification.json').read_text())['source_sha256']
unchanged={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in old.items() if p not in ['actual/core/phone_shell.gd','actual/tests/weapon_rescue_square_20261103.gd']}
assert all(unchanged.values())
verification={'logic_checks':logic['checks'],'background_checks':visual['checks'],'errors':[], 'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['actual/core/phone_shell.gd','actual/tests/direction_size_fix_20261103.gd']},'unchanged_gameplay':unchanged,'images':images}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
def fig(path,caption):
    return '<figure><a href="'+path+'"><img loading="lazy" src="'+path+'" alt="'+html.escape(caption)+'"></a><figcaption>'+html.escape(caption)+'</figcaption></figure>'
parts=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>方向键尺寸更正 · 2026-11-03</title><style>body{margin:0;background:#101820;color:#e1e8ed;font:16px/1.8 system-ui,sans-serif}main{max-width:1160px;margin:auto;padding:30px 24px 64px}h1,h2{color:#ead6aa;line-height:1.4}h1{font-size:28px}h2{font-size:22px;margin-top:36px}a{color:#96c5eb}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:20px}figure{margin:18px 0}img{display:block;width:100%;border-radius:6px}figcaption{font-size:14px;color:#b7c1cb}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:9px 14px;border-bottom:1px solid #344451}.box{padding:18px 24px;background:#1b2b37;border-radius:8px}@media(max-width:700px){.grid{display:block}main{padding:24px 14px}}</style><main><h1>方向键：恢复按钮大小，只收紧实际间距</h1><div class="box"><p>上次缩小过头了。按钮材质有透明边，我直接按整块绘制矩形计算重叠，忽略了图片实际可见的边框。</p><p>绘制框从43×43改成35×35，看似只少8像素；透明边仍占原来的宽度，可见部分却从约33×31变成25×23，面积少了约44%，因此看起来明显偏小。</p><p>已恢复原先的43像素绘制宽度，按材质上下透明边补偿高度，使可见按钮为33×33，再按可见边框排列。触控范围覆盖整个按钮及边缘，四键互不重叠。此前约10屏幕像素左调保留。</p></div><h2>前后运行对照</h2><div class="grid">''']
parts.append(fig('../weapon-rescue-square-20261103/wide-square-directions.webp','上次：可见按钮约25×23，空隙偏大'))
parts.append(fig('wide-restored-size.webp','本次：恢复原先宽度；可见按钮33×33，外围103×103逻辑像素'))
parts.append('</div><h2>实际尺寸与点击</h2><table><thead><tr><th>项目</th><th>本次尺寸（逻辑像素）</th></tr></thead><tbody><tr><td>位图绘制区域，含透明边</td><td>43×45</td></tr><tr><td>可见按钮</td><td>33×33</td></tr><tr><td>单键点击范围</td><td>35×35</td></tr><tr><td>四键可见外围</td><td>103×103</td></tr></tbody></table><p>按实际位图透明度检查边界；箭头和按下光晕对齐可见按钮。窄屏仍保留边框间距与中央内容的安全距离，最窄支持窗口按可用空间小幅适配。</p><div class="grid">')
parts.append(fig('compact-restored-size.webp','1334×750：可见按钮99×99屏幕像素，外围309×309'))
parts.append(fig('wide-pressed-right.webp','按下右键：保留材质与柔和阴影，箭头居中'))
parts.append('</div><h2>定向检查</h2><p>'+str(logic['checks'])+'项无窗口逻辑、'+str(visual['checks'])+'项后台画面与布局检查通过。覆盖原图透明边测量、可见边框正方形、点击覆盖、触控互不重叠、中央内容避让、四键真实按下／松开、状态页右键切换以及宽屏、窄屏、最小窗口。</p>')
parts.append('<p>本轮仅调整方向键及对应检查；武器命中与双救经验奖励的源文件校验保持一致。未安装或更新iPhone。</p><p><a href="logic.json">逻辑结果</a> · <a href="visual.json">后台检查</a> · <a href="verification.json">图片尺寸／体积与源文件校验</a></p><p>截图均为原尺寸无损WebP；原始PNG保存在source/direction-size-fix-20261103/screenshots。</p></main></html>')
(OUT/'index.html').write_text(''.join(parts))
p=ROOT/'actual/README.md';entry='2026-11-03 方向键尺寸更正：此前按含透明边的绘制矩形防重叠，把可见按钮缩至约25×23。现按原材质实测透明边恢复43×45绘制区域、33×33可见按钮，触控35×35，四键可见外围103×103；箭头与按下光晕按可见面居中，保留约10屏幕像素左调。[前后运行对照与定向验证](reports/direction-size-fix-20261103/index.html)。未安装或更新iPhone。\n\n';s=p.read_text()
if not s.startswith('2026-11-03 方向键尺寸更正'):p.write_text(entry+s)
print(json.dumps({'logic':logic['checks'],'background':visual['checks'],'images':len(images),'largest_bytes':max(i['bytes'] for i in images),'unchanged_gameplay':all(unchanged.values())},ensure_ascii=False))
