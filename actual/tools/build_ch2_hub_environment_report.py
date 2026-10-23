from pathlib import Path
import json,hashlib,html
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter2-environment-20261023/hubs';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(R/'data/chapter2_hubs.json');v=read(R/'data/chapter2_hub_environment.json');review=read(O/'visual-review.json');inputs=read(O/'interaction-review.json');phase=read(O/'phase-fixture.json');assert all(x['passed']for x in [review,inputs,phase])
body=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第二章据点 · 环境与材质对照</title><style>body{background:#14212a;color:#e5eef2;font:16px/1.8 system-ui;margin:0}main{max-width:1220px;margin:auto;padding:36px 24px}section{padding:24px;border-radius:16px;background:#21323e;margin:24px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}figure{margin:0}img{width:100%;image-rendering:pixelated}figcaption,p{color:#bed0d9}a{color:#b5dae5}h1{font-size:32px}h2{font-size:24px}@media(max-width:800px){.pair{grid-template-columns:1fr}main{padding:20px 12px}}</style><main><h1>第二章据点 · 环境与材质对照</h1><p>七处据点逐一核对。岛屿保留草地与沙岸，船团是木甲板，航灯前场和军港仓院是室外石地；黑昼冷光按剧情推进。六处海上出入口补完整接驳船，保持原行动和碰撞范围。</p><p><a href="../index.html">返回第二章环境总页</a></p>']
for room,r in d['rooms'].items():
 body.append('<section><h2>'+html.escape(room+' · '+r['title'])+'</h2><p>'+html.escape(v['notes'][room])+'</p><div class="pair">')
 for state,label in [('before','修改前'),('after','修正后')]:
  path=state+'/'+room+'.png';body.append('<figure><a href="'+path+'"><img src="'+path+'" alt="'+room+' '+label+'"></a><figcaption>'+label+' · 原生562×320视口</figcaption></figure>')
 body.append('</div></section>')
body.append(f'<p>各对象均通过正常输入走到邻接位并确认，共{len(inputs["records"])}处对象、{inputs["inputs"]}次按键。{phase["count"]}项材质域与章节／黑昼阶段显示检查通过；H27前后图像逐像素相同。逐对象检查不将打开菜单等同招募／奖励结算，相关结算由两轮逐关试玩覆盖。</p><p><a href="interaction-review.json">普通输入对象检查</a> · <a href="phase-fixture.json">显示阶段检查</a> · <a href="visual-review.json">逐图检查记录</a></p></main></html>')
(O/'index.html').write_text(''.join(body))
freeze={'passed':True,'files':{p:sha(R/p)for p in ['core/story_hub.gd','data/chapter2_hubs.json','data/chapter2_hub_environment.json','assets/chapter2-environment-20261023/hubs/terrain.png']},'phase_checks':phase['count'],'normal_input_actions':len(inputs['records']),'normal_inputs':inputs['inputs'],'no_further_runtime_edits':True}
(O/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n');print(freeze)
