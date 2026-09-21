"""Interaction inspection, accessible reading, story payoffs and co-op signals."""
import math
import pygame
from biome_art import landmark
from biome_ui import KINDS,LABELS,DETAILS
from sanctuary import CHAPTERS,budew
from story_art import draw_scene
from home_progress import home_progress
from model import path_to

TEXT=(243,237,216); GREEN=(177,225,153); GOLD=(247,203,118); MUTED=(153,176,166)
ENDINGS=(
 ('The first lantern is lit.','The orchard seeds settle into warm earth. A path now leads safely home.'),
 ('Water returns to the garden.','The pond catches the light again. Small footsteps gather by its edge.'),
 ('The woodland answers.','A quiet bell rings across the sanctuary. The ferns open around a new shelter.'),
 ('The terrace wakes.','The old stones hold the afternoon warmth. Another corner of home is restored.'),
 ('Everyone has a place here.','The last seeds glow beneath the stars. Applin has brought the scattered light home.'),
)


class PolishUI:
    def init_polish(self):
        self.large_text=self.store.get('large_text_v42',False)
        self.audio.music_volume=self.store.get('music_volume_v42',.4)
        self.audio.effects_volume=self.store.get('effects_volume_v42',.8)
        self.audio.apply()
        self.inspect_pos=None
        self.ending=False
        self.pings={}
        from home_activities import care_state
        from garden_timers import migrate_crops
        progress=home_progress(self.store)
        migrate_crops(care_state(progress))
        self.store.set('sanctuary_v4',progress)
        self.pending_contract=None
        self.collection_page=0
        self.contract_goal=0
        self.record_offset=0
        self.name_input=''
        self.profile_notice=''
        self.selected_berry=0
        self.home_tab=0
        self.resident_page=0
        self.care_notice='Grow a little garden and meet your rescued Budew.'

    def polish_action(self,action):
        if action=='accessibility':
            if self.screen=='play': self.action('pause')
            self.navigation.append((self.screen,self.return_screen)); self.return_screen=self.screen
            self.screen='accessibility'
        elif action=='large_text':
            self.large_text=not self.large_text; self.store.set('large_text_v42',self.large_text)
        elif action in ('music_level','effects_level'):
            attr='music_volume' if action=='music_level' else 'effects_volume'
            old=getattr(self.audio,attr); value=round(old+.2,1)
            if value>1: value=0
            setattr(self.audio,attr,value); self.store.set(attr+'_v42',value); self.audio.apply()
            if attr=='effects_volume': self.audio.play('seed')
        elif action=='inspect_nearest' and self.game:
            targets=self.inspect_targets()
            if targets:
                pos=min(targets,key=lambda p:sum(abs(a-b) for a,b in zip(self.game.player,p)))
                self.action(f'inspect:{pos[0]}:{pos[1]}')
            else: self.game.notify('This legacy map has no biome landmark to inspect.')
        elif action.startswith('inspect:') and self.game:
            _,x,y=action.split(':'); self.inspect_pos=(int(x),int(y))
            if self.screen=='play': self.action('pause')
            self.navigation.append((self.screen,self.return_screen)); self.return_screen=self.screen
            self.screen='object_info'
        elif action.startswith('ping:'):
            player=int(action[-1]); g=self.game
            if not g or not g.coop or self.screen!='play': return True
            pos=g.partner['pos'] if player else g.player
            self.pings[player]=(pos,g.elapsed+5)
            g.notify(f'Player {player+1}: come here! The numbered flag lasts five seconds.')
        elif action=='ending' and self.game and self.game.state=='cleared':
            self.navigation.append((self.screen,self.return_screen)); self.return_screen=self.screen
            self.screen='ending'; self.ending=True
        else: return False
        return True

    def flow_text(self,text,x,y,width,size=20,color=TEXT,line_height=None):
        size=size+3 if self.large_text else size
        spacing=line_height or size+8
        words=text.split(); line=''
        for word in words:
            candidate=(line+' '+word).strip()
            if line and self.font(size).size(candidate)[0]>width:
                self.text(line,(x,y),size,color); y+=spacing; line=word
            else: line=candidate
        if line: self.text(line,(x,y),size,color); y+=spacing
        return y

    def inspect_targets(self):
        g=self.game
        if g.rules_version<31: return []
        if g.tier in (0,2): return g.interactables
        if g.tier==1: return [g.bridge[0]] if g.bridge else []
        if g.tier==3: return [g.switch]
        return [p for lane in g.wind_lanes for p in lane['cells']]

    def object_status(self,pos,player=0):
        g=self.game; location=g.partner['pos'] if player else g.player
        distance=sum(abs(a-b) for a,b in zip(location,pos))
        if g.tier in (0,2):
            cooldown=g.terrain_cooldowns.get(f'{pos[0]},{pos[1]}',0)
            if cooldown>0: return f'Recharging: {math.ceil(cooldown)} seconds. Nearby birds may still be investigating.'
            return 'Ready. Stand on or beside it and press Interact.' if distance<=1 else 'Ready. Move beside it before pressing Interact.'
        if g.tier==1:
            return ('Crossing passable. ' if g.bridge_open else 'Crossing flooded. ')+f'{g.tide_label.lower()}; next tide phase in {math.ceil(g.bridge_time)} seconds. No button is needed.'
        if g.tier==3:
            if g.ruin_request: return 'Turning: keep the closing gate clear. Occupied gates wait until everyone leaves.'
            return 'Ready. Stand beside the wheel and press Interact. Gate I and Gate II exchange their routes.'
        cooldown=g.terrain_cooldowns.get(f'wind{player}',0)
        return f'Wind recharge: {math.ceil(cooldown)} seconds.' if cooldown else 'Ready. Stand on a feather and press Interact to ride along the marked direction.'

    def draw_object_info(self):
        g=self.game; self.header(LABELS[g.tier], 'Paused field guide / inspect here, use the object inside the maze')
        self.panel((48,151,1184,559))
        self.canvas.blit(landmark(KINDS[g.tier],190),(92,225))
        y=self.flow_text(DETAILS[g.tier][0],337,200,835,24,GOLD)
        y=self.flow_text(DETAILS[g.tier][1],337,y+22,835,21)
        y=self.flow_text(self.object_status(self.inspect_pos),337,y+30,835,20,GREEN)
        if g.coop: self.flow_text('Player 2: '+self.object_status(self.inspect_pos,1),337,y+22,835,18)
        self.flow_text('Return to the paused maze, then resume to use this object. Inspecting it does not spend a charge or advance the timer.',85,585,1090,18,MUTED)
        self.button('Back to paused maze',(850,753,380,48),'back',True)

    def draw_accessibility(self):
        self.header('Sound and readable text','Settings apply immediately and are saved on this computer.')
        for i,(label,value,action,desc) in enumerate((
            ('Reading size','LARGE' if self.large_text else 'STANDARD','large_text','Story, instructions, notices and interaction details.'),
            ('Music volume',f'{round(self.audio.music_volume*100)}%','music_level','Cycles 0 to 100%. The music toggle still controls mute.'),
            ('Effects volume',f'{round(self.audio.effects_volume*100)}%','effects_level','Cycles 0 to 100%. A short seed sound previews the level.'),
            ('Comfort mode','ON' if self.comfort else 'OFF','comfort','Fixed map; no camera motion, decorative motion or character bobbing.'))):
            y=158+i*115; self.panel((48,y,1184,103))
            self.text(label,(75,y+12),25,TEXT)
            self.flow_text(desc,75,y+52,850,17,MUTED)
            self.button(value,(1020,y+25,181,49),action)
        self.flow_text('Predator shapes: ! chasing, triangle warning, ? searching, diamond lured, square recovering. These symbols work without relying on colour.',65,638,1138,18)
        self.button('Back',(48,754,180,48),'back',True)

    def draw_ending(self):
        g=self.game; title,body=ENDINGS[g.tier]
        self.header(title,'Chapter ending / take your time')
        phase=self.t if self.characters and not self.comfort else 0
        draw_scene(self.canvas,pygame.Rect(48,143,1184,300),g.tier,2,self.hero_sprite(90,0,g.direction),phase)
        for i in range(g.rescued): budew(self.canvas,(759+i*38,408),32)
        self.panel((48,460,1184,260))
        y=self.flow_text(body,75,480,1120,23,GOLD)
        rescue=('Budew: You came back for us. We will keep the garden growing.' if g.rescued else 'Some Budew are still out there. Another journey may lead you to them.')
        y=self.flow_text(f'{g.rescued} of 2 Budew brought home this chapter. '+rescue,75,y+12,1120,20)
        if g.tier==4:
            p=home_progress(self.store)
            self.flow_text(f'Your sanctuary now shelters {p["rescued"]} rescued Budew, with {len(p["restored"])} of 5 gardens restored.',75,y+10,1120,20,GREEN)
        self.button('Back to results',(48,752,254,48),'back')
        action=self.result_primary()
        self.button('Continue from results',(850,752,382,48),action,True)

    def draw_polish_world(self):
        g=self.game; d=pygame.draw
        for pos in self.inspect_targets():
            x,y=self.center(pos)
            hit=pygame.Rect(x-self.cell//2,y-self.cell//2,self.cell,self.cell).clip(pygame.Rect(30,150,880,610))
            if hit.width and hit.height: self.buttons.append((hit,f'inspect:{pos[0]}:{pos[1]}'))
        for e,visual in zip(g.enemies,self.visual_enemies):
            x,y=self.center(visual); y-=self.cell*.76
            tag='×' if e.stunned>0 else '!' if e.mood in ('chase','swoop') else '?' if e.mood=='search' else '◇' if e.mood=='lured' else '□' if e.recovery>0 else '·'
            if e.warning>0:
                d.polygon(self.canvas,GOLD,[(x,y-7),(x-7,y+5),(x+7,y+5)],2)
            else:
                self.text(tag,(x,y),15,GOLD if e.mood=='lured' else TEXT,center=True,bold=True)
        for player,(pos,expiry) in self.pings.items():
            if expiry<=g.elapsed: continue
            x,y=self.center(pos); color=(153,222,248) if player else GOLD
            d.line(self.canvas,color,(x,y-26),(x,y-4),2)
            d.polygon(self.canvas,color,[(x,y-26),(x+18,y-20),(x,y-14)])
            self.text(str(player+1),(x+7,y-20),10,(14,24,27),center=True,bold=True)
        if g.coop and g.partner['down']:
            x,y=self.center(g.partner['pos']); d.rect(self.canvas,GOLD,(x-self.cell//2,y-self.cell//2,self.cell,self.cell),2)

    def draw_polish_hud(self):
        g=self.game
        if g.coop:
            self.button('P1 call' if pygame.K_F3 in sum(self.controls.keys,[]) else 'P1 [F3]',(826,30,114,43),'ping:0',small=True)
            self.button('P2 call' if pygame.K_F4 in sum(self.controls.keys,[]) else 'P2 [F4]',(950,30,114,43),'ping:1',small=True)
        if g.mode=='tutorial':
            target=None
            if g.tutorial_step==1: target=min(g.hidden_cells,key=lambda p:len(path_to(g.grid,g.player,p))) if g.hidden_cells else None
            elif g.tutorial_step==2: target=g.interactables[0] if g.interactables else None
            elif g.tutorial_step>=4: target=min(g.seeds,key=lambda p:len(path_to(g.grid,g.player,p))) if g.seeds else g.exit
            if target:
                route=path_to(g.grid,g.player,target)
                for pos in route[1:]: pygame.draw.circle(self.canvas,GOLD,self.center(pos),3)
            self.text(f'LESSON {min(6,g.tutorial_step+1)} / 6',(33,119),12,GOLD,bold=True)
        if g.coop and g.partner['down']:
            self.text(f'P2 NEEDS HELP / {math.ceil(g.partner["revive"])}s',(951,123),13,GOLD,bold=True)

    def result_comparison(self):
        g=self.game; old=getattr(g,'previous_best',{})
        if getattr(g,'contract',None):
            from challenge_hall import goal_met
            return g.contract+(': mastery earned!' if goal_met(g) else ': goal not met this run. Try another route.')
        if not old: return 'First clear in this rules category.' if g.state=='cleared' else 'Use the warnings and distractions to plan your next route.'
        return f'Compared with prior best: {g.elapsed-old["seconds"]:+.1f}s / {g.steps-old["steps"]:+d} steps (lower is better).'
