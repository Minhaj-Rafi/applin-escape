"""High-visibility biome landmarks and their illustrated field guide."""
import math
import pygame
from biome_art import landmark, feather, IVORY, INK, TEAL
from biome_rules import BIOME_RULES

KINDS=('fruit','tide','bell','wheel','wind')
LABELS=('Fruit lure','Tidal stones','Shrine bell','Turning wheel','Wind ride')
DETAILS=(
    ('Red hanging fruit on an ivory-marked branch.', 'Interact beside it. Falling fruit draws nearby birds for five seconds.'),
    ('Ivory stepping stones between two coral-tipped posts.', 'Amber means closing soon. Blue waves and a crossbar mean flooded.'),
    ('A broad golden bell under an indigo roof.', 'Interact beside it to lure nearby birds for six seconds.'),
    ('A violet six-spoke wheel with a bright brass hub.', 'Interact beside it. Gate I and Gate II swap after the amber preview.'),
    ('A striped windsock and bright feather-shaped lane marks.', 'Interact on a feather for a wind ride; dash along the wind to go farther.'),
)


class BiomeUI:
    def interaction_hint(self):
        g=self.game; key=self.controls.key_name(0,5)
        return f'{key}: interact / ledge   |   '+(BIOME_RULES[g.tier][1] if g.rules_version>=31 else 'Legacy challenge: original v3.0 terrain rules.')

    def draw_biome_badge(self):
        g=self.game
        if g.rules_version<31:
            self.text('Legacy v3.0 terrain rules',(674,106),12,IVORY); return
        self.canvas.blit(landmark(KINDS[g.tier],42),(615,91))
        self.text(LABELS[g.tier],(667,94),16,IVORY,bold=True)
        self.text(g.biome_prompt(),(667,116),11,(229,201,149))

    def draw_biome_features(self):
        g=self.game
        if g.rules_version<31: return
        d=pygame.draw; size=self.cell; marker_size=max(32,int(size*1.12))
        animated=self.characters and not self.comfort
        nearby=[]
        for pos in g.interactables:
            x,y=self.center(pos)
            kind='fruit' if g.tier==0 else 'bell'
            phase=g.elapsed*6 if animated and g.lure_pos==pos and g.lure_time>0 else 0
            self.canvas.blit(landmark(kind,marker_size,phase=phase),(x-marker_size//2,y-marker_size//2))
            cooldown=g.terrain_cooldowns.get(f'{pos[0]},{pos[1]}',0)
            if cooldown>0:
                r=marker_size//3
                d.line(self.canvas,INK,(x-r,y+marker_size//2),(x+r,y+marker_size//2),3)
                d.line(self.canvas,(255,211,120),(x-r,y+marker_size//2),(x-r+int(2*r*(1-cooldown/14)),y+marker_size//2),2)
            nearby.append(pos)
        if g.lure_time>0 and g.lure_pos:
            x,y=self.center(g.lure_pos)
            for r in (marker_size//2,marker_size//2+4): d.arc(self.canvas,(255,232,168),(x-r,y-r,r*2,r*2),-.6,.6,2)
        if g.tier==1 and g.bridge:
            pos=g.bridge[0]; x,y=self.center(pos)
            state='closed' if not g.bridge_open else 'ready' if g.tide_label=='OPEN' else 'warning'
            self.canvas.blit(landmark('tide',marker_size,state),(x-marker_size//2,y-marker_size//2))
        if g.tier==3 and g.ruin_gates:
            x,y=self.center(g.switch)
            phase=g.elapsed if animated and g.ruin_request else 0
            self.canvas.blit(landmark('wheel',marker_size,phase=phase),(x-marker_size//2,y-marker_size//2))
            nearby.append(g.switch)
            for index,pos in enumerate(g.ruin_gates):
                x,y=self.center(pos); r=max(10,size//2-2); opened=index==g.ruin_turn
                color=((255,184,85) if opened else TEAL) if g.ruin_request else TEAL if opened else (209,150,173)
                for dx in (-r,r):
                    d.rect(self.canvas,INK,(x+dx-3,y-r,6,2*r))
                    d.rect(self.canvas,IVORY,(x+dx-2,y-r,3,2*r))
                    d.polygon(self.canvas,(151,92,191),[(x+dx-5,y-r),(x+dx,y-r-6),(x+dx+5,y-r)])
                if not opened:
                    for dy in (-r//2,r//2): d.line(self.canvas,color,(x-r,y+dy),(x+r,y+dy),4)
                else: d.line(self.canvas,color,(x-r+3,y+r-2),(x+r-3,y+r-2),3)
                self.text('I' if index==0 else 'II',(x,y-r-6),11,IVORY,center=True,bold=True)
        if g.tier==4:
            for lane in g.wind_lanes:
                for pos in lane['cells']: feather(self.canvas,self.center(pos),size,lane['direction'])
                x,y=self.center(lane['cells'][0])
                self.canvas.blit(landmark('wind',max(29,size),direction=lane['direction']),(x-size//2,y-size//2))
            nearby=[p for lane in g.wind_lanes for p in lane['cells']]
        for player,pos in enumerate((g.player,g.partner['pos']) if g.coop else (g.player,)):
            options=[p for p in nearby if abs(p[0]-pos[0])+abs(p[1]-pos[1]) <= (0 if g.tier==4 else 1)]
            if options:
                target=min(options,key=lambda p:abs(p[0]-pos[0])+abs(p[1]-pos[1])); x,y=self.center(target)
                key=self.controls.key_name(player,5)
                # Small, steady input hint; the objects themselves have no badge outline.
                rect=self.text(key,(x,y-marker_size//2-10),11,IVORY,center=True,bold=True)

    def draw_biome_guide(self):
        self.header('Know it at a glance.', 'The same shapes appear here, on the map and beside the biome name. Colour is only one cue.')
        for i,(name,(look,use)) in enumerate(zip(LABELS,DETAILS)):
            y=144+i*113
            self.panel((43,y,1190,103))
            self.canvas.blit(landmark(KINDS[i],84),(61,y+8))
            self.text(name,(170,y+10),24,IVORY,bold=True)
            self.text(look,(170,y+45),16,(184,210,200))
            self.text(use,(170,y+72),15,(233,207,153))
        self.button('Back',(48,766,170,44),'back')
        self.text('Interact defaults: E / Right Ctrl. Remap through Settings > Controls.',(268,780),16,IVORY)
