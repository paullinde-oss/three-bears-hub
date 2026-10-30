import sys; sys.path.insert(0,'tools')
from preview import *; from acc import *; from beard import make
import palettes as P
SKIN = P.SKIN
def dr(spec): return draw(spec[0], *spec[1])
NAVY=[(14,18,34),(30,40,70),(48,62,104),(70,88,136),(110,130,176)]
RED=[(40,10,10),(120,24,20),(170,44,30),(204,70,44),(232,120,90)]
def full(hairname, accs=(), beard=None, num=None, captain=False, capcol=None, skin='light', hairramp=HAIR, eye='normal', mouth='smile', brow='normal', eyecol='brown'):
    im=body_layer()
    if num is not None: number(num, im)
    if captain: over(im, dr(CAPTAIN))
    over(im,tint(H,SKIN[skin])); over(im,C)
    over(im,tintgray(draw(EYES[eye],*EYES_POS),P.EYES[eyecol]))
    if beard: over(im,tint(make(beard),hairramp))
    over(im,tintgray(draw(MOUTHS[mouth],*MOUTH_POS),SKIN[skin]))
    over(im,tintgray(draw(BROWS[brow],*BROWS_POS[brow]),hairramp))
    for e in ('earring_gold','earring_silver'):
        if e in accs: over(im,dr(EARRINGS[e]))
    if hairname:
        hl=np.load(f'parts/hair/{hairname}.npy')
        if 'cap' in accs or 'toque' in accs: hl=hl.copy(); hl[:21]=-1
        over(im,tint(hl,hairramp))
    for g in ('glasses','sunglasses'):
        if g in accs: over(im,dr(GLASSES[g]))
    if 'cap' in accs: over(im,tint(cap(),capcol or NAVY))
    if 'toque' in accs: over(im,tint(toque(),capcol or RED))
    return im
def sheet(looks, out):
    tiles=[]
    for lk in looks:
        im=full(**lk)
        full_t=Image.fromarray(im).resize((300,300),Image.NEAREST)
        crop=Image.fromarray(im).crop((18,6,58,52)).resize((240,276),Image.NEAREST)
        can=Image.new('RGB',(300,580),'white'); can.paste(crop,(30,0)); can.paste(full_t,(0,280)); tiles.append(can)
    s=Image.new('RGB',(300*len(tiles),580),'white')
    for k,t in enumerate(tiles): s.paste(t,(k*300,0))
    s.save(out)
if __name__=='__main__':
    looks=[dict(hairname='mullet',beard='short',num=7,captain=True),dict(hairname='messy',accs=('cap',),beard='stubble',num=99),
       dict(hairname='crew',accs=('glasses',),num=4),dict(hairname='short',accs=('sunglasses','earring_gold'),beard='goatee',num=22),
       dict(hairname='curly',accs=('toque',),beard='full',num=16),dict(hairname=None,beard='full',num=41,skin='brown',mouth='grin')]
    sheet(looks,'looks1.png')
