#!/usr/bin/env python3
"""Original FE2 epilogue strings, condition bytecode and reviewed Chinese.
Sources: bank004 L04B25E..L04B3EB/L04B7A2/L04BDC2; bank012 L0CB9E0.
"""
import json,re,sys
from pathlib import Path
from extract_opening import Source
ROOT=Path(__file__).resolve().parents[1]
SRC=Path('/private/tmp/fe2-analysis-20261012')
ENDING_ZH={
0:'安详地长眠着……',
1:'安详地长眠在{death_place}……',
2:'担任新生瓦伦西亚的宰相。作为阿尔姆一世国王的得力助手，为王国的重建竭尽心力。',
3:'担任新生瓦伦西亚的宰相。作为阿尔姆一世国王的得力助手，为王国的重建竭尽心力。',
4:'将米拉与多玛的两个教团合而为一，成为最高司祭。',
5:'加入王国骑士团，为瓦伦西亚的复兴而努力。',
6:'战争结束后，他向阿尔姆告别。此后，再没有人见过他的身影。',
7:'加入王国骑士团，为瓦伦西亚的复兴而努力。',
8:'与托宾争夺克莱尔的芳心，最终赢得了她的爱。他得意地说：“男人靠的不是长相，而是真心。”',
9:'因托宾战死而悲伤不已，终日借酒消愁。不知何时，他的脸上才能再现笑容……',
10:'失去心爱之人，虽然知道独行不适合自己，仍孤身踏上了旅途。',
11:'终于抵不过格雷的坚持，无奈地与他走到一起。“唉，明明我喜欢的是阿尔姆啊……”',
12:'“格雷这家伙，真是太任性了。”她埋怨着独自先她而去的格雷。',
13:'受托统率新生瓦伦西亚的骑士团。据说，最近迎娶了一位美丽的妻子。',
14:'受托统率新生瓦伦西亚的骑士团。然而，此后在与海盗的战斗中，失去了生命。',
15:'与波伊一起，在索菲亚的教会工作。',
16:'失去了总与自己拌嘴的波伊，她受到了不小的打击。',
17:'为了救助饱受创伤的人们，前往利盖尔。',
18:'据说，她爱上了一个任谁都想不到的人。那人究竟是谁，她只是微笑，不肯回答。',
19:'仍然整天与梅伊拌嘴。或许，对他们来说，这就是幸福吧。',
20:'梅伊先他而去，他才第一次认清自己的心意。然而，时间再也无法倒流。',
21:'与杰西等人一起，为建立一个新的国家而努力。',
22:'在基斯昔日的领地上，建立了一个新的国家。后来，人们开始称他为“沙漠佣兵王”。',
23:'应阿尔姆的请求，向年轻的士兵们传授战斗技巧。',
24:'脱下铠甲，成为克莱贝的妻子。传说中的女骑士玛蒂尔达，她的名字，将永远铭刻在瓦伦西亚的历史之中。',
25:'失去克莱贝后，她不得不接掌骑士团。传说中的女骑士玛蒂尔达，她的名字，将永远铭刻在瓦伦西亚的历史之中。',
26:'为保护村庄免受盗贼侵袭，担任自卫团的团长。',
27:'找回弟弟妹妹之后，回到了山之村。听说，现在的他又像从前一样，做起了伐木工。',
28:'在基斯昔日的领地上，建立了一个新的国家。后来，人们开始称他为“沙漠佣兵王”。',
29:'姐姐玛拉与赫丝缇被献祭给多玛，转生为魔女……对于牺牲了三个女儿的父亲朱达，索妮娅绝不会原谅。',
30:'战争结束之后，他和勇者剑一起，忽然消失得无影无踪。据传，他为了寻找新的战斗，渡海前往了南方大陆。',
31:'参与杰西建立王国的事业。他的身旁，依偎着一位美丽的妻子。',
32:'与美丽的妻子一起，为瓦伦西亚王国的复兴而努力。',
33:'认为自己的魔力还远未成熟，于是渡海前往另一片大陆。',
34:'封印了自己的魔法，以一名普通女子的身份，幸福地生活着。',
35:'一边祈祷吉克的记忆不要恢复，一边与他幸福地生活着。',
36:'失去了最爱的人，她悲痛万分，剪去头发。此后，听说她一直为那些因战火而无家可归的孩子们奔走。',
37:'平安救出艾丝特之后，留下灿烂的笑容，返回了故乡。',
38:'失去了姐妹，将悲伤藏在心底，返回了故乡。',
39:'怀着守护了妹妹们的喜悦，振翅飞向阿卡内亚。',
40:'“对不起，帕奥拉，事情竟会变成这样……”\n“没关系，别放在心上，赛莉卡。失去妹妹，是我自己的责任……”\n帕奥拉将悲伤藏在心中，飞向故乡。',
41:'“我一定还会再来！谢谢大家！”艾丝特总是那么开朗。',
42:'“姐姐……”艾丝特想起为自己而死的姐姐，流下了眼泪。',
43:'在激烈的战斗中，他已经恢复了记忆。可是，是为了深爱自己的蒂塔，还是因为那段过去太过悲惨？他始终不愿多说……',
44:'后来，她与阿尔姆结为夫妻，成为瓦伦西亚的第一位王后。\n凭借温柔与聪慧，她辅佐年轻的国王，奠定了瓦伦西亚王国的根基。\n据说，人们相信她是米拉的转世，始终发自内心地爱戴着她。',
45:'后世的人们如此传颂：\n斩断诸神邪恶的锁链，建立我等千年王朝之人——\n永远不要忘记，我们的圣王，阿尔姆一世！',
}
NARRATION_ZH=['就这样，这场大战落下了帷幕。','付出了无数牺牲之后，如今，瓦伦西亚终于迎来了和平。','这场战争，究竟意味着什么？','没有人能够回答这个问题。','唯一可以确定的是……','当人类再一次变得傲慢自大……','新的战火便会燃起，焚尽大地……','直到一切都化为乌有。','或许，最可怕、最丑陋的东西……','恰恰就存在于人类的内心之中。','']
GOD_ZH=['到此为止吧……','勇者阿尔姆啊，我把一切都托付给你。','继承我们兄妹的意志，治理这片土地……','以多玛的力量和米拉的爱，正确地引导人们。','绝不可再重蹈我们的覆辙。','也绝不可再一次，打扰我们的长眠……']

