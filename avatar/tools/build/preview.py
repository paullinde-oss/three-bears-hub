import sys; sys.path.insert(0,'tools')
import numpy as np; from PIL import Image
from compose import *; from extract import classify; from feat import *
H=np.load('head_levels.npy'); C=np.load('collar.npy')
HAIR=[(64,40,30),(96,60,40),(132,84,52),(166,112,70),(196,146,96)]
EYEC=[(20,14,20),(60,40,30),(110,72,40),(150,110,70),(200,170,130)]
def tintgray(layer, ramp):
    out=layer.copy(); g=(layer[...,0]==layer[...,1])&(layer[...,1]==layer[...,2])&(layer[...,3]>0)
    for i,v in enumerate((0,64,128,191,255)):
        m=g&(layer[...,0]==v); out[m,:3]=ramp[i]
    return out
def face(eye,brow,mouth,hair=3,skin='light'):
    im=body_layer(); over(im,tint(H,SKIN[skin])); over(im,C)
    over(im,tintgray(draw(EYES[eye],*EYES_POS),EYEC))
    over(im,tintgray(draw(MOUTHS[mouth],*MOUTH_POS),SKIN[skin]))
    over(im,tintgray(draw(BROWS[brow],*BROWS_POS[brow]),HAIR))
    if hair is not None: over(im,tint(classify(hair,'hair'),HAIR))
    return im
if __name__=='__main__':
    combos=[('normal','normal','grin',3),('happy','normal','smile',16),('narrow','angry','neutral',14),('wide','raised','smirk',17),('normal','thick','smile',9),('happy','thin','grin',None)]
    tiles=[Image.fromarray(face(*c)).crop((22,6,58,48)).resize((216,252),Image.NEAREST) for c in combos]
    sheet=Image.new('RGB',(216*6,252),'white')
    for k,t in enumerate(tiles): sheet.paste(t,(k*216,0))
    sheet.save(sys.argv[1] if len(sys.argv)>1 else 'faces1.png')
