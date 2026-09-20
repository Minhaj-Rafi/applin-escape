"""Original code-drawn fan sprites and decorative graphics. No ripped assets."""
import math
import pygame

CREAM = (246, 237, 213)


def applin(size=96, frame=0, facing=1, gaze=(0,0), blink=False):
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    d = pygame.draw
    bob = (0, -2, 0, 1)[frame % 4]
    d.ellipse(s, (4, 14, 12, 85), (22, 101, 85, 17))
    d.ellipse(s, (70, 115, 62), (21, 87 + bob, 35, 22))
    d.ellipse(s, (84, 139, 72), (73, 87 + bob, 35, 22))
    d.ellipse(s, (117, 32, 44), (22, 35 + bob, 86,  70))
    d.ellipse(s, (210, 66, 65), (24, 30 + bob, 46, 66))
    d.ellipse(s, (225, 77, 66), (55, 30 + bob, 49, 69))
    d.ellipse(s, (239, 102, 77), (29, 36 + bob, 34, 51))
    d.ellipse(s, (255, 177, 126), (34, 43 + bob, 9, 20))
    d.ellipse(s, (131, 43, 49), (49, 77 + bob, 37, 22))
    d.ellipse(s, (51, 69, 47), (56, 80 + bob, 24, 13))
    # Applin's green eye stalks and leaf-shaped eyes above its apple body.
    d.line(s, (80, 117, 51), (57, 43 + bob), (47, 19 + bob), 9)
    d.line(s, (80, 117, 51), (72, 43 + bob), (83, 17 + bob), 9)
    d.ellipse(s, (129, 184, 68), (29, 6 + bob, 31, 35))
    d.ellipse(s, (157, 205, 78), (72, 4 + bob, 30, 36))
    d.ellipse(s, (249, 239, 198), (37, 13 + bob, 16, 23))
    d.ellipse(s, (249, 239, 198), (77, 11 + bob, 16, 23))
    if blink:
        d.line(s,(41,54,35),(39,24+bob),(51,24+bob),3)
        d.line(s,(41,54,35),(79,22+bob),(91,22+bob),3)
    else:
        dx,dy=gaze[0]*2,gaze[1]*2
        d.ellipse(s, (41, 54, 35), (43+dx, 17+bob+dy, 6, 16))
        d.ellipse(s, (41, 54, 35), (81+dx, 15+bob+dy, 6, 16))
    d.line(s, (99, 76, 41), (65, 41 + bob), (65, 24 + bob), 5)
    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return pygame.transform.smoothscale(s, (size, size))


def cramorant(size=96, frame=0, facing=1):
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    d = pygame.draw
    flap = (0, -7, 0, 5)[frame % 4]
    d.ellipse(s, (4, 14, 12, 85), (17, 107, 94, 13))
    d.polygon(s, (35, 76, 118), [(39, 93), (8, 82 + flap), (29, 69), (47, 76)])
    d.line(s, (224, 163, 63), (61, 93), (56, 110), 5)
    d.line(s, (224, 163, 63), (80, 94), (80, 110), 5)
    d.line(s, (244, 186, 79), (46, 111), (65, 111), 4)
    d.line(s, (244, 186, 79), (73, 111), (90, 111), 4)
    d.ellipse(s, (44, 107, 163), (30, 52, 61, 49))
    d.ellipse(s, (71, 139, 189), (36, 53, 42, 39))
    d.polygon(s, (32, 83, 139), [(49, 60), (19, 52 + flap), (31, 85 + flap), (57, 84)])
    d.ellipse(s, (65, 130, 184), (65, 24, 24, 61))
    d.ellipse(s, (71, 144, 202), (58, 12, 39, 40))
    d.polygon(s, (52, 113, 171), [(65, 23), (60, 5), (75, 14), (78, 3), (88, 21)])
    d.polygon(s, (243, 197, 76), [(84, 32), (122, 41), (87, 48)])
    d.line(s, (173, 118, 46), (92, 42), (119, 41), 2)
    d.polygon(s, (238, 222, 180), [(70, 50), (93, 49), (89,  70), (78, 82), (66, 65)])
    d.circle(s, (245, 247, 225), (82, 29), 9)
    d.circle(s, (39, 49, 51), (85, 29), 4)
    d.circle(s, (255, 255, 241), (86, 27), 1)
    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return pygame.transform.smoothscale(s, (size, size))


def seed(surface, center, radius, t=0):
    x,y=center
    r=max(8,radius)
    # Pointed top and rounded belly distinguish the seed from the round berry.
    pygame.draw.ellipse(surface,(61,61,40),(x-r,y+r-2,2*r,5))
    points=[(x,y-r-3),(x+r*.68,y-r*.3),(x+r*.8,y+r*.35),(x+r*.4,y+r),(x-r*.4,y+r),(x-r*.8,y+r*.35),(x-r*.68,y-r*.3)]
    pygame.draw.polygon(surface,(202,119,19),points)
    pygame.draw.polygon(surface,(255,205,42),[(x,y-r-3),(x+r*.68,y-r*.3),(x+r*.6,y+r*.45),(x,y+r*.8),(x-r*.5,y+r*.3)])
    pygame.draw.line(surface,(134,75,14),(x,y-r+4),(x-1,y+r-2),2)
    offset=int(math.sin(t*2)*1) if t else 0
    pygame.draw.line(surface,(255,248,174),(x+2+offset,y-r+4),(x+3+offset,y+3),2)


