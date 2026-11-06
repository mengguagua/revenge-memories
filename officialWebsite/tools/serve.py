"""Local static preview, with byte ranges for seeking and no exposed source files."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import mimetypes
import re

ROOT=Path(__file__).resolve().parents[1]
class WebsiteHandler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def send_head(self):
        relative=unquote(urlsplit(self.path).path).lstrip('/') or 'index.html'
        target=(ROOT/relative).resolve()
        if not target.is_relative_to(ROOT) or not (relative in {'index.html','styles.css','app.js','content.js','robots.txt','sitemap.xml'} or relative.startswith('assets/')) or not target.is_file():
            self.send_error(404,'File not found');return None
        compressed=False
        original_target=target
        if target.suffix in {'.html','.css','.js','.txt'} and 'gzip' in self.headers.get('Accept-Encoding',''):
            packed=Path(str(target)+'.gz')
            if packed.is_file() and packed.stat().st_mtime>=target.stat().st_mtime:
                target=packed;compressed=True
        f=target.open('rb');size=target.stat().st_size
        start,end=0,size-1
        range_header=self.headers.get('Range')
        if range_header:
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',range_header)
            if not match or not any(match.groups()):
                f.close();self.send_error(416,'Invalid range');return None
            first,last=match.groups()
            if not first:start=max(0,size-int(last))
            else:start=int(first);end=min(size-1,int(last)) if last else size-1
            if start>=size or start>end:
                f.close();self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
        self.send_response(206 if range_header else 200)
        self.send_header('Content-Type',mimetypes.guess_type(str(original_target))[0] or 'application/octet-stream')
        self.send_header('Content-Length',str(end-start+1))
        if original_target.suffix in {'.html','.css','.js','.txt'}:self.send_header('Vary','Accept-Encoding')
        if compressed:self.send_header('Content-Encoding','gzip')
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Cache-Control','no-cache' if original_target.suffix in {'.html','.css','.js'} else 'public, max-age=3600')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self'; media-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; base-uri 'self'; frame-ancestors 'none'")
        if range_header:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers();f.seek(start);self.remaining=end-start+1
        return f
    def copyfile(self,source,outputfile):
        remaining=getattr(self,'remaining',0)
        try:
            while remaining>0:
                chunk=source.read(min(256*1024,remaining))
                if not chunk:break
                outputfile.write(chunk);remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):pass
    def log_message(self,format,*args):
        if str(args[1] if len(args)>1 else '') not in {'200','206','304'}:super().log_message(format,*args)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=4173);parser.add_argument('--host',default='127.0.0.1');args=parser.parse_args()
    server=ThreadingHTTPServer((args.host,args.port),WebsiteHandler)
    print(f'Official website: http://localhost:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
