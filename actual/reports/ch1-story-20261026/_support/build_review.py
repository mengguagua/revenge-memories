from pathlib import Path
import json, hashlib, html, struct
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'actual/reports/ch1-story-20261026'
BASE = OUT / 'before'
CODES = ['M11','M12','M13','M14','M15','S11','S12']
def load(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def esc(t): return html.escape(str(t))
def lines(t):
    return ''.join('<p>'+esc(line)+'</p>' for line in str(t).split('／'))
def png_info(p):
    raw=p.read_bytes(); return {'path':str(p.relative_to(ROOT)), 'pixels':list(struct.unpack('>II',raw[16:24])), 'bytes':len(raw), 'sha256':digest(p)}
checks=load(OUT/'checks.json'); visual=load(OUT/'visual-checks.json')
play_path=ROOT/'actual/reports/full-playtest-20261023/ch1/story-M12-20261026/story-M12-20261026-play.json'
play=load(play_path); battle=play['battles'][0]
assert checks['passed'] and visual['passed'] and play['passed']
assert len(checks['checks'])==178 and len(visual['checks'])==385 and visual['dialogue_pages']==99
stats=load(OUT/'stat-changes.json'); asset=load(OUT/'portrait-asset.json')
(OUT/'portrait-prompt.txt').write_text('Mode: built-in image_gen\n\n'+asset['prompt']+'\n\nReferences: actual/assets/portraits-0.5.0/west_infantry.png and korlan.png, style only.\nRuntime: 48×48 logical pixels; 40 colors; nearest-neighbour derivative, then lossless oxipng.\nOriginal is preserved under source/ch1-story-20261026/ with .gdignore.\n')
asset['prompt_record']='actual/reports/ch1-story-20261026/portrait-prompt.txt'
asset['sha256']=digest(Path(asset['runtime_path']))
(OUT/'portrait-asset.json').write_text(json.dumps(asset,ensure_ascii=False,indent=2)+'\n')
shots=[png_info(OUT/n) for n in ['M12-before-0.png','M12-before-5.png','M12-before-11.png','M12-commander-status.png']]
manifest=[dict(png_info(Path(asset['runtime_path'])), usage='M12指挥官状态／对白画像', quality='原生48×48像素；不透明蓝底与现有画像一致；无需透明边缘处理。')]
manifest += [dict(s,usage='后台手机比例运行截图',quality='原始2556×1179尺寸保留，PNG无损压缩。') for s in shots]
(OUT/'image-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
changes=load(OUT/'changes.json'); files={}
for name,old_hash in changes['baseline_files'].items():
    assert digest(BASE/name)==old_hash, name
    files[name]={'baseline_sha256':old_hash,'current_sha256':digest(ROOT/name)}
# All story text in the live stage records must appear verbatim in the current dialogue collection.
doc=(ROOT/'docs2/完整台词汇总.md').read_text(); synchronized=0; stage_keys={}
for code in CODES:
    path=Path(f'actual/data/stages/{code}.json'); now=load(ROOT/path); before=load(BASE/path)
    stage_keys[code]=[k for k in now if now[k]!=before.get(k)]
    allowed={'cause','before','during','after','after_no_survivors','absent_branch','dialogue_require_speaker_alive'}
    if code=='M12': allowed|={'enemies','combat_balance_revision'}
    assert set(stage_keys[code]) <= allowed,(code,stage_keys[code])
    for key in ['cause','before','during','after','after_no_survivors','absent_branch']:
        for line in now.get(key,'').split('／'):
            if not line:continue
            assert line in doc,(code,key,line)
            synchronized+=1
# The ordinary-input play used the same enemy stats, deployment, objectives and artwork.
played_stage=load(ROOT/'actual/data/stages/M12.json')
for entry in battle['initial_enemies']:
    current=next(u for u in played_stage['enemies'] if u['id']==entry['id'])
    for key in ['level','max_hp','strength','skill','speed','defence','position','item_id']:
        assert current[key]==entry[key],(entry['id'],key)
limits=['本轮未导出iPhone安装包，也未安装、更新或启动手机游戏。',
        '运行画面为防抢焦点脚本生成的后台Godot视口；2556×1179，使用现有iPhone安全区。未执行真机触摸试玩。',
        '七关完成了对白与布局检查；正常输入通关仅复测M12，使用既有历史部署队伍，不代表首周目或真人难度。',
        '旧档迁移定向检查覆盖当前地图单位的伤势、死亡与重复读取，不代表所有历史地图版本。正在播放的已存对白保持原队列，后续事件使用新稿。',
        '后台呈现脚本退出时有8个ObjectDB实例和2个资源未释放的清理提示；检查正常完成，进程退出码0，无脚本错误。']
delivery={'date':'2026-10-26','status':'completed-local-source','numeric_scope':'M12 enemies only','story_scope':CODES,
          'phone_updated':False,'iphone_exported':False,'domain_checks':len(checks['checks']),
          'visual_checks':len(visual['checks']),'dialogue_pages':visual['dialogue_pages'],
          'document_fragments_verified':synchronized,'all_passed':True,
          'ordinary_input_play':{'stage':'M12','turns':battle['final_turn'],'inputs':play['total_inputs'],
            'outcome':battle['outcome'],'return_view':battle['return_view'],'source':battle['source'],
            'source_saves_modified':play['source_saves_modified'],'forced_victories':play['forced_victories'],
            'stat_edits':play['stat_edits'],'path':str(play_path.relative_to(ROOT)),
            'stage_prose_refinements_after_play':'M12 cause and after text clarified; enemy stats, map, geometry and goals unchanged.'},
          'changed_stage_keys':stage_keys,'files':files,'images':manifest,'limits':limits}
(OUT/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
labels={'cause':'起因','before':'开场','during':'途中事件','after':'战后','after_no_survivors':'无人存活投降分支','absent_branch':'人物缺席处理'}
story=''
for code in CODES:
    now=load(ROOT/f'actual/data/stages/{code}.json'); old=load(BASE/f'actual/data/stages/{code}.json')
    content=''
    for key,label in labels.items():
        if key not in now:continue
        content+=f'<h4>{label}</h4><div class="compare"><div><span class="tag">修改前</span>{lines(old.get(key,"此前无单独分支"))}</div><div><span class="tag new">当前稿</span>{lines(now[key])}</div></div>'
    story+=f'<details id="{code}" {"open" if code=="M12" else ""}><summary>{code} · {esc(now["name_zh"])}</summary><div class="details-body">{content}</div></details>'
rows=''
for u in stats['units']:
    old=u['before'];now=u['after'];name='指挥官' if u['id']=='M12_boss' else '焚毁兵' if u['id']=='M12_e1' else {'soldier':'士兵','archer':'弓手','mercenary':'佣兵'}[u['class']]
    cells=[u['id']+' '+name]
    for field in ['level','max_hp','strength','skill','speed','defence']:
        cells.append(str(old[field]) if old[field]==now[field] else f'{old[field]} → {now[field]}')
    rows+='<tr>'+''.join('<td>'+esc(c)+'</td>' for c in cells)+'</tr>'
captions=['主角团先说清来到粮站的目的','芙拉说明伤者不能挪动的原因','明确点火次数与失败条件','指挥官独立画像；生命已调整为29']
gallery=''.join(f'<figure><a href="{s["path"].split("/")[-1]}"><img loading="lazy" src="{s["path"].split("/")[-1]}" alt="{cap}"></a><figcaption>{cap} · {s["pixels"][0]}×{s["pixels"][1]} · {s["bytes"]:,} 字节</figcaption></figure>' for s,cap in zip(shots,captions))
nav=''.join(f'<a href="#{c}">{c}</a>' for c in CODES)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第一章剧情与 M12 反馈 · 2026-10-26</title>
<style>
:root{color-scheme:dark;--bg:#101820;--card:#1a2631;--muted:#b6c5d1;--accent:#e6c987}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#edf2f5;font:16px/1.8 system-ui,-apple-system,"PingFang SC",sans-serif}main{max-width:1240px;padding:42px 28px 70px;margin:auto}h1{font-size:30px;line-height:1.4}h2{font-size:23px;margin:45px 0 16px}h3{font-size:19px}h4{margin:25px 0 12px;color:var(--accent)}p{margin:9px 0}a{color:#a9d8ff;text-underline-offset:4px}a:focus-visible,summary:focus-visible{outline:none;box-shadow:0 0 0 5px #b2d9ff44;border-radius:5px}nav{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}nav a{padding:8px 16px;background:var(--card);border-radius:8px;text-decoration:none}.lead{font-size:18px;max-width:980px}.muted{color:var(--muted)}.box{background:var(--card);border-radius:12px;padding:22px 26px;margin:20px 0}.good{color:#a3d9b1}.compare{display:grid;grid-template-columns:1fr 1fr;gap:20px}.compare>div{padding:18px 22px;background:#141e28;border-radius:9px}.compare p{line-height:1.9}.tag{display:inline-block;color:var(--muted);font-size:13px;margin-bottom:9px}.new{color:#b1e5c1}details{background:var(--card);border-radius:10px;margin:18px 0;scroll-margin-top:20px}summary{cursor:pointer;padding:20px 24px;font-size:19px;font-weight:600}.details-body{padding:0 24px 24px}table{width:100%;border-collapse:collapse;font-size:15px}th,td{padding:13px 14px;text-align:left;border-bottom:1px solid #354452}th{color:var(--accent);white-space:nowrap}.scroll{overflow:auto}figure{margin:26px 0}figure img{display:block;width:100%;border-radius:7px}figcaption{padding:8px 1px;color:var(--muted);font-size:14px}.portrait{display:flex;flex-wrap:wrap;gap:28px;align-items:center}.portrait img{width:192px;height:192px;image-rendering:pixelated}.portrait p{max-width:780px}li{margin:9px 0}code{font-size:14px;color:#dfcfb1}footer{margin-top:42px;color:var(--muted);font-size:14px}blockquote{margin:18px 0;padding:15px 22px;background:#22313b;border-radius:8px;font-size:19px}@media(max-width:760px){main{padding:25px 16px}.compare{grid-template-columns:1fr}.details-body{padding:0 14px 18px}h1{font-size:25px}th,td{padding:10px}.box{padding:18px}}
</style><main>
<p class="muted">复仇与回忆 · 本地源码验收 · 2026-10-26</p><h1>第一章剧情衔接与 M12 反馈</h1>
<p class="lead">七关补齐主角团的来意、眼前遭遇与行动选择；维持“外传”短句、直白的说话节奏。敌军数值只调整 M12，增加指挥官单独画像，并把芙拉留守诊所的原因写进开场。</p>
<div class="box"><p>焚粮提示已改为：</p><blockquote>若敌方连续两次在粮仓门前点火，战斗失败。</blockquote><p class="muted">焚毁兵仍从第7回合出发；首次点火提示已说明“已点火一次”。失败规则保持原机制。</p></div>
<nav><a href="#screens">运行画面</a><a href="#stats">M12数值</a><a href="#portrait">指挥官画像</a><a href="#story">七关前后对照</a><a href="#checks">验证与边界</a></nav>
<h2>玩家能看到的剧情接续</h2>
<div class="scroll"><table><tr><th>关卡</th><th>来意 → 遭遇 → 主线推进</th></tr>
<tr><td>M11 流民林路</td><td>查丘堡守备 → 撞见追赶流民 → 先救人，再沿粮车与军令查科兰。</td></tr>
<tr><td>M12 丘堡粮站</td><td>问科兰车队 → 芙拉照护被打伤的老人、守军威胁焚粮 → 保粮、分粮，找到押送所线索。</td></tr>
<tr><td>M13 南岗押送所</td><td>找押送军令 → 听见囚犯求救、认识蕾娜 → 开牢救人，得知旧塔还有劳工。</td></tr>
<tr><td>M14 旧塔外营</td><td>依赫兰承诺进城 → 旧部拒认通路 → 控制哨卡、接受投降，查明北门撤离。</td></tr>
<tr><td>M15 海峡旧塔堡</td><td>拦科兰、问凯尔之死 → 看见劳工被抛下 → 先开内院，再阻止撤离，实际播放战后收束。</td></tr>
<tr><td>S11 旧矿道</td><td>应村民请求入矿 → 贝克因伤者不识岔路而留下 → 清路护送，工具按实际取得结果处理。</td></tr>
<tr><td>S12 林村诊所道路</td><td>寻找北去道路 → 遇见受阻药车与留守的赫维 → 先送药安置病人，再交接、邀请。</td></tr></table></div>
<p>原有墓前开局、赫兰合作、科兰败北 D13、日返与庆典据点流程继续衔接。M14守军全灭时改从撤离军令得知线索；未入队的芙拉、蕾娜遇难时，不让替代人物借用她们的私人经历。</p>
<p>同步文档：<a href="../../../docs2/完整故事剧情.md">完整故事剧情</a> · <a href="../../../docs2/完整台词汇总.md">完整台词汇总</a> · <a href="../../../docs2/完整游戏设定.md">完整游戏设定</a>。</p>
<h2 id="screens">手机比例运行画面</h2><p class="muted">Godot后台视口，现有iPhone安全区。点击查看原尺寸；对白、画像与边框安全间距已实际查看。</p>'''+gallery+'''
<h2 id="stats">只调整 M12 敌军</h2><div class="scroll"><table><tr><th>单位</th><th>等级</th><th>最大生命</th><th>力量</th><th>技巧</th><th>速度</th><th>物防</th></tr>'''+rows+'''</table></div>
<p>力量增加2，对应相同装备下的攻击增加2。指挥官属于士兵，也增加2生命；其铁枪装备后攻击仍为11。佣兵采用本关固定成长：等级1→2、生命+2、力量／技巧／速度／物防各+1；击败经验40→44。幸运、魔防、移动、射程、装备和掉落保持。</p>
<p class="muted">原敌军构造器每两级才给一档基础成长，直接改等级无法满足本次“增加对应数值”的要求，因此佣兵使用明确的关卡成长值。旧档只迁移已知旧值，保留伤势和死亡，不重复叠加；不在读取时新增敌人或移动单位。</p>
<h2 id="portrait">指挥官独立画像</h2><div class="box portrait"><img src="../../assets/portraits-ch1-20261026/m12-commander.png" alt="M12指挥官单独画像"><div><p>中年面貌、胡须与颊疤，铁盔配短脊和铜色额带，红围巾；与普通士兵区分。状态页与本关“指挥官”对白共用这一身份。</p><p>运行图48×48，40色，1,277字节。使用内置 <code>image_gen</code> 生成，参考现有士兵与科兰的像素风格，原图离线保留。</p><p><a href="../../assets/portraits-ch1-20261026/m12-commander.png">运行画像</a> · <a href="../../../source/ch1-story-20261026/commander-original.png">原始生成图</a> · <a href="portrait-prompt.txt">提示词记录</a> · <a href="portrait-asset.json">工具与素材记录</a></p></div></div>
<h2 id="story">七关逐句前后对照</h2><p class="muted">左侧为本次修改前的工作区文本，右侧为当前运行稿；并非用Git旧提交覆盖其他工作的结果。</p><nav>'''+nav+'''</nav>'''+story+'''
<h2 id="checks">验证结果与实际范围</h2><div class="box"><p class="good">178项规则／分支／存档检查通过；385项后台呈现检查通过，覆盖99页对白。</p><p>M12用既有历史部署记录正常输入通关：7回合，549次输入；继续完成分粮、邀请芙拉并返回大地图。没有强制胜利或修改战斗中的属性、随机状态、位置。</p><p>113条起因、台词与缺席说明已对照《完整台词汇总》确认一致。其他六关敌军、七关地图／部署／交互／目标未改。</p></div><ul>'''+''.join('<li>'+esc(t)+'</li>' for t in limits)+'''</ul>
<p>证据：<a href="checks.json">规则／分支／存档</a> · <a href="visual-checks.json">99页呈现检查</a> · <a href="../full-playtest-20261023/ch1/story-M12-20261026/story-M12-20261026-play.json">M12正常输入记录</a> · <a href="stat-changes.json">逐个敌人数值</a> · <a href="image-manifest.json">图片尺寸与字节数</a> · <a href="delivery.json">最终范围及文件哈希</a></p>
<footer>本轮只交付本地源码、同步文档与验收记录；手机游戏尚未更新。</footer></main></html>'''
(OUT/'index.html').write_text(page)
(OUT/'README.md').write_text('''# 第一章剧情与M12反馈 · 2026-10-26

[逐句对照、运行画面与验证记录](index.html)。

- 故事范围：M11、M12、M13、M14、M15、S11、S12。
- 数值范围：只改M12。六名士兵（包含指挥官）最大生命+2；两名弓手生命-2、力量+2；佣兵等级+1并增加本关固定成长。
- 新画像：`actual/assets/portraits-ch1-20261026/m12-commander.png`，48×48、1277字节。内置image_gen生成，完整要求记录见portrait-prompt.txt，工具与路径见portrait-asset.json；原始源图保留在工程source目录并使用.gdignore隔离。
- 芙拉留守是因为刚为被士兵打伤的老人包住腿伤，暂不能搬动。分粮后由医者接手，随后再邀请她同行。
- 《完整故事剧情》《完整台词汇总》《完整游戏设定》同步。113条运行文本对齐通过。

178项规则／分支／存档检查、385项后台呈现检查通过，实际渲染99页对白；保存4张代表性手机比例画面。仅M12完成普通输入复测，7回合549次输入，分粮、邀请和返回世界接续通过。使用既有历史部署队伍，没有强制胜利、改属性或随机状态。

本轮无iPhone导出、安装或真机触摸试玩，也未重跑完整第一章或全游戏。后台呈现结束有8个ObjectDB实例与2个资源未释放的清理提示，无脚本错误，退出码0。最终范围、版本哈希及限制见delivery.json。
''')
print(json.dumps({'review':str(OUT/'index.html'),'domain':len(checks['checks']),'visual':len(visual['checks']),'pages':visual['dialogue_pages'],'document_fragments':synchronized,'images':[{k:v for k,v in i.items() if k in ['path','pixels','bytes']} for i in manifest]},ensure_ascii=False))
