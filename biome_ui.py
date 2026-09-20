"""Biome markers and prompts rendered in the existing calm full-map view."""
import math
import pygame
from art import leaf
from biome_rules import BIOME_RULES


class BiomeUI:
    def interaction_hint(self):
        g=self.game
        key=self.controls.key_name(0,5)
        return f'{key}: interact / ledge   |   '+(BIOME_RULES[g.tier][1] if g.rules_version>=31 else 'Legacy challenge: original v3.0 terrain rules.')

    def draw_biome_features(self):
        g=self.game
        if g.rules_version<31: return
        d=pygame.draw; size=self.cell
        animated=self.characters and not self.comfort
        for pos in g.interactables:
            x,y=self.center(pos); r=max(7,size//3)
            if g.tier==0:
                d.ellipse(self.canvas,(44,70,45),(x-r,y+r//2,r*2,r//2+2))
                d.line(self.canvas,(137,92,57),(x,y+r),(x,y-r//2),max(2,size//12))
                for dx,dy in ((-r//2,0),(r//2,0),(0,-r//2)):
                    d.circle(self.canvas,(88,150,71),(x+dx,y+dy),r//2+2)
                offset=int((1-g.lure_pending/.8)*r) if g.lure_pos==pos and g.lure_pending>0 and animated else 0
                d.circle(self.canvas,(244,121,70),(x+2,y-2+offset),max(3,r//3))
                leaf(self.canvas,(x+3,y-6+offset),3,(225,224,135),-.5)
            else:
                for dx in (-r,r): d.line(self.canvas,(114,82,66),(x+dx,y+r),(x+dx,y-r),max(2,size//12))
                d.line(self.canvas,(183,141,98),(x-r-2,y-r),(x+r+2,y-r),3)
                swing=int(math.sin(g.elapsed*8)*2) if animated and g.lure_pos==pos and g.lure_time>0 else 0
                d.arc(self.canvas,(246,207,101),(x-r//2+swing,y-r//2,r,r),0,math.pi,3)
                d.line(self.canvas,(246,207,101),(x-r//2+swing,y+r//2),(x+r//2+swing,y+r//2),3)
                d.circle(self.canvas,(178,120,67),(x+swing,y+r//2+2),2)
            cooldown=g.terrain_cooldowns.get(f'{pos[0]},{pos[1]}',0)
            if cooldown>0:
                d.line(self.canvas,(74,87,72),(x-r,y+r+3),(x+r,y+r+3),2)
                d.line(self.canvas,(234,198,112),(x-r,y+r+3),(x-r+int(2*r*(1-cooldown/14)),y+r+3),2)
        if g.lure_time>0 and g.lure_pos:
            x,y=self.center(g.lure_pos)
            # Fixed arcs communicate sound without camera motion or screen flashes.
            for r in (size//2,size//2+4): d.arc(self.canvas,(244,210,134),(x-r,y-r,r*2,r*2),-.6,.6,1)
        if g.tier==1 and g.bridge:
            x,y=self.center(g.bridge[0]); r=size//2-1
            d.rect(self.canvas,(48,109,135),(x-r,y-r,r*2,r*2))
            if g.bridge_open:
                color=(243,192,104) if g.tide_label!='OPEN' else (212,231,210)
                for dx,dy in ((-r//2,2),(0,-2),(r//2,2)):
                    d.ellipse(self.canvas,(44,80,91),(x+dx-4,y+dy-1,9,7))
                    d.ellipse(self.canvas,color,(x+dx-4,y+dy-3,9,6))
            else:
                for dy in (-4,3): d.line(self.canvas,(113,181,205),(x-r+3,y+dy),(x+r-3,y+dy),1)
        if g.tier==3 and g.ruin_gates:
            x,y=self.center(g.switch)
            d.circle(self.canvas,(213,177,111),(x,y),max(7,size//3),2)
            for i in range(4):
                angle=i*math.pi/2+(g.elapsed*.8 if animated and g.ruin_request else 0)
                d.line(self.canvas,(225,187,120),(x,y),(x+int(math.cos(angle)*size*.28),y+int(math.sin(angle)*size*.28)),2)
            for index,pos in enumerate(g.ruin_gates):
                x,y=self.center(pos); r=size//2-2
                opened=index==g.ruin_turn
                color=((238,185,96) if opened else (109,218,197)) if g.ruin_request else (109,218,197) if opened else (153,124,107)
                for dx in (-r,r): d.rect(self.canvas,(180,152,129),(x+dx-2,y-r,4,2*r))
                if not opened:
                    for dy in (-r//2,r//2): d.line(self.canvas,color,(x-r,y+dy),(x+r,y+dy),3)
                else:
                    d.line(self.canvas,color,(x-r+3,y+r-2),(x+r-3,y+r-2),2)
                self.text('I' if index==0 else 'II',(x,y-r-5),10,color,center=True)
        if g.tier==4:
            for lane in g.wind_lanes:
                dx,dy=lane['direction']
                for pos in lane['cells']:
                    x,y=self.center(pos)
                    color=(208,234,241)
                    for offset in (-3,3):
                        cx,cy=x-dx*offset,y-dy*offset
                        d.lines(self.canvas,color,False,[(cx-dx*3-dy*3,cy-dy*3+dx*3),(cx+dx*2,cy+dy*2),(cx-dx*3+dy*3,cy-dy*3-dx*3)],2)
