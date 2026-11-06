from pathlib import Path
import re,ast,json
ROOT=Path(__file__).resolve().parents[4]
def literals(s):
 out=[]
 for m in re.finditer(r'"(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27',s):
  try:out.append(ast.literal_eval(m.group()))
  except (ValueError,SyntaxError):pass
 return out
def split_args(s):
 out=[];start=0;depth=0;quote=None;escape=False
 for i,c in enumerate(s):
  if quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c==quote:quote=None
  elif c in ['"',"'"]:quote=c
  elif c in '([{':depth+=1
  elif c in ')]}':depth-=1
  elif c==',' and depth==0:out.append(s[start:i]);start=i+1
 out.append(s[start:]);return out
def calls(text):
 for m in re.finditer(r'(?<![\w.])((?:g\.)?queue_lines|lines)\(',text):
  depth=1;i=m.end();quote=None;escape=False
  while i<len(text) and depth:
   c=text[i]
   if quote:
    if escape:escape=False
    elif c=='\\':escape=True
    elif c==quote:quote=None
   elif c in ['"',"'"]:quote=c
   elif c=='(':depth+=1
   elif c==')':depth-=1
   i+=1
  args=split_args(text[m.end():i-1]);index=1 if m[1]=='lines' else 0
  if len(args)<=index:continue
  vals=[v for v in literals(args[index]) if '：' in v and len(v.split('：',1)[1])>2]
  if not vals:continue
  # Concatenated messages are transcribed with readable variables in the common appendix.
  if '+' in re.sub(r'"(?:\\.|[^"\\])*"','',args[index]):continue
  keyvals=literals(args[index+1]) if len(args)>index+1 else []
  yield {'key':keyvals[-1] if keyvals else '', 'texts':vals,'line':text[:m.start()].count('\n')+1,'expression':args[index].strip()}
def catalog():
 out=[]
 for n in ['game_state','chapter2_rules','chapter3_rules','chapter4_rules','chapter5_rules']:
  text=(ROOT/f'actual/core/{n}.gd').read_text()
  for row in calls(text):row['file']=n;out.append(row)
 return out
if __name__=='__main__':
 rows=catalog();(ROOT/'actual/reports/dialogue-complete-20261026/static-events.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 for i,r in enumerate(rows):print(i,r['file'],r['key'],r['texts'])
