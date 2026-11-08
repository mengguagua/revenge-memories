#!/usr/bin/env python3
"""Read the bundled library; author in an explicit task-local workspace."""
from pathlib import Path
import argparse,shutil,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--library',type=Path,default=ROOT/'toolkit')
 parser.add_argument('command',choices=['list','render','act','check','new','workspace'])
 args,rest=parser.parse_known_args()
 library=args.library.expanduser().resolve()
 if args.command=='workspace':
  if len(rest)!=1:parser.error('workspace needs one destination directory')
  destination=Path(rest[0]).expanduser().resolve()
  if destination.exists():parser.error('Destination already exists; reuse it with --library')
  shutil.copytree(library,destination);print(destination);return 0
 if args.command=='new' and library==(ROOT/'toolkit').resolve():parser.error('Create a workspace first; the installed library stays immutable')
 if args.command in ['render','act']:
  if '--out' not in rest:parser.error('Supply --out <preview-directory>')
  i=rest.index('--out')
  if i+1>=len(rest):parser.error('--out needs a path')
  rest[i+1]=str(Path(rest[i+1]).expanduser().resolve())
 node=shutil.which('node')
 if not node:parser.error('Node 18+ is required')
 major=int(subprocess.check_output([node,'--version'],text=True).strip().lstrip('v').split('.')[0])
 if major<18:parser.error('Node 18+ is required')
 tool=library/'tools'/(args.command+'.mjs')
 if not tool.is_file():parser.error('Not a complete PixelFX library: '+str(library))
 return subprocess.run([node,str(tool),*rest],cwd=library).returncode
if __name__=='__main__':raise SystemExit(main())
