"""Small offline 6502 routine runner for recovering authored FE2 effect frames.

Used only by extraction tools. No ROM or CPU implementation enters the game.
Implements the official integer CPU instructions, with mapper writes captured.
"""
class CPU:
    def __init__(self,rom):
        self.rom=rom[16:16+16*16384];self.mem=bytearray(65536);self.bank=5
        self.a=self.x=self.y=0;self.p=0x20;self.sp=0xff;self.pc=0;self.chr=23;self.hooks={}
    def read(self,a):
        a&=65535
        if a>=0xc000:return self.rom[15*16384+a-0xc000]
        if a>=0x8000:return self.rom[self.bank*16384+a-0x8000]
        return self.mem[a]
    def write(self,a,v):
        v&=255;a&=65535
        if a==0xa000:self.bank=v&15
        elif a in [0xb000,0xc000]:self.chr=v
        elif a<0x8000:self.mem[a]=v
    def word(self,a):return self.read(a)+256*self.read((a+1)&65535)
    def next(self):v=self.read(self.pc);self.pc=(self.pc+1)&65535;return v
    def nz(self,v):v&=255;self.p=(self.p&~130)|(128 if v&128 else 0)|(2 if not v else 0);return v
    def push(self,v):self.mem[256+self.sp]=v&255;self.sp=(self.sp-1)&255
    def pop(self):self.sp=(self.sp+1)&255;return self.mem[256+self.sp]
    def addr(self,m):
        if m=='imm':a=self.pc;self.pc+=1;return a
        if m=='z':return self.next()
        if m=='zx':return (self.next()+self.x)&255
        if m=='zy':return (self.next()+self.y)&255
        if m=='ix':z=(self.next()+self.x)&255;return self.read(z)+256*self.read((z+1)&255)
        if m=='iy':z=self.next();return (self.read(z)+256*self.read((z+1)&255)+self.y)&65535
        a=self.next()+256*self.next()
        return (a+(self.x if m=='ax' else self.y if m=='ay' else 0))&65535
    def compare(self,a,v):r=a-v;self.p=(self.p&~1)|(1 if r>=0 else 0);self.nz(r)
    def call(self,bank,address,limit=200000):
        self.bank=bank;self.mem[0x2f]=bank;self.pc=address;self.sp=255;self.push(0x4f);self.push(0xff)
        for n in range(limit):
            if self.pc==0x5000:return n
            hook=self.hooks.get((self.bank,self.pc),self.hooks.get(self.pc))
            if hook:
                hook(self);self.pc=self.pop()+256*self.pop()+1;continue
            self.step()
        raise RuntimeError(f'CPU routine timeout at bank{self.bank:02X}:{self.pc:04X}')
    def step(self):
        pos=self.pc;op=self.next()
        if op in LOAD:
            r,m=LOAD[op];setattr(self,r,self.nz(self.read(self.addr(m))));return
        if op in STORE:r,m=STORE[op];self.write(self.addr(m),getattr(self,r));return
        if op in ALU:
            kind,m=ALU[op];v=self.read(self.addr(m))
            if kind=='ora':self.a=self.nz(self.a|v)
            elif kind=='and':self.a=self.nz(self.a&v)
            elif kind=='eor':self.a=self.nz(self.a^v)
            elif kind in ['adc','sbc']:
                v=v if kind=='adc' else v^255;r=self.a+v+(self.p&1)
                self.p=(self.p&~65)|(1 if r>255 else 0)|(64 if (~(self.a^v)&(self.a^r)&128) else 0);self.a=self.nz(r)
            elif kind=='cmp':self.compare(self.a,v)
            elif kind=='cpx':self.compare(self.x,v)
            elif kind=='cpy':self.compare(self.y,v)
            elif kind=='bit':self.p=(self.p&~194)|(v&192)|(2 if not self.a&v else 0)
            return
        if op in MODIFY:
            kind,m=MODIFY[op];a=None if m=='acc' else self.addr(m);v=self.a if a is None else self.read(a);carry=self.p&1
            if kind=='inc':v+=1
            elif kind=='dec':v-=1
            elif kind in ['asl','rol']:self.p=(self.p&~1)|(v>>7);v=(v<<1)|(carry if kind=='rol' else 0)
            elif kind in ['lsr','ror']:self.p=(self.p&~1)|(v&1);v=(v>>1)|(carry<<7 if kind=='ror' else 0)
            v=self.nz(v)
            if a is None:self.a=v
            else:self.write(a,v)
            return
        if op in BRANCH:
            mask,setbit=BRANCH[op];v=self.next();v=v-256 if v>=128 else v
            if bool(self.p&mask)==setbit:self.pc=(self.pc+v)&65535
            return
        if op==0x20:
            a=self.next()+256*self.next();r=self.pc-1;self.push(r>>8);self.push(r);self.pc=a
        elif op==0x60:self.pc=self.pop()+256*self.pop()+1
        elif op==0x4c:self.pc=self.next()+256*self.next()
        elif op==0x6c:a=self.next()+256*self.next();self.pc=self.read(a)+256*self.read((a&0xff00)|((a+1)&255))
        elif op==0x48:self.push(self.a)
        elif op==0x68:self.a=self.nz(self.pop())
        elif op==0x08:self.push(self.p|0x30)
        elif op==0x28:self.p=self.pop()|0x20
        elif op==0xaa:self.x=self.nz(self.a)
        elif op==0xa8:self.y=self.nz(self.a)
        elif op==0x8a:self.a=self.nz(self.x)
        elif op==0x98:self.a=self.nz(self.y)
        elif op==0xba:self.x=self.nz(self.sp)
        elif op==0x9a:self.sp=self.x
        elif op==0xe8:self.x=self.nz(self.x+1)
        elif op==0xca:self.x=self.nz(self.x-1)
        elif op==0xc8:self.y=self.nz(self.y+1)
        elif op==0x88:self.y=self.nz(self.y-1)
        elif op in [0x18,0x38,0x58,0x78,0xb8,0xd8,0xf8]:
            mask={0x18:1,0x38:1,0x58:4,0x78:4,0xb8:64,0xd8:8,0xf8:8}[op]
            self.p=(self.p|mask) if op in [0x38,0x78,0xf8] else self.p&~mask
        elif op==0xea:pass
        else:raise RuntimeError(f'Unsupported opcode {op:02X} bank{self.bank:02X}:{pos:04X}')

