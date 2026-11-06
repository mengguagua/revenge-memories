from pathlib import Path
import json,re,html,hashlib,shutil
root=Path('/Users/gcc/gaocc/project/revenge-memories');out=root/'actual/reports/dialogue-coverage-audit-20261026';p=out/'audit.json';d=json.loads(p.read_text());s=d['summary'];doc=(root/'docs2/完整台词汇总.md').read_text();esc=lambda x:html.escape(str(x))
d['source_sha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'docs2/完整台词汇总.md',root/'actual/data/campaign.json',*[root/f'actual/core/{n}.gd' for n in ['game_state','story_hub','chapter2_rules','chapter3_rules','chapter3_hub','chapter4_rules','chapter4_hub','chapter5_rules','chapter5_hub','chapter5_endings']]]}
design=doc.split('### 一、关键主线场景D00—D52',1)[1].split('### 二、战场对白',1)[0];campaign=json.loads((root/'actual/data/campaign.json').read_text());d['design_scene_comparison']=[]
for code in ['D00','D11','D12','D13','D21','D31','D32','D33','D41']:
 m=re.search(r'^#### '+code+r' [^\n]*\n(.*?)(?=^#### |\Z)',design,re.M|re.S);lines=[l for l in m[1].splitlines() if re.match(r'^[^：]{1,12}：',l)];norm=lambda t:re.sub(r'\s+','',t)
 runtime=campaign['scenes'][code];shared=sum(norm(r['speaker']+'：'+r['text']) in norm(m[1]) for r in runtime)
 d['design_scene_comparison'].append({'code':code,'design_spoken_lines':len(lines),'configured_pages':len(runtime),'exact_shared_pages':shared,'new_or_rewritten_pages':len(runtime)-shared})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
chapterrows=''.join(f'<tr><td>第{c["chapter"]}章</td><td>{c["main"]}关</td><td>{c["main_opening_victory_segments"]}</td><td>{c["segments_fully_in_document"]}</td><td>{c["main_opening_victory_segments"]-c["segments_fully_in_document"]}</td></tr>' for c in s['chapters'])
scenerows=''.join(f'<tr><td>{r["code"]}</td><td>{r["design_spoken_lines"]}</td><td>{r["configured_pages"]}</td><td>{r["exact_shared_pages"]}</td><td>{r["new_or_rewritten_pages"]}</td></tr>' for r in d['design_scene_comparison'])
siderows=''.join(f'<tr><td>{r["code"]}</td><td>{"已有运行稿" if r["has_current_battle_entry"] else "只有设计稿，无现行运行卡"}</td><td>{"常规开场、自动战后原句已收录" if r["has_current_battle_entry"] else "开场、自动战后现行原句未完整收录"}</td></tr>' for r in d['battles'] if r['side'])
missing=''
for file in ['actual/core/story_hub.gd','actual/core/chapter3_hub.gd','actual/core/chapter4_hub.gd','actual/core/chapter5_hub.gd']:
 rows=[r for r in d['hub_literals'] if r['file']==file];unlisted=[r for r in rows if not r['in_document']]
 missing+=f'<details><summary>{esc(Path(file).name)}：{len(rows)}条固定原文中缺{len(unlisted)}条</summary><div class="body"><ol>'+''.join(f'<li><p>{esc(r["literal"])}</p><small>{esc(r["file"])}:{r["line"]}</small></li>' for r in unlisted)+'</ol></div></details>'
battle=''
for r in d['battles']:
 if r['side']:continue
 body=''
 for key,phase in r['phases'].items():
  missinglines=phase['whole_document']['missing']
  body+='<h4>'+('开场' if key=='before' else '自动胜利后')+f' · {phase["whole_document"]["exact"]}/{phase["whole_document"]["total"]}条原句可在全文找到</h4>'
  for line in phase['text'].split('／'):body+=f'<p class="{"missing" if line in missinglines else "included"}">{esc(line)}</p>'
 battle+=f'<details><summary>{r["code"]} · '+('基础原句均有收录' if all(not v['whole_document']['missing'] for v in r['phases'].values()) else '有缺句或旧稿差异')+'</summary><div class="body">'+body+'</div></details>'
phone=''
for r in d['phone_text_differences']:
 body=''
 for key,v in r['fields'].items():
  body+=f'<h4>{esc(key)}</h4><div class="compare"><div><small>上次已确认安装包</small><p>{esc(v["installed"])}</p></div><div><small>当前源码</small><p>{esc(v["current"])}</p></div></div>'
 phone+=f'<details><summary>{r["code"]}</summary><div class="body">'+body+'</div></details>'
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>完整台词汇总覆盖审计 · 2026-10-26</title><style>
:root{color-scheme:dark}body{margin:0;background:#101922;color:#edf1f4;font:16px/1.85 system-ui,-apple-system,"PingFang SC",sans-serif}main{max-width:1180px;margin:auto;padding:35px 25px 70px}h1{font-size:29px;line-height:1.5}h2{font-size:23px;margin:40px 0 16px}h3{font-size:18px}p{margin:10px 0}a{color:#b1d9ff}a:focus-visible,summary:focus-visible{outline:none;box-shadow:0 0 0 5px #a9d5ff44;border-radius:5px}.box,details{background:#1b2935;border-radius:10px;margin:20px 0}.box{padding:22px 26px}small,.muted{color:#b3c4d1}nav{display:flex;flex-wrap:wrap;gap:12px}nav a{background:#203343;padding:7px 14px;border-radius:7px;text-decoration:none}table{width:100%;border-collapse:collapse}td,th{padding:12px 14px;border-bottom:1px solid #374752;text-align:left}th{color:#e2c987}summary{cursor:pointer;padding:18px 22px;font-weight:600}.body{padding:0 22px 22px}h4{color:#dacba8;margin:22px 0 10px}.missing{color:#ffd8a5}.included{color:#bedac4}.compare{display:grid;grid-template-columns:1fr 1fr;gap:18px}.compare>div{padding:16px 20px;background:#13202c;border-radius:9px}li{margin:12px 0}.scroll{overflow:auto}footer{margin-top:40px;color:#b3c4d1}@media(max-width:760px){main{padding:24px 15px}.compare{grid-template-columns:1fr}td,th{padding:9px}h1{font-size:24px}}
</style><main><p class="muted">2026-10-26 · 只读分析</p><h1>《完整台词汇总》收录了什么，又漏了什么</h1><p>支线与战后台词已有部分收录。主要问题是旧设计、旧运行快照、近期补记混在同一文件中；它尚不能作为按玩家体验顺序阅读的现行完整台本。</p><div class="box"><p><b>当前游戏40关，文档现行运行卡只有23关。</b>第一、二、三章有卡；第四、五章17关已接入游戏，文档仍标“尚未接入”。</p><p>上一轮只同步第一章七关的战场字段和少数相关分支，没有完成全篇据点／招募／交接／关系／结局同步。序章、第一章及通用据点仍有28条可完整提取的固定对白／剧情提示未收录。</p></div>
<nav><a href="#scope">统计口径</a><a href="#main">主线差异</a><a href="#scenes">关键场景</a><a href="#side">支线与战后</a><a href="#hubs">据点缺漏明细</a><a href="#phone">上次手机包</a><a href="#recommendation">建议结构</a></nav>
<h2 id="scope">统计口径与限制</h2><p>本次比对文档、当前源码实际调用路径及上次已确认安装IPA内的数据；没有启动游戏、操作iPhone或执行新增实玩。以下“运行”指当前代码会读取的文本，不等于本轮逐句真机观看。</p><p>主线基础段落按每关“开场＋自动胜利后”各一段，共31关62段，计入第三章控制器追加的兵装线索，使用正常存活人物分支。第四、五章按控制器文本比对，没有把不被播放的JSON字段当作实机台词。战中全部事件、可选关系、装备交付和条件变体另列，未混入62段。</p><p>“完整收录”表示该基础段的每条原句都能在文档全文找到；不保证它们位于同一处或按实际顺序排列。“缺句／改写”不等于剧情方向全部相反，也不表示游戏没有对白。</p>
<h2 id="main">31关主线：62段中30段存在缺句或旧稿差异</h2><div class="scroll"><table><tr><th>章节</th><th>主线关数</th><th>开场＋胜利后段数</th><th>原句全部有收录</th><th>存在缺句／改写</th></tr>'''+chapterrows+'''<tr><th>合计</th><th>31关</th><th>62</th><th>32</th><th>30</th></tr></table></div>
<p>第一章10段刚同步；第二章12段的基础原句均可找到。第三章缺M33、F33开场追加的工房军械／魔剑线索。第四、五章28段均未完整同步，个别句子仍可在早期设计稿找到。</p><p>例如M44实际战后是“赫兰已失去指挥权。把伤兵交给照护处，我们回营站核对两岸结果。”；J54实际战后是神的实体倒下、循环仍运转、主角决定接船的三句。文档主要保留设计说明，没有同步成现行战后逐句稿。</p><h3>逐关基础原文</h3><p class="muted">绿色表示全文有原句，橙色表示全文找不到完整原句；不把同义概述算作逐句收录。</p>'''+battle+'''
<h2 id="scenes">关键主线场景：先区分第一部分“设计稿”和第四部分“运行稿”</h2><div class="scroll"><table><tr><th>场景</th><th>第一部分人物台词数</th><th>配置页数</th><th>共享原句</th><th>新增／改写页数</th></tr>'''+scenerows+'''</table></div>
<p>D31设计稿6句，实际配置14页，保留5句，另有9页新增／改写；D32由6句扩为12页；D33由5句扩为9页。这些扩写已收在第四部分，单读第一部分会误以为实机漏播或改了剧情。</p><p>campaign.json现有14组90页配置文字，全都能在文档某处找到；其中D22整组6页是保留的汇总数据，实际拆成首次交锋、败北与取箱事件，不能重复计算为玩家必看页数。D41的5句已经接入M44，却仍只在“设计”区；D42、D51、D52在章节控制器中触发，不能只检查campaign.json。</p>
<h2 id="side">9条支线与40关战后</h2><div class="scroll"><table><tr><th>支线</th><th>运行稿收录状态</th><th>基础文本</th></tr>'''+siderows+'''</table></div>
<p>战后应拆成两层：第一层是胜利自动播放，前三章23关的常规原句基本已收，第四、五章17关没有现行完整逐句稿；第二层是进入据点后主动交谈，包括招募、分粮、病人交接、工具、村民经历与关系事件，这一层缺漏明显。</p><p>典型旧稿：文档H08还写“工具不是开路的钥匙……”，实装已按是否取得工具分别说“工具也找回来了……”或“有些工具还落在洞里……”。S12实际有运药员、管理员、赫维三人的交接，文档控制器表仍是一句旧管理员说明。S41名册毁损、S42赛琳遇难的后果也只补了说明，没有逐句收齐。</p>
<h2 id="hubs">据点：242条可完整提取的固定对白／剧情提示中，104条未收录</h2><p>按原文去重后仍为242条，其中104条在文档全文均未找到。这里只统计四个据点控制器中能完整提取的固定句与分支句；动态姓名、数量拼接、兵装／饰品交付及后日谈未穷举，因此104不是全篇遗漏总量。</p>'''+missing+'''
<p>文档还把R02/R03/R06及18人后日谈标作待实现；实际已有条件触发和伤情／招募／关系变体。第三部分的后日谈主要是设计语义，并非当前结束字幕的逐字副本。</p>
<h2 id="phone">上次已确认安装的手机包与当前代码不同</h2><p>只读解包10月25日21:32批次IPA，包内PCK哈希与当次安装记录一致：<code>a02ab0f5…39674a</code>。这不是本轮对手机当前状态的重新确认。</p><p>该包的场景配置与当前campaign.json相同；40关起因／战场／缺席文字的不同集中在M11—M15、S11、S12七关，即刚完成而尚未更新手机的第一章改稿。因此，当前文档第一章战场部分比这次已确认安装包新；第四、五章和战后据点部分又比这个包旧。</p>'''+phone+'''
<h2 id="recommendation">建议的整理方式</h2><p>后续应将“现行逐句台本”独立放在前面，按玩家顺序记录：据点出发→开场→战中事件→胜利自动对白→战后据点→支线邀请／招募／交接→关系→章节收束／结局。每组附触发条件、分支和实际来源；不播放的设计说明明确另存，废弃旧句不继续标为当前。</p><p>优先补齐第一章战后据点，再同步第四、五章17关与结局，最后整理跨章关系、动态照护和物品交付。以实际调用路径为准，而不是只复制JSON的before/during/after。</p>
<p>证据：<a href="audit.json">完整比对数据</a> · <a href="../../../docs2/完整台词汇总.md">被审阅文档</a> · <a href="../iphone-install-20261025-213231/delivery.json">上次安装记录</a></p><footer>本轮只生成分析记录；未修改《完整台词汇总》、游戏源码或手机游戏。</footer></main></html>'''
(out/'index.html').write_text(page)
support=out/'_support';support.mkdir(exist_ok=True)
shutil.copy('/private/tmp/dialogue_audit_20261026.py',support/'audit.py');shutil.copy('/private/tmp/build_dialogue_audit_review.py',support/'build_review.py')
print(json.dumps({'review':str(out/'index.html'),'mainline_segments':62,'segments_with_missing_or_old_text':30,'fixed_hub_literals':242,'unlisted_fixed_literals':104,'phone_changed_battle_texts':s['installed_snapshot']['differing_stage_texts']},ensure_ascii=False))
