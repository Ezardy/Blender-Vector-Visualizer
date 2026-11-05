# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate matching SVG/PNG asset icons using only Python's standard library."""
from pathlib import Path
import math, struct, zlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'images' / 'icons'
SIZE = 256
SCALE = 2

class Canvas:
    def __init__(self, accent):
        self.accent=accent;self.svg=[];self.pixels=bytearray([19,25,38,255])*(SIZE*SCALE)**2
    def color(self,c):return tuple(bytes.fromhex(c.lstrip('#')))+(255,)
    def paint(self,bounds,inside,c):
        rgba=bytes(self.color(c));n=SIZE*SCALE
        x0,y0,x1,y1=bounds
        for y in range(max(0,int(y0*SCALE)),min(n,int(y1*SCALE)+1)):
            for x in range(max(0,int(x0*SCALE)),min(n,int(x1*SCALE)+1)):
                if inside((x+.5)/SCALE,(y+.5)/SCALE):
                    pos=(y*n+x)*4;self.pixels[pos:pos+4]=rgba
    def polygon(self,points,c):
        self.svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in points)}" fill="{c}"/>')
        def inside(x,y):
            odd=False
            for (ax,ay),(bx,by) in zip(points,points[1:]+points[:1]):
                if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:odd=not odd
            return odd
        self.paint((min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)),inside,c)
    def line(self,a,b,c,w=7):
        self.svg.append(f'<path d="M {a[0]} {a[1]} L {b[0]} {b[1]}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>')
        ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay;den=dx*dx+dy*dy;r=w/2
        def inside(x,y):
            t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/den)) if den else 0
            return (x-ax-t*dx)**2+(y-ay-t*dy)**2<=r*r
        self.paint((min(ax,bx)-r,min(ay,by)-r,max(ax,bx)+r,max(ay,by)+r),inside,c)
    def circle(self,p,r,c):
        x,y=p;self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>');self.paint((x-r,y-r,x+r,y+r),lambda a,b:(a-x)**2+(b-y)**2<=r*r,c)
    def arrow(self,a,b,c=None,w=8):
        c=c or self.accent;dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy);ux,uy=dx/length,dy/length
        base=(b[0]-ux*25,b[1]-uy*25);self.line(a,base,c,w);self.polygon([b,(base[0]-uy*12,base[1]+ux*12),(base[0]+uy*12,base[1]-ux*12)],c)
    def plane(self):
        self.polygon([(35,164),(160,207),(223,137),(98,97)],'#263447')
        for a,b in [((35,164),(160,207)),((160,207),(223,137)),((223,137),(98,97)),((98,97),(35,164))]:self.line(a,b,'#53657c',3)
    def png(self):
        data=bytearray();n=SIZE*SCALE
        for y in range(SIZE):
            data.append(0)
            for x in range(SIZE):
                for c in range(4):data.append(sum(self.pixels[((y*SCALE+dy)*n+x*SCALE+dx)*4+c] for dy in range(SCALE) for dx in range(SCALE))//(SCALE*SCALE))
        def chunk(t,p):return struct.pack('>I',len(p))+t+p+struct.pack('>I',zlib.crc32(t+p)&0xffffffff)
        return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',SIZE,SIZE,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(bytes(data),9))+chunk(b'IEND',b'')
    def save(self,name):
        (OUT/f'{name}.png').write_bytes(self.png())
        (OUT/f'{name}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256"><rect width="256" height="256" fill="#131926"/>'+''.join(self.svg)+'</svg>\n',encoding='utf-8')

def generate():
    OUT.mkdir(parents=True,exist_ok=True)
    c=Canvas('#64b5ff');c.arrow((54,196),(201,57));c.circle((54,196),12,'#e8f2ff');c.circle((54,196),6,'#131926');c.circle((201,57),7,'#e8f2ff');c.save('object-to-object')
    c=Canvas('#45d9de');c.plane();c.arrow((75,51),(184,89),'#91a1b6',6);c.line((75,51),(75,159),'#53657c',3);c.line((184,89),(184,186),'#53657c',3);c.arrow((75,159),(184,186));c.save('projection')
    c=Canvas('#ffae5a');c.arrow((44,117),(166,46),'#91a1b6',6);c.arrow((82,209),(204,138));c.circle((82,209),7,'#e8f2ff');c.line((74,209),(90,209),'#e8f2ff',3);c.line((82,201),(82,217),'#e8f2ff',3);c.save('parallel')
    c=Canvas('#61e69d');c.plane();c.arrow((128,163),(128,37));c.line((128,143),(146,149),'#e8f2ff',3);c.line((146,149),(146,168),'#e8f2ff',3);c.circle((128,163),6,'#e8f2ff');c.save('surface-normal')
    c=Canvas('#bc95ff');c.polygon([(42,212),(218,212),(218,42),(42,42)],'#202b3e');c.arrow((65,190),(216,190),'#91a1b6',5);c.arrow((65,190),(124,61),'#53657c',5);c.arrow((65,190),(65,47));c.line((65,167),(88,167),'#e8f2ff',3);c.line((88,167),(88,190),'#e8f2ff',3);c.save('perpendicular')
    c=Canvas('#ff81aa');c.plane();c.line((45,205),(208,48),'#91a1b6',6);c.circle((45,205),6,'#e8f2ff');c.circle((208,48),6,'#e8f2ff');c.circle((126,127),14,c.accent);c.circle((126,127),6,'#131926');c.line((103,127),(149,127),c.accent,3);c.line((126,104),(126,150),c.accent,3);c.save('segment-intersection')
    print(f'Generated six SVG and PNG icons in {OUT}')

if __name__=='__main__':generate()
