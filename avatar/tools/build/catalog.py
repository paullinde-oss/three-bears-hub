import sys; sys.path.insert(0,'tools')
from looks import *; import palettes as P
from PIL import ImageDraw
def flat(im):
    bg = Image.new('RGBA', (100, 100), (255, 255, 255, 255)); bg.alpha_composite(Image.fromarray(im)); return bg.convert('RGB')
def tile(lk, label, w=120):
    t=flat(full(**lk)).crop((20,6,58,50)).resize((w,int(w*44/38)),Image.NEAREST)
    can=Image.new('RGB',(w,t.height+16),'white'); can.paste(t,(0,0)); ImageDraw.Draw(can).text((3,t.height+2),label,fill='black'); return can
if __name__=='__main__':
    rows=[]
    hairs=['buzz','swept','messy','textured','slick','crew','wavy','short','curly_short','side_part','mullet','curly',None]
    rows.append([tile(dict(hairname=h,hairramp=P.HAIR['brown'],num=8),h or 'bald') for h in hairs])
    rows.append([tile(dict(hairname='textured',skin=s,hairramp=P.HAIR['dark_brown']),'skin: '+s) for s in P.SKIN]+
                [tile(dict(hairname='wavy',hairramp=r),'hair: '+k) for k,r in list(P.HAIR.items())[:7]])
    rows.append([tile(dict(hairname='crew',hairramp=r),'hair: '+k) for k,r in list(P.HAIR.items())[7:]]+
                [tile(dict(hairname='short',beard=b,hairramp=P.HAIR['dark_brown']),b) for b in ['stubble','short','full','goatee','mustache','chinstrap']]+
                [tile(dict(hairname='side_part',mouth=m),'mouth: '+m) for m in ['grin','smile','neutral','smirk']]+
                [tile(dict(hairname='crew',eye='wide',eyecol='blue'),'eyes: blue')])
    rows.append([tile(dict(hairname='crew',eye=e),'eyes: '+e) for e in ['normal','happy','narrow']]+
                [tile(dict(hairname='slick',brow=b),'brows: '+b) for b in ['normal','thick','angry','raised','thin']]+
                [tile(dict(hairname='messy',accs=a,capcol=P.GEAR[c]),' + '.join(a)+' '+c) for a,c in [(('cap',),'navy'),(('cap',),'red'),(('toque',),'orange'),(('toque',),'green'),(('glasses',),'grey'),(('sunglasses',),'grey')]]+
                [tile(dict(hairname='buzz',accs=('earring_gold',)),'earring')])
    W=max(sum(t.width for t in r) for r in rows); Hh=sum(max(t.height for t in r) for r in rows)
    sheet=Image.new('RGB',(W,Hh),'white'); y=0
    for r in rows:
        x=0
        for t in r: sheet.paste(t,(x,y)); x+=t.width
        y+=max(t.height for t in r)
    sheet.save(sys.argv[1])
