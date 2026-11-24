"""viewer: python view.py out.png -> side / front / back / left for every character"""
import sys
from PIL import Image
from engine import *
from source import Source, CHARS
from rigs import RIGS

def grid(rows, k=6, crop=(8, 20, 56, 60)):
    x0,y0,x1,y1=crop; cw,ch=(x1-x0)*k,(y1-y0)*k
    im=Image.new('RGBA',(cw*max(len(r) for r in rows),ch*len(rows)),(170,170,170,255))
    for j,r in enumerate(rows):
        for i,f in enumerate(r):
            t=Image.fromarray(f).crop(crop).resize((cw,ch),Image.NEAREST)
            im.alpha_composite(t,(i*cw,j*ch))
    return im

if __name__=='__main__':
    rows=[]
    for k in CHARS:
        s=Source(k); r=RIGS[k]
        rows.append([s.anims['Idle'][0], s.with_shadow(r.frame('Down')), s.with_shadow(r.frame('Up')), flip(s.anims['Idle'][0])])
    grid(rows).save(sys.argv[1])
