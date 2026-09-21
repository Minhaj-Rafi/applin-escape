"""Original handheld-inspired landscape tiles, built entirely from drawing code."""
import math
import random
import pygame
from model import water_channel

TILE = 48
BIOMES = (
    dict(name='Bramblebrook Orchard', ground=(132, 185, 92), path=(218, 203, 137), dark=(42, 99, 63), light=(91, 162, 74), water=(70, 155, 185), rock=(131, 138, 103)),
    dict(name='Tideglass Wetlands', ground=(106, 174, 121), path=(224, 210, 158), dark=(40, 113, 93), light=(86, 163, 108), water=(57, 152, 184), rock=(121, 157, 146)),
    dict(name='Bellfern Shrine', ground=(112, 159, 113), path=(187, 192, 152), dark=(43, 92, 78), light=(77, 137, 102), water=(65, 131, 155), rock=(135, 154, 147)),
    dict(name='Copperleaf Ruins', ground=(174, 161, 98), path=(221, 190, 136), dark=(128, 75, 63), light=(202, 125, 64), water=(78, 143, 158), rock=(146, 136, 122)),
    dict(name='Starfall Highlands', ground=(102, 130, 139), path=(168, 173, 176), dark=(46,  70, 89), light=(78, 113, 134), water=(49, 104, 145), rock=(109, 126, 144)),
)


def brighten(color, amount):
    return tuple(max(0, min(255, c+amount)) for c in color)