LOAD={};STORE={};ALU={};MODIFY={}
def add(table,kind,ops,modes):
    for op,mode in zip(ops,modes.split()):table[op]=(kind,mode)
MODES='imm z zx a ax ay ix iy'
add(LOAD,'a',[0xa9,0xa5,0xb5,0xad,0xbd,0xb9,0xa1,0xb1],MODES)
add(LOAD,'x',[0xa2,0xa6,0xb6,0xae,0xbe],'imm z zy a ay')
add(LOAD,'y',[0xa0,0xa4,0xb4,0xac,0xbc],'imm z zx a ax')
add(STORE,'a',[0x85,0x95,0x8d,0x9d,0x99,0x81,0x91],'z zx a ax ay ix iy')
add(STORE,'x',[0x86,0x96,0x8e],'z zy a');add(STORE,'y',[0x84,0x94,0x8c],'z zx a')
for kind,base in [('ora',0),('and',0x20),('eor',0x40),('adc',0x60),('cmp',0xc0),('sbc',0xe0)]:add(ALU,kind,[base+v for v in [9,5,21,13,29,25,1,17]],MODES)
add(ALU,'cpx',[0xe0,0xe4,0xec],'imm z a');add(ALU,'cpy',[0xc0,0xc4,0xcc],'imm z a');add(ALU,'bit',[0x24,0x2c],'z a')
for kind,base in [('asl',0),('rol',0x20),('lsr',0x40),('ror',0x60)]:add(MODIFY,kind,[base+v for v in [10,6,22,14,30]],'acc z zx a ax')
add(MODIFY,'inc',[0xe6,0xf6,0xee,0xfe],'z zx a ax');add(MODIFY,'dec',[0xc6,0xd6,0xce,0xde],'z zx a ax')
BRANCH={0x10:(128,False),0x30:(128,True),0x50:(64,False),0x70:(64,True),0x90:(1,False),0xb0:(1,True),0xd0:(2,False),0xf0:(2,True)}