def main():
 s=Source(SRC); mapping={bytes.fromhex(k):v for k,v in [l.rstrip('\n').split('=',1) for l in (SRC/'jp.tbl').read_text().splitlines() if '=' in l]}
 def decode(raw):
  out='';i=0
  while i<len(raw):
   c=raw[i]
   if c==239:break
   if c==237:out+='\n';i+=1;continue
   if bytes(raw[i:i+2]) in mapping:out+=mapping[bytes(raw[i:i+2])];i+=2
   elif bytes([c]) in mapping:out+=mapping[bytes([c])];i+=1
   else:raise ValueError(f'Unmapped original text byte {c:02X}')
  return out
 def source_text(bank,label):
  strings=s.strings(bank,label)
  return '\n'.join(strings) if strings else decode(s.db(bank,label))
 first=re.findall(r'\.dw (\w+)',s.block(4,'L04B7A2'))[:31]
 second=re.findall(r'\.dw (\w+)',s.block(12,'L0CB9E0'))
 texts={str(i):{'id':i,'text_ja':source_text(bank,label),'text_zh':ENDING_ZH[i],'source':s.ref(bank,label)} for i,(bank,label) in enumerate([(4,l) for l in first]+[(12,l) for l in second])}
 assert len(texts)==46
 branches={};conditions=re.findall(r'\.dw (\w+)',s.block(4,'L04BDC2'))
 for character_id,label in enumerate(conditions,1):
  raw=s.db(4,label)
  if raw[0]==0:
   entry={'kind':'fixed','ending_id':raw[1],'conditions':[]}
  else:
   count=raw[0]&7;refs=raw[1:count+1];n=raw[count+1];patternbytes=raw[count+2:count+2+(n+1)//2];outcomes=raw[count+2+(n+1)//2:count+2+(n+1)//2+n+1]
   patterns=[]
   for b in patternbytes:patterns += [b>>4,b&15]
   entry={'kind':'dependent_survival','related_character_ids':[r&63 for r in refs],'rules':[{'living_mask':v,'ending_id':outcomes[j]} for j,v in enumerate(patterns[:n])],'default_ending_id':outcomes[-1],'mask_rule':'For related characters in order: first alive=>bit8, second alive=>bit4, third=>bit2, fourth=>bit1; unrecruited/dead count false.','conditions':[]}
  entry.update({'character_id':character_id,'raw':raw[:2] if raw[0]==0 else raw,'source':s.ref(4,label)}); branches[str(character_id)]=entry
 narr_labels=re.findall(r'\.dw (\w+)',s.block(4,'L04B78C'))
 narration=[{'text_ja':source_text(4,l),'text_zh':zh,'source':s.ref(4,l)} for l,zh in zip(narr_labels,NARRATION_ZH)]
 god_ja=decode(s.db(12,'L0CB92E')[9:]).strip().split('\n\n')
 assert len(god_ja)==len(GOD_ZH),(len(god_ja),god_ja)
 out={'schema_version':1,'source_commit':'956365ef33c63751e7afd03f05e600d7728549da','narration':narration,'final_words':[{'speaker':'duma','text_ja':ja,'text_zh':zh,'source':s.ref(12,'L0CB92E')} for ja,zh in zip(god_ja,GOD_ZH)],'texts':texts,'characters':branches,'display_order':s.db(4,'L04B160'),'selection':{'unrecruited':'Skip entirely (L04B25E carry/ending255).','dead':'Use ending1, prefix stored death map/location, regardless companion branches (persistent unit field4 ==255).','alive':'Evaluate fixed/dependent_survival entry.','death_location_map':s.db(4,'L04B295'),'provenance':[s.ref(4,'L04B25E'),s.ref(4,'L04B2DF'),s.ref(4,'L04B344'),s.ref(4,'L04B04F')]}}
 (ROOT/'data/ending_zh.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(f'Extracted {len(texts)} ending variants, {len(branches)} character conditions, {len(narration)} closing narration paragraphs, {len(god_ja)} final words')
if __name__=='__main__':main()