def berry(surface, center, radius, t=0):
    x,y=center
    r=max(7,radius)
    pygame.draw.ellipse(surface,( 40, 50, 70),(x-r,y+r-1,2*r,5))
    pygame.draw.circle(surface,( 80,42,170),(x,y+1),r+1)
    pygame.draw.circle(surface,( 50,128,239),(x+1,y),r)
    pygame.draw.circle(surface,(82,184,255),(x+2,y-2),max(3,r-3))
    pygame.draw.ellipse(surface,(228,247,255),(x-3,y-4,4,6))
    sway=int(math.sin(t*2.4)) if t else 0
    pygame.draw.polygon(surface,(110,234,147),[(x,y-r+1),(x-5+sway,y-r-4),(x,y-r-2),(x+5+sway,y-r-5),(x+3,y-r),(x+7,y-r+1)])


def heart(surface, x, y, active=True):
    color = (240, 126, 122) if active else (66, 71, 75)
    pygame.draw.circle(surface, color, (x-4, y-3), 6)
    pygame.draw.circle(surface, color, (x+4, y-3), 6)
    pygame.draw.polygon(surface, color, [(x-10, y-1), (x+10, y-1), (x, y+11)])


def leaf(surface, center, size, color=(154, 222, 170), angle=0):
    x, y = center
    pts = [(x+math.cos(angle+a)*size*r, y+math.sin(angle+a)*size*r)
           for a, r in ((0, 1), (1.3, .55), (math.pi, 1), (4.4, .55))]
    pygame.draw.polygon(surface, color, pts)


class Sprites:
    def __init__(self):
        self.cache = {}

    def get(self, name, size, frame, facing=1):
        key = name, size, frame % 8, 1 if facing >= 0 else -1
        if key not in self.cache:
            self.cache[key] = applin(size,frame,facing) if name == 'applin' else flying_hunter(name,size,frame,facing)
        return self.cache[key]


def hunter(species, size=96, frame=0, facing=1):
    """New stylized fan drawings; no extracted or traced game sprites."""
    if species.lower() == 'cramorant':
        return cramorant(size,frame,facing)
    s=pygame.Surface((128,128),pygame.SRCALPHA)
    d=pygame.draw
    flap=(0,-8,0,6)[frame%4]
    colors={
        'pidgeotto':((165,119, 70),(231,205,145),(120,77,48)),
        'spearow':((160,109, 70),(219,173,121),(94, 60,44)),
        'murkrow':((56, 70,105),(85,104,145),(31, 40, 70)),
        'talonflame':((202, 80, 50),(243,156,81),( 60, 70, 90)),
    }
    base,light,dark=colors[species.lower()]
    d.ellipse(s,(0,0,0,65),(18,104,92,14))
    d.line(s,(224,167, 90),(57, 90),(51,110),4)
    d.line(s,(224,167,90),(78,90),(83,110),4)
    d.line(s,(224,167,90),(43,111),(60,111),4)
    d.line(s,(224,167,90),(77,111),(94,111),4)
    d.polygon(s,dark,[(35, 80),(7, 90),(19,57),(46,68)])
    d.ellipse(s,base,(31,46, 60,55))
    d.ellipse(s,light,(56,53,33,42))
    d.polygon(s,dark,[(58,60),(19, 40+flap),(27,85+flap),(63,84)])
    for i in range(3):
        d.line(s,base,(26+i*7,55+flap),(40+i*7,77+flap),3)
    d.ellipse(s,base,(60, 18,43, 40))
    d.polygon(s,(225,173, 90),[(96,34),(121,42),(97,48)])
    d.circle(s,(249,238,202),(88, 30),7)
    d.circle(s,(38,38, 40),(90,30),3)
    if species.lower()=='pidgeotto':
        d.polygon(s,(190, 70,60),[(67, 20),(72,5),(86,9),(96,21)])
        d.polygon(s,(237,199,100),[(66,22),(60,11),(70,14),(79,23)])
        d.line(s,dark,(79,35),(89,40),4)
    elif species.lower()=='spearow':
        d.polygon(s,dark,[(64,27),(56,9),(72,17),(75,6),(83,19),(94,13),(98,26)])
        d.line(s,(244,218,166),(71,49),(87,54),5)
    elif species.lower()=='murkrow':
        d.polygon(s,dark,[(57,26),(64,7),(83,3),(96,19),(109,24),(58,30)])
        d.line(s,light,(64,21),(99,23),2)
        d.polygon(s,(223,173,71),[(94,37),(123,41),(99,46)])
        d.polygon(s,dark,[(26,91),(6,101),(7,83),(2, 70),(32, 70)])
    elif species.lower()=='talonflame':
        d.polygon(s,base,[(69,22),(58,8),(82,14),(95,25)])
        d.line(s,dark,(80,27),(97,29),3)
        for x,y in ((68,66),(78,75),(66,83)):
            d.polygon(s,dark,[(x,y),(x+5,y-2),(x+2,y+5)])
        d.polygon(s,(226, 90, 50),[(31,70),(13,63),(17,86),(35,89)])
    if facing<0:
        s=pygame.transform.flip(s,True,False)
    return pygame.transform.smoothscale(s,(size,size))