class World:
    def __init__(self, game):
        self.game = game
        self.palette = BIOMES[game.tier]
        self.rng = random.Random(game.seed ^ 0xB10FE)
        self.surface = pygame.Surface((game.config.width*TILE, game.config.height*TILE))
        self.kinds = {}
        self.water_cells = []
        self.grass_cells = set()
        self.lamps = []
        from journey47 import clearings
        self.clearing_centers=clearings(game)
        self.build()

    def channel(self, x, y):
        return water_channel(self.game.tier,x,y,self.game.config.width,self.game.config.height)

    def tile_kind(self, x, y, wall):
        g=self.game
        if getattr(g,'rules_version',30)>=31:
            if g.tier==1 and g.bridge and (x,y)==g.bridge[0]: return 'water' if wall else 'bridge'
            if g.tier==3 and (x,y) in g.ruin_gates: return 'ruin' if wall else 'paving'
        if self.channel(x, y):
            return 'water' if wall else 'bridge'
        if not wall:
            if (x,y) in self.game.hidden_cells:
                return 'grass'
            return 'paving' if self.game.tier in (2, 4) else 'path'
        if self.game.tier in (2, 4) and (x*3+y*7)%9 < 4:
            return 'rock'
        if self.game.tier == 3 and (x*5+y*3)%7 < 3:
            return 'ruin'
        return 'tree'

    def ground(self, target, x, y, kind):
        p = self.palette
        rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
        pygame.draw.rect(target, p['ground'], rect)
        for _ in range(9):
            px, py = rect.x+self.rng.randrange(3,45), rect.y+self.rng.randrange(3,45)
            color = brighten(p['ground'], self.rng.choice((-13, 12, 19)))
            pygame.draw.line(target, color, (px, py), (px+2, py-2))
        if kind in ('path', 'paving'):
            pygame.draw.rect(target, p['path'], rect.inflate(-2,-2), border_radius=3)
            for _ in range(8):
                px, py = rect.x+self.rng.randrange(4,43), rect.y+self.rng.randrange(4,43)
                pygame.draw.line(target, brighten(p['path'], -15), (px,py), (px+2,py))
            # Join neighboring route tiles for continuous walking surfaces.
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                if self.kinds.get((x+dx,y+dy)) in ('path','paving','bridge'):
                    if dx:
                        pygame.draw.rect(target,p['path'],(rect.x+(TILE-3 if dx>0 else 0),rect.y+1,3,TILE-2))
                    else:
                        pygame.draw.rect(target,p['path'],(rect.x+1,rect.y+(TILE-3 if dy>0 else 0),TILE-2,3))
            if kind == 'paving':
                for px in (rect.x+3,rect.x+25):
                    for py in (rect.y+3,rect.y+25):
                        pygame.draw.rect(target,brighten(p['path'],-17),(px,py,19,19),1,border_radius=3)
            center=next((c for c in self.clearing_centers if abs(c[0]-x)<=1 and abs(c[1]-y)<=1),None)
            if center:
                shade=brighten(p['path'],-24)
                # Orchard stepping stones, wetland boardwalk planks, shrine/ruin courtyards, highland rings.
                if self.game.tier==0:
                    pygame.draw.ellipse(target,shade,(rect.x+8,rect.y+17,32,15),2)
                elif self.game.tier==1:
                    for yy in (10,23,36): pygame.draw.line(target,shade,(rect.x+4,rect.y+yy),(rect.right-4,rect.y+yy),2)
                elif self.game.tier in (2,3):
                    pygame.draw.rect(target,shade,rect.inflate(-10,-10),2,border_radius=5)
                else:
                    pygame.draw.circle(target,shade,rect.center,15,2)
        elif kind == 'grass':
            self.grass_cells.add((x,y))
            for gy in (10,24,38):
                for gx in (8,23,38):
                    px,py = rect.x+gx,rect.y+gy
                    pygame.draw.lines(target,brighten(p['ground'],-32),False,[(px-3,py),(px-4,py-6),(px,py-1),(px+3,py-8),(px+4,py)],2)
            if (x+y)%3 == 0:
                for dx,dy in ((10,10),(35,31)):
                    self.flower(target,rect.x+dx,rect.y+dy)

    def flower(self, s, x, y):
        color = [(251,234,172),(244,170,169),(207,190,242)][(x+y)%3]
        for dx,dy in ((-2,0),(2,0),(0,-2),(0,2)):
            pygame.draw.circle(s,color,(x+dx,y+dy),2)
        pygame.draw.circle(s,(255,233,116),(x,y),1)

    def tree(self, s, x, y):
        p=self.palette
        x,y=x*TILE,y*TILE
        d=pygame.draw
        d.ellipse(s,brighten(p['ground'],-35),(x+3,y+ 30,43,16))
        d.rect(s,(115,85,58),(x+20,y+24,10,22))
        d.line(s,(169,126,74),(x+23,y+31),(x+23,y+43),2)
        if self.game.tier == 4:
            d.polygon(s,p['dark'],[(x+24,y+2),(x+4,y+34),(x+44,y+34)])
            d.polygon(s,p['light'],[(x+24,y+2),(x+11,y+23),(x+35,y+23)])
            d.polygon(s,brighten(p['light'],15),[(x+24,y+2),(x+17,y+14),(x+29,y+14)])
        else:
            for cx,cy,r in ((24,24,22),(14,17,13),(33,17,13),(24,10,11)):
                d.circle(s,p['dark'],(x+cx,y+cy),r)
            for cx,cy,r in ((23,18,17),(14,14,10),(33,14,10),(23,8,8)):
                d.circle(s,p['light'],(x+cx,y+cy),r)
            d.arc(s,brighten(p['light'],25),(x+9,y+3,22,20),.7,2.8,2)
            d.arc(s,brighten(p['light'],-15),(x+23,y+17,16,13),3.7,6,2)
            if self.game.tier == 0 and (x+y)%5 == 0:
                d.circle(s,(203,79,64),(x+13,y+22),3)
                d.circle(s,(235,103,65),(x+32,y+17),3)

    def rock(self,s,x,y,ruin=False):
        x,y=x*TILE,y*TILE
        d=pygame.draw
        p=self.palette
        dark=brighten(p['rock'],-30)
        d.ellipse(s,brighten(p['ground'],-32),(x+3,y+34,43,12))
        if ruin:
            d.rect(s,dark,(x+7,y+6,34,36),border_radius=3)
            d.rect(s,p['rock'],(x+6,y+3,34,34),border_radius=3)
            for by in (14,26):
                d.line(s,dark,(x+7,y+by),(x+39,y+by),2)
            d.line(s,dark,(x+20,y+3),(x+20,y+14),2)
            d.line(s,dark,(x+29,y+15),(x+29,y+25),2)
            d.lines(s,p['light'],False,[(x+8,y+3),(x+11,y+13),(x+7,y+21),(x+13,y+33)],3)
        else:
            pts=[(x+5,y+35),(x+9,y+15),(x+20,y+7),(x+36,y+13),(x+44,y+32),(x+37,y+42),(x+12,y+42)]
            d.polygon(s,dark,pts)
            d.polygon(s,p['rock'],[(x+7,y+32),(x+11,y+14),(x+21,y+7),(x+36,y+13),(x+40,y+30),(x+28,y+35)])
            d.lines(s,brighten(p['rock'],28),False,[(x+12,y+20),(x+20,y+11),(x+30,y+14)],2)
            d.lines(s,dark,False,[(x+26,y+21),(x+22,y+27),(x+29,y+31)],2)

    def water(self,s,x,y,bridge=False):
        p=self.palette
        px,py=x*TILE,y*TILE
        d=pygame.draw
        d.rect(s,p['water'],(px,py,TILE,TILE))
        for dx,dy in ((5,12),(23,31)):
            d.lines(s,brighten(p['water'], 30),False,[(px+dx,py+dy),(px+dx+5,py+dy+2),(px+dx+11,py+dy)],1)
        if bridge:
            # Horizontal or vertical based on real corridor connectivity.
            g=self.game.grid
            horizontal = 0 < x < len(g[0])-1 and not g[y][x-1] and not g[y][x+1]
            d.rect(s,(105,78,51),(px,py,TILE,TILE))
            for v in range(1,48,8):
                r=(px+v,py+3,6,42) if horizontal else (px+3,py+v,42,6)
                d.rect(s,(194,154,94),r)
                d.line(s,(225,187,115),(r[0],r[1]),(r[0]+r[2]-1,r[1]),1)
            if horizontal:
                for q in (py+2,py+45):
                    d.line(s,(94,70,48),(px,q),(px+48,q),3)
            else:
                for q in (px+2,px+45):
                    d.line(s,(94,70,48),(q,py),(q,py+48),3)
        else:
            self.water_cells.append((x,y))
            # Light banks indicate the impassable water edge.
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                if self.kinds.get((x+dx,y+dy)) not in ('water','bridge'):
                    if dx:
                        d.rect(s,(201,199,140),(px+(45 if dx>0 else 0),py,3,48))
                    else:
                        d.rect(s,(201,199,140),(px,py+(45 if dy>0 else 0),48,3))

    def build(self):
        for y,row in enumerate(self.game.grid):
            for x,wall in enumerate(row):
                self.kinds[x,y]=self.tile_kind(x,y,wall)
        for (x,y),kind in self.kinds.items():
            self.ground(self.surface,x,y,kind)
            if kind=='tree': self.tree(self.surface,x,y)
            elif kind in ('rock','ruin'): self.rock(self.surface,x,y,kind=='ruin')
            elif kind in ('water','bridge'): self.water(self.surface,x,y,kind=='bridge')
        # A welcoming nest tile and an original shrine gate landmark.
        x,y=self.game.player
        px,py=x*TILE,y*TILE
        pygame.draw.ellipse(self.surface,(126,102,61),(px+6,py+22,36,19),3)
        pygame.draw.ellipse(self.surface,(224,191,112),(px+9,py+25,30,12),2)

    def draw(self, canvas, origin, cell, t, motion):
        scale=cell/TILE
        if cell==TILE:
            canvas.blit(self.surface,origin)
        else:
            size=(self.game.config.width*cell,self.game.config.height*cell)
            canvas.blit(pygame.transform.scale(self.surface,size),origin)
        if motion:
            for x,y in self.water_cells:
                px,py=int(origin[0]+(x+.5)*cell),int(origin[1]+(y+.5)*cell)
                if canvas.get_clip().collidepoint(px,py):
                    offset=int(math.sin(t*2+x)*cell*.13)
                    pygame.draw.line(canvas,brighten(self.palette['water'],45),(px-cell//6,py+offset),(px+cell//6,py+offset),1)
        ex,ey=self.game.exit
        x,y=int(origin[0]+ex*cell),int(origin[1]+ey*cell)
        c=(242,218,149) if not self.game.seeds else (177,163,134)
        d=pygame.draw
        for dx in (.18,.73):
            d.rect(canvas,c,(x+int(dx*cell),y+cell//3,max(3,cell//9),cell*2//3))
        d.polygon(canvas,( 90,91, 70),[(x+cell//10,y+cell//3),(x+cell//2,y+cell//10),(x+cell*9//10,y+cell//3)])
        d.line(canvas,c,(x+cell//8,y+cell//3),(x+cell*7//8,y+cell//3),max(2,cell//12))
