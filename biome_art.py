"""Original landmark sprites, drawn large enough to identify on the full map."""
import math
import pygame

INK=(37,48,66)
IVORY=(248,239,211)
TEAL=(49,211,204)


def landmark(kind, size=40, state='ready', phase=0, direction=(1,0)):
    s=pygame.Surface((80,80),pygame.SRCALPHA); d=pygame.draw
    # A physical stone foot and shadow separate objects from all ground palettes.
    d.ellipse(s,(20,30,39,160),(9,62,64,13))
    if kind in ('fruit','bell','wheel','wind'):
        d.polygon(s,(121,128,140),[(19,60),(56,60),(67,69),(11,69)])
        d.line(s,IVORY,(18,60),(57,60),3)
    if kind=='fruit':
        d.line(s,(108,66,50),(40,63),(40,16),9)
        d.line(s,IVORY,(37,62),(37,17),3)
        d.line(s,(112,67,50),(21,20),(65,20),7)
        for x,y in ((19,34),(43,43),(63,34)):
            d.line(s,(67,110,55),(x,20),(x,y-5),3)
            d.ellipse(s,(156,41,61),(x-11,y-7,23,25))
            d.ellipse(s,(253,87,66),(x-10,y-9,21,24))
            d.ellipse(s,(255,198,144),(x-7,y-6,5,10))
            d.polygon(s,(99,221,133),[(x,y-8),(x+2,y-16),(x+12,y-12),(x+4,y-8)])
    elif kind=='bell':
        d.line(s,(76,69,145),(15,62),(15,10),9)
        d.line(s,(76,69,145),(65,62),(65,10),9)
        d.line(s,IVORY,(13,59),(13,12),3)
        d.polygon(s,(106,90,181),[(8,13),(39,3),(73,13),(72,19),(8,19)])
        cx=40+int(math.sin(phase)*3)
        d.circle(s,(255,219,109),(cx,26),13)
        d.polygon(s,(239,173,45),[(cx-13,25),(cx+13,25),(cx+17,48),(cx-17,48)])
        d.polygon(s,(255,223,117),[(cx-10,24),(cx,24),(cx-3,44),(cx-13,44)])
        d.ellipse(s,(255,234,150),(cx-22,44,44,10))
        d.circle(s,(167,94,49),(cx,57),5)
        d.line(s,IVORY,(cx-9,25),(cx-12,37),3)
    elif kind=='wheel':
        d.rect(s,(152,141,124),(30,42,20,23),border_radius=3)
        d.circle(s,(60,48,96),(40,33),28)
        d.circle(s,(168,113,240),(40,31),26)
        d.circle(s,(65,53,113),(40,31),17)
        for i in range(6):
            angle=i*math.tau/6+phase
            end=(40+int(math.cos(angle)*24),31+int(math.sin(angle)*24))
            d.line(s,(240,199,117),(40,31),end,5)
            d.circle(s,IVORY,end,4)
        d.circle(s,IVORY,(40,31),8)
        d.circle(s,(234,152,71),(40,31),4)
    elif kind=='tide':
        d.ellipse(s,(38,91,134),(4,27,72,43))
        for x in (5,69):
            d.rect(s,IVORY,(x,15,6,46),border_radius=2)
            d.polygon(s,(251,136,106),[(x,14),(x+6,14),(x+3,5)])
        if state!='closed':
            color=(255,204,107) if state=='warning' else IVORY
            for x,y in ((21,40),(40,33),(58,42)):
                d.ellipse(s,(29,60,85),(x-10,y+3,22,16))
                d.ellipse(s,color,(x-10,y-3,22,15))
                d.line(s,(255,254,235),(x-5,y),(x+3,y-1),2)
        else:
            for y in (34,47,60): d.lines(s,(103,222,230),False,[(12,y),(25,y-4),(38,y),(51,y-4),(66,y)],3)
            d.line(s,(246,133,127),(14,27),(66,27),6)
    elif kind=='wind':
        d.line(s,(82,86,103),(23,63),(23,10),7)
        d.line(s,IVORY,(20,63),(20,10),3)
        d.circle(s,(255,203,109),(23,9),5)
        d.polygon(s,(38,159,190),[(26,11),(69,20),(59,37),(27,31)])
        d.polygon(s,IVORY,[(27,12),(39,14),(39,31),(27,29)])
        d.polygon(s,(255,170,102),[(50,17),(60,19),(54,35),(46,33)])
        d.line(s,(227,252,250),(41,49),(68,49),3)
        d.lines(s,(227,252,250),False,[(60,43),(68,49),(60,55)],3)
    if kind=='wind' and direction[0]<0: s=pygame.transform.flip(s,True,False)
    return pygame.transform.smoothscale(s,(size,size))


def feather(surface,center,size,direction):
    x,y=center; dx,dy=direction; d=pygame.draw
    # A feather, with a dark quill and white vanes, is distinct from a ledge arrow.
    r=max(7,size//3)
    tip=(x+dx*r,y+dy*r); tail=(x-dx*r,y-dy*r)
    d.line(surface,INK,tail,tip,5)
    d.line(surface,(111,242,243),tail,tip,2)
    for t in (-.4,.1,.6):
        cx,cy=x+dx*r*t,y+dy*r*t
        for side in (-1,1):
            d.line(surface,IVORY,(int(cx-dx*3-dy*side*r*.5),int(cy-dy*3+dx*side*r*.5)),(int(cx+dx*2),int(cy+dy*2)),2)