def flying_hunter(species,size=96,frame=0,facing=1):
    """Original airborne fan interpretation; silhouette and plumage distinguish roles."""
    name=species.lower()
    palettes={
        'cramorant':((51,133,192),(244,228,184),(29,77,132)),
        'pidgeotto':((173,125, 70),(246,219,153),(120,74,43)),
        'spearow':((170,111,76),(239,181,120),( 90, 50,40)),
        'murkrow':(( 40,54,94),(96,115,159),(21,29, 50)),
        'talonflame':((222,93, 60),(247,160, 80),(54, 60,76))}
    body,breast,wing=palettes[name]
    s=pygame.Surface((128,128),pygame.SRCALPHA)
    d=pygame.draw
    phase=math.sin(frame/8*math.tau)
    tip=int( 50-35*phase)
    # Far wing, tucked feet and tail, then body and near wing.
    d.polygon(s,wing,[(67,55),(93,tip+6),(120,tip+13),(107,tip+25),(83, 70)])
    d.polygon(s,wing,[( 40, 70),(7, 80),(14,52),(49,59)])
    d.line(s,(222,164,79),( 60, 80),( 50,85),3)
    d.line(s,(222,164,79),(74, 80),(66,85),3)
    d.ellipse(s,body,( 30,42,65,45))
    d.ellipse(s,breast,(64,50,28,32))
    d.polygon(s,wing,[(58,49),(27,tip),(5,tip+15),(15,tip+23),(11,tip+31),(28,tip+39),( 60, 70)])
    for i in range(3):
        d.line(s,body,(17+i*7,tip+17),(37+i*4,tip+ 30),2)
    hx,hy=(82, 30) if name=='cramorant' else ( 80, 40)
    if name=='cramorant':
        d.ellipse(s,body,(70,28,19,41))
    d.ellipse(s,body,(hx-17,hy-16,36,32))
    beak_len=29 if name=='cramorant' else 22 if name=='murkrow' else 16
    d.polygon(s,(242,185,82),[(hx+12,hy+1),(hx+12+beak_len,hy+7),(hx+13,hy+12)])
    d.circle(s,(255,247,212),(hx+7,hy-3),6)
    d.circle(s,(25,30,37),(hx+9,hy-3),3)
    if name=='pidgeotto':
        d.polygon(s,(211,75, 50),[(hx-14,hy-10),(hx-22,hy-25),(hx-3,hy-20),(hx+12,hy-10)])
        d.line(s,(255,218,101),(hx-19,hy- 20),(hx-4,hy-14),4)
        d.line(s,wing,(hx,hy+4),(hx+10,hy+8),3)
    elif name=='spearow':
        d.polygon(s,wing,[(hx-17,hy-8),(hx-21,hy-26),(hx-9,hy-18),(hx-2,hy-28),(hx+5,hy-14),(hx+16,hy-18),(hx+17,hy-4)])
        d.polygon(s,(184,65, 50),[(26,tip+9),(9,tip+15),(24,tip+30),( 40,tip+27)])
    elif name=='murkrow':
        d.polygon(s,wing,[(hx-23,hy-8),(hx-11,hy-28),(hx+7,hy-30),(hx+17,hy-12),(hx+24,hy-7)])
        d.line(s,breast,(hx-17,hy-8),(hx+20,hy-7),2)
        d.polygon(s,wing,[(25, 70),(5,65),(8,88),(21,91),(32,82)])
    elif name=='talonflame':
        d.polygon(s,body,[(hx-16,hy-7),(hx-24,hy-24),(hx-5,hy-15),(hx+10,hy-8)])
        d.line(s,wing,(hx-1,hy-7),(hx+13,hy-6),3)
        for dx,dy in ((69, 60),(77, 70),(64,74)):
            d.polygon(s,wing,[(dx,dy),(dx+5,dy),(dx+2,dy+5)])
        d.line(s,body,(10,tip+14),(29,tip+ 30),5)
    else:
        d.polygon(s,wing,[(hx-12,hy-9),(hx-20,hy-26),(hx-3,hy-17),(hx+4,hy-27),(hx+12,hy-10)])
    if facing<0:s=pygame.transform.flip(s,True,False)
    return pygame.transform.smoothscale(s,(size,size))
