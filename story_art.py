"""Original layered illustrations, built from the game's own drawing vocabulary."""
import math
import random
from functools import lru_cache
import pygame
from art import applin, leaf, seed
from biome_art import landmark

PALETTES=(
 ((172,215,183),(248,222,153),(82,139,92),(49,101,66)),
 ((158,208,220),(246,226,185),(75,134,143),(47,94,112)),
 ((111,162,153),(225,227,156),(58,111,89),(32,76,65)),
 ((225,177,145),(255,220,157),(157,122,91),(93,89,77)),
 ((51,72,116),(169,167,196),(79,108,137),(43,68,99)),
)
KINDS=('fruit','tide','bell','wheel','wind')


def tree(s,x,y,scale,color,fruit=False):
    d=pygame.draw; r=int(28*scale)
    d.ellipse(s,(34,64,47),(x-r,y+int(32*scale),r*2,int(15*scale)))
    d.rect(s,(98,76,55),(x-int(5*scale),y,int(10*scale),int(40*scale)))
    for dx,dy,k in ((-18,0,.8),(18,-4,.85),(0,-20,1.)):
        pos=(x+int(dx*scale),y+int(dy*scale))
        d.circle(s,color,pos,int(r*k))
        d.arc(s,tuple(min(255,c+27) for c in color),(pos[0]-r*k,pos[1]-r*k,2*r*k,2*r*k),.7,2.7,max(1,int(2*scale)))
    if fruit:
        for dx,dy in ((-15,-8),(16,1),(0,-30)):
            d.circle(s,(235,95,66),(x+int(dx*scale),y+int(dy*scale)),max(2,int(4*scale)))


@lru_cache(maxsize=18)
def landscape(tier,page):
    s=pygame.Surface((1184,350)); d=pygame.draw
    sky,light,far,near=PALETTES[tier]
    for y in range(350):
        u=y/349
        d.line(s,tuple(int(a*(1-u)+b*u) for a,b in zip(sky,light)),(0,y),(1183,y))
    d.circle(s,light,(971,61),30)
    if tier==4:
        for x,y in ((130,32),(267,62),(453,25),(670,53),(810,23),(1100,94)):
            d.line(s,(230,233,224),(x-3,y),(x+3,y),1); d.line(s,(230,233,224),(x,y-3),(x,y+3),1)
    for start in range(-100,1300,200):
        d.polygon(s,far,[(start,215),(start+125,80+(start%71)),(start+300,215)])
    d.ellipse(s,near,(-160,170,1500,340))
    d.polygon(s,(194,181,131),[(440,350),(777,350),(658,224),(554,206),(500,213),(600,253)])
    rng=random.Random(710+tier)
    for _ in range(110):
        x=rng.randrange(1184); y=rng.randrange(225,350)
        if 435<x<780: continue
        d.line(s,tuple(min(255,c+18) for c in near),(x,y),(x+2,y-4),1)
    if tier==1:
        d.ellipse(s,(65,140,164),(35,212,435,130))
        for j in range(5):
            d.arc(s,(164,220,220),(75+j*22,229+j*13,320-j*42,33),.2,2.8,2)
            d.ellipse(s,(234,228,194),(110+j*61,251+(j%2)*20,46,17))
        for x in (75,395,425):
            d.line(s,(158,175,111),(x,285),(x-4,240),3)
    elif tier==3:
        for x,h in ((120,123),(270,89),(900,110),(1055,150)):
            d.rect(s,(126,118,101),(x,285-h,42,h))
            d.rect(s,(193,175,137),(x-8,278-h,58,13),border_radius=3)
            d.line(s,(222,194,142),(x+8,289-h),(x+8,280),3)
            for y in range(303-h,280,24): d.line(s,(93,94,81),(x,y),(x+40,y),2)
    elif tier==4:
        for x,y in ((175,285),(303,249),(1000,282)):
            d.polygon(s,(123,144,154),[(x-62,y+18),(x-33,y-27),(x+5,y-41),(x+55,y+14)])
            d.line(s,(196,206,197),(x-33,y-27),(x+5,y-41),3)
    else:
        color=(66,127,75) if tier==0 else (42,97,76)
        for x,y,sc in ((75,203,1.5),(225,231,1.2),(368,206,.9),(924,225,1.3),(1107,196,1.7)):
            tree(s,x,y,sc,color,tier==0)
    # The landmark and small narrative details change with each player-paced panel.
    s.blit(landmark(KINDS[tier],122),(785,217))
    if page==0:
        for x,y in ((450,278),(535,257),(665,287)): seed(s,(x,y),10,0)
    elif page==1:
        s.blit(landmark(KINDS[tier],63),(321,275))
        for x in (453,506,559): d.ellipse(s,(229,216,167),(x,294,23,9))
    else:
        d.rect(s,(200,189,147),(940,245,94,75),border_radius=6)
        d.polygon(s,(105,79,83),[(923,249),(987,203),(1051,249)])
        d.rect(s,(251,222,141),(975,272,25,48),border_radius=12)
        for x in (950,1013): d.rect(s,(246,223,163),(x,266,14,18),border_radius=3)
    # Foreground leaves frame the scene without camera movement.
    for x in (18,45,1136,1165): leaf(s,(x,335),24,(50,101,63),x)
    return s


def draw_scene(surface,rect,tier,page,hero=None,phase=0):
    frame=landscape(tier,page).copy()
    sprite=hero if hero is not None else applin(90,int(phase*3)%4)
    walk=int(math.sin(phase*.55)*18) if phase else 0
    frame.blit(sprite,(545+page*35+walk,248))
    if phase:
        # Local wingbeats and water ripples; the landscape and camera remain fixed.
        from art import cramorant
        bird=cramorant(56,int(phase*5)%8,-1)
        frame.blit(bird,(970+int(math.sin(phase*.8)*12),105+int(math.sin(phase*2)*3)))
        if tier==1:
            for i in range(3):
                r=12+int((phase*7+i*15)%40)
                pygame.draw.arc(frame,(174,224,223),(204-r,267-r//3,r*2,r//2),.1,2.9,1)
    # Gentle, local animation only; phase is held at zero in comfort mode.
    if phase:
        for j in range(4):
            x=430+j*104; y=210+int(math.sin(phase*.7+j)*4)
            leaf(frame,(x,y),5,(229,218,152),j*.5)
    surface.blit(pygame.transform.smoothscale(frame,rect.size),rect)
