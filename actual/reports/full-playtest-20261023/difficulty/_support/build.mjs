import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const out=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..');
const payload=JSON.parse(await fs.readFile(path.join(out,'_support/datasets.json'),'utf8'));
const wb=Workbook.create();
const summary=wb.worksheets.add('难度概览');
const colors={ink:'#24334A',header:'#334766',light:'#EDF1F6',accent:'#6C7C93',warning:'#FFF0D5'};
const sheets={};
const col=i=>{let s='';for(i++;i;i=Math.floor((i-1)/26))s=String.fromCharCode(65+(i-1)%26)+s;return s;};
const q=s=>"'"+s+"'";
const start=7;
function formatBase(sheet,range){
  sheet.showGridLines=false;
  const r=sheet.getRange(range);r.format.font={name:'Helvetica Neue',size:11,color:colors.ink};
  r.format.verticalAlignment='center';r.format.rowHeight=24;
}
const widths={
 '40关难度':{0:8,1:10,2:23,3:10,4:10,21:24,22:62,23:96,24:40,25:13,26:17,27:16,28:34,29:75,30:26,31:34,32:105,33:135},
 '敌军明细':{0:8,1:10,2:15,3:13,4:24,5:22,6:18,18:18,19:48,20:22,21:18,22:18,23:20,24:74,25:58,39:110,40:100},
 '角色数值':{0:15,1:16,2:15,3:17,4:20,5:13,6:16,7:16,8:16,9:90,10:120},
 '职业基底':{0:10,1:20,2:20,11:25,12:110,13:100},
 '主角进阶':{0:14,1:20,2:32,3:12,4:20,5:16,6:16,7:90,8:90,9:105},
 '装备对比':{0:11,1:19,2:20,3:20,16:31,17:110,18:48,19:95,20:115},
 '外传80图':{0:15,1:25,2:12,3:14,17:28,18:45,19:110,20:90},
 '机制差异':{0:24,1:64,2:92,3:84,4:88,5:110}
};
const notes={
 '40关难度':'敌军累计上限包含条件增援，提前通关或切断投送可减少。平均属性只统计初始敌军。',
 '敌军明细':'数量上限用于事件/能力模板。伤害为无暴击、无克制、无追击的单次命中，对生命52、双防10、速度/幸运/回避0的标准目标。',
 '角色数值':'按 source_character 映射比较首次入队定义。差值=当前−外传；成长率差为百分点。ID/位标志的差值不代表强弱。',
 '职业基底':'共用转职/构造基底表数值保持。玩家初始属性与个人成长看角色数值；关卡敌军覆盖值看敌军明细。',
 '主角进阶':'当前进阶补足最低值，保留较高属性、等级、经验与当前HP。艾琳没有等价的原版公主最低属性，原值留空。',
 '装备对比':'同 item_id 的源数值比较。原17/18号 hp_cost=129为源权限标志，不是实际129HP消耗。新增59–66号没有原版等价物。',
 '外传80图':'原版地图默认部署的独立参考表。地图、游军、洞窟重复遭遇与当前40关并不一一对应，不比较“同关难度百分比”。',
 '机制差异':'区分源数值、当前运行规则与任务压力。没有据此调整职业、武器、敌军或成长数值。'
};
for(const [name,{headers,rows}] of Object.entries(payload.data)){
  const s=wb.worksheets.add(name);sheets[name]=s;const last=start+rows.length-1;
  formatBase(s,`A1:${col(headers.length-1)}${last}`);
  s.getRange('A2').values=[[name]];s.getRange('A2').format.font={name:'Helvetica Neue',size:15,bold:true,color:colors.ink};
  s.getRange(`A3:${col(Math.min(headers.length-1,7))}3`).format.borders={bottom:{style:'thin',color:colors.accent}};
  s.getRange('A4').values=[[notes[name]]];s.getRange('A4').format.font={italic:true,color:colors.accent,size:11};
  s.getRange(`A6:${col(headers.length-1)}${last}`).values=[headers,...rows];
  const table=s.tables.add(`A6:${col(headers.length-1)}${last}`,true,`Data${Object.keys(sheets).length}`);table.showFilterButton=true;
  s.getRange(`A6:${col(headers.length-1)}6`).format={fill:colors.header,font:{name:'Helvetica Neue',size:11,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',rowHeight:45,wrapText:true};
  s.getRange(`A7:${col(headers.length-1)}${last}`).format.rowHeight=name==='机制差异'?72:29;
  for(let i=0;i<headers.length;i++){
    const r=s.getRange(`${col(i)}6:${col(i)}${last}`);r.format.columnWidth=widths[name]?.[i]??15;
    const sample=rows.map(r=>r[i]).filter(v=>v!==null&&v!==undefined&&v!=='');
    const numeric=sample.length&&sample.every(v=>typeof v==='number');
    s.getRange(`${col(i)}7:${col(i)}${last}`).format.horizontalAlignment=numeric?'right':'left';
    if(numeric)s.getRange(`${col(i)}7:${col(i)}${last}`).setNumberFormat(sample.some(v=>!Number.isInteger(v))?'0.00':'0');
  }
  // Long objectives, conditions and citations must stay visible when neighbouring cells contain data.
  const textUnits=t=>[...String(t)].reduce((n,c)=>n+(c.charCodeAt(0)>255?2:1),0);
  const wrapped={
    '40关难度':[21,22,23,24,28,29,30,31,32,33], '敌军明细':[19,24,25,39,40],
    '角色数值':[9,10], '职业基底':[12,13], '主角进阶':[7,8,9],
    '装备对比':[16,17,18,19,20], '外传80图':[18,19,20], '机制差异':[1,2,3,4,5]
  }[name];
  for(const c of wrapped)s.getRange(`${col(c)}7:${col(c)}${last}`).format.wrapText=true;
  for(let i=0;i<rows.length;i++){
    let lines=1;
    for(const c of wrapped)lines=Math.max(lines,Math.ceil(textUnits(rows[i][c]??'')/((widths[name]?.[c]??15)-3)));
    s.getRange(`A${start+i}:${col(headers.length-1)}${start+i}`).format.rowHeight=Math.max(29,lines*16+10);
  }
  s.freezePanes.freezeRows(6);s.freezePanes.freezeColumns(name==='角色数值'?2:2);
}
// Deltas calculate from the adjacent numeric source values; missing comparisons remain blank.
function delta(name,index,left,right){
  const s=sheets[name];for(let i=0;i<payload.data[name].rows.length;i++){
    const row=payload.data[name].rows[i];if(typeof row[left]==='number'&&typeof row[right]==='number')s.getRange(`${col(index)}${start+i}`).formulas=[[`=${col(left)}${start+i}-${col(right)}${start+i}`]];
  }
  const r=s.getRange(`${col(index)}${start}:${col(index)}${start+payload.data[name].rows.length-1}`);
  r.conditionalFormats.add('cellIs',{operator:'notEqual',formula:0,format:{fill:colors.warning,font:{bold:true,color:'#7B4C0A'}}});
}
delta('角色数值',8,7,6);
delta('主角进阶',6,5,4);
// Enemy columns: current attributes and original imported-template fields.
for(const [d,a,b] of [[28,9,27],[30,10,29],[32,14,31],[34,12,33],[36,16,35],[38,17,37]])delta('敌军明细',d,a,b);
for(const [d,a,b] of [[6,5,4],[9,8,7],[12,11,10],[15,14,13]])delta('装备对比',d,a,b);
// Correct resistance deltas use bare source resistance, not equipment-added defence.
// Deployed enemy accessories in this snapshot do not change magic defence; checked in extraction.
const chars=payload.data['角色数值'].rows;
for(let i=0;i<chars.length;i++)sheets['角色数值'].getRange(`G${start+i}:I${start+i}`).setNumberFormat(chars[i][5]==='百分比'?'0%':'0');
const stageSheet=sheets['40关难度'];const enemyEnd=start+payload.data['敌军明细'].rows.length-1;
const er=c=>`${q('敌军明细')}!$${c}$7:$${c}$${enemyEnd}`;
for(let i=0;i<payload.data['40关难度'].rows.length;i++){
  const r=start+i;
  stageSheet.getRange(`F${r}:I${r}`).formulas=[[
    `=SUMIFS(${er('D')},${er('B')},B${r},${er('C')},"初始")`,
    `=SUMIFS(${er('D')},${er('B')},B${r},${er('C')},"固定增援")`,
    `=SUMIFS(${er('D')},${er('B')},B${r},${er('C')},"事件波次")+SUMIFS(${er('D')},${er('B')},B${r},${er('C')},"能力召唤")`,
    `=SUM(F${r}:H${r})`
  ]];
  for(const [d,c]of [['J','I'],['K','J'],['M','K'],['N','P'],['O','Q'],['P','M'],['Q','R']])stageSheet.getRange(`${d}${r}`).formulas=[[`=AVERAGEIFS(${er(c)},${er('B')},B${r},${er('C')},"初始")`]];
  stageSheet.getRange(`L${r}`).formulas=[[`=SUMIFS(${er('J')},${er('B')},B${r},${er('C')},"初始")`]];
}
stageSheet.getRange('J7:Q46').setNumberFormat('0.00');stageSheet.getRange('L7:L46').setNumberFormat('0');
stageSheet.getRange('Z7:AC46').format.fill='#FFF6E6';
stageSheet.getRange('AC7:AC46').conditionalFormats.add('containsText',{text:'待',format:{fill:'#FFF0D5',font:{color:'#8A5B16'}}});

formatBase(summary,'A1:J33');summary.tabColor=colors.header;
summary.getRange('A2').values=[['1–5章难度与外传数值对照']];summary.getRange('A2').format.font={name:'Helvetica Neue',size:15,bold:true,color:colors.ink};
summary.getRange('A3:J3').format.borders={bottom:{style:'thin',color:colors.accent}};
summary.getRange('A4').values=[['2026-10-24汇总。当前40关为自定义剧情遭遇，不与外传80地图硬配。只统计，不调整数值。']];summary.getRange('A4').format.font={italic:true,color:colors.accent,size:11};
const sh=['章节','关卡数','初始敌军','固定增援上限','事件/能力上限','累计敌军上限','平均初始生命','平均初始力量','最大单击(双防10)'];
summary.getRange('A6:I11').values=[sh,...payload.stats.chapters];
summary.getRange('A6:I6').format={fill:colors.header,font:{bold:true,color:'#FFFFFF',size:11},rowHeight:45,wrapText:true,horizontalAlignment:'center'};
summary.getRange('A7:I11').format.rowHeight=32;summary.getRange('B7:I12').format.horizontalAlignment='right';summary.getRange('G7:H11').setNumberFormat('0.00');
for(let i=0;i<5;i++){
  const r=7+i,st=q('40关难度');
  summary.getRange(`B${r}:F${r}`).formulas=[[
    `=COUNTIFS(${st}!$A$7:$A$46,A${r})`,
    ...['F','G','H','I'].map(c=>`=SUMIFS(${st}!$${c}$7:$${c}$46,${st}!$A$7:$A$46,A${r})`)
  ]];
  summary.getRange(`G${r}:H${r}`).formulas=[[
    `=AVERAGEIFS(${er('J')},${er('A')},A${r},${er('C')},"初始")`,
    `=AVERAGEIFS(${er('K')},${er('A')},A${r},${er('C')},"初始")`
  ]];
}
summary.getRange('A12').values=[['合计']];summary.getRange('B12:F12').formulas=[['=SUM(B7:B11)','=SUM(C7:C11)','=SUM(D7:D11)','=SUM(E7:E11)','=SUM(F7:F11)']];summary.getRange('A12:I12').format={fill:colors.light,font:{bold:true},rowHeight:30};
summary.getRange('A15').values=[['可直接比较的结论']];summary.getRange('A15').format.font={bold:true,size:13};
const findings=[
 ['装备数值','六兵装、两饰品沿用相同ID源数值。引光剑使用者由阿尔姆改为艾琳，取得条件均按当前剧情。'],
 ['角色差异','18名源角色映射可核对。罗恩换为弓手并重配基础属性；诺娅6项成长概率变化，其他17人成长概率保持。'],
 ['主角进阶','胡纳普最低属性与原勇者相同，移动5→6。艾琳新增最低属性与攻击法术减耗，移动4→5。'],
 ['终战观察','护途盾使最低进阶艾琳达21物防/23魔防，J54首领半血两类单击均为1。此为组合风险，未据此调数值。'],
 ['统计限制','累计483为所有条件部署的理论上限；F44切断投送、召唤者提前退场、容量限制或提前胜利会降低实际出现数。'],
 ['实玩结果','40关均胜利，43次完整尝试（2次战败重试、1次脚本停滞重跑）。成功流程新濒死6人次，NPC损失2人。使用真实历史检查点，非新档单次连续五章通关。']
];
summary.getRange('A17:B22').values=findings;
summary.getRange('A17:A22').format.font={bold:true};summary.getRange('B17:B22').format.wrapText=true;summary.getRange('A17:B22').format.rowHeight=58;
summary.getRange('A25').values=[['阅读口径']];summary.getRange('A25').format.font={bold:true,size:13};
summary.getRange('A27:B29').values=[['原版关卡','80地图独立列示。当前关卡没有原版地图对应元数据，禁止把阶段/编号相似当作同关。'],['敌军差值','只在原始模板和职业一致时给差值。等级改动会单独提示。换职业模板留空，不伪造同级对比。'],['数值单位','属性为点，移动/射程为格，成长概率为百分比。空白代表无可靠对应，不是0。']];
summary.getRange('A27:A29').format.font={bold:true};summary.getRange('B27:B29').format.wrapText=true;summary.getRange('A27:B29').format.rowHeight=58;
summary.getRange('A1:A33').format.columnWidth=17;summary.getRange('B1:B33').format.columnWidth=29;
for(const c of ['C','D','E','F','G','H','I'])summary.getRange(`${c}1:${c}33`).format.columnWidth=18;
// Descriptive text spans empty cells using explicit presentation merges, while the analytical table remains unmerged.
for(const r of [...Array.from({length:6},(_,i)=>17+i),27,28,29])summary.mergeCells(`B${r}:I${r}`);

wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'final formula scan'});
await fs.writeFile(path.join(out,'_support/formula-scan.ndjson'),errors.ndjson);
const inspection=await wb.inspect({kind:'table',range:'难度概览!A6:I12',include:'values,formulas',tableMaxRows:7,tableMaxCols:9,maxChars:8000});
await fs.writeFile(path.join(out,'_support/summary-inspection.ndjson'),inspection.ndjson);
const renderRanges={
 '难度概览':'A1:I29','40关难度':'Z6:AG17','敌军明细':'A1:R15','角色数值':'A1:I18','职业基底':'A1:L16','主角进阶':'A1:G20','装备对比':'A1:Q14','外传80图':'A1:Q16','机制差异':'A1:D11'
};
await fs.mkdir(path.join(out,'_support/previews'),{recursive:true});
const renderOnly=process.env.RENDER_ONLY?.split(',');
for(const [name,range]of Object.entries(renderRanges)){
  if(renderOnly&&!renderOnly.includes(name))continue;
  const p=await wb.render({sheetName:name,range,scale:1.25,format:'png'});
  await fs.writeFile(path.join(out,'_support/previews',`${name}.png`),new Uint8Array(await p.arrayBuffer()));
}
const result=await SpreadsheetFile.exportXlsx(wb);await result.save(path.join(out,'1-5章难度与外传数值对照.xlsx'));
await fs.writeFile(path.join(out,'_support/build-check.json'),JSON.stringify({sheets:9,rows:Object.fromEntries(Object.entries(payload.data).map(([k,v])=>[k,v.rows.length])),formulaErrors:errors.ndjson,summary:summary.getRange('A7:I12').values},null,2));
console.log(JSON.stringify({output:path.join(out,'1-5章难度与外传数值对照.xlsx'),summary:summary.getRange('A7:I12').values,errors:errors.ndjson}));
