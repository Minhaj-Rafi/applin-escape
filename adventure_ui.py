"""Expedition menus and original procedural illustrations."""
import math
import pygame
from expedition import ABILITIES, SKILLS, COSMETICS, TUTORIAL, parse_code
from model import TIERS, SPECIES_ROLES
from art import leaf, seed, berry, applin

TEXT=(243,237,216)
MUTED=(153,176,166)
GREEN=(177,225,153)
GOLD=(247,203,118)
RED=(239,143,133)

ABILITY_HELP = (
    'Hop to safety, leave a short decoy and briefly stun nearby birds.',
    'Rush up to four corridor tiles with a brief shield. Walls stop the dash.',
    'Leave a tempting apple for seven seconds. Birds investigate its location.',
    'Hide your scent for five seconds. Move through danger without a hit.',
)
SPECIES_HELP = {
    'Pidgeotto': 'Tracks your position. Use a loop or conceal yourself in grass.',
    'Cramorant': 'Guards objectives, then pursues when you approach.',
    'Spearow': 'Aims ahead of you. Change direction before its ambush.',
    'Murkrow': 'Mixes pursuit with wandering. Watch both branches.',
    'Talonflame': 'Fast tracker. Let its marked swoop pass, then move.',
}


class ExpeditionUI:
    def init_adventure(self):
        self.skill = self.store.get('skill_v3', 'Standard')
        self.ability = self.store.get('ability_v3', 'Leaf Slip')
        self.coop = self.store.get('coop_v3', False)
        self.cosmetic = self.store.get('cosmetic_v3', 'Orchard')
        if self.skill not in SKILLS: self.skill = 'Standard'
        if self.ability not in ABILITIES: self.ability = 'Leaf Slip'
        if self.cosmetic not in COSMETICS: self.cosmetic = 'Orchard'
        self.particle_fx = self.store.get('particles_v3', True)
        self.adaptive_music = self.store.get('adaptive_v3', True)
        self.challenge_input = ''
        self.challenge_error = ''
        self.autosave_timer = 0.0
        self.partner_timer = 0.0
        self.visual_partner = [1., 1.]
        self.celebrate = 0.0
        self.journal_page = 0
        self.pending_code = None
        self.resume_data = None
        self.character_cache = {}
        self.navigation = []

    def unlocked_cosmetics(self):
        achievements = self.store.get('achievements', [])
        return ['Orchard'] + (['Golden'] if 'First sanctuary' in achievements else []) + \
               (['Moonleaf'] if 'Untouched' in achievements else []) + \
               (['Blossom'] if 'Rescue ranger' in achievements else [])

    def save_expedition(self):
        if self.game and (self.game.state == 'playing' or
                          self.game.state == 'cleared' and self.game.mode == 'campaign' and self.game.tier < 4):
            self.store.set('active_expedition', {'game': self.game.snapshot(),
                                                'campaign': self.campaign_results,'story':self.story_mode})

    def extra_action(self, action):
        if action == 'back': self.binding=None
        if action == 'back' and self.navigation and self.screen in ('adventure','journal','challenge','controls','biome_guide','sanctuary','story','accessibility','object_info','ending','home_activities','home_hub','challenge_hall','profile','records','contract_collection'):
            self.screen, self.return_screen = self.navigation.pop()
        elif action in ('adventure', 'journal', 'challenge'):
            self.navigation.append((self.screen, self.return_screen))
            if self.screen == 'play': self.screen = 'paused'
            self.return_screen = self.screen
            self.screen = action
        elif action == 'continue':
            data = self.store.get('active_expedition', None)
            if data:
                self.resume_data = data
                self.start()
        elif action == 'save_menu':
            self.consume_events()
            self.save_expedition()
            self.game = None
            self.screen = 'menu'
            self.audio.set_biome(None)
        elif action == 'tutorial':
            self.campaign_results = []
            self.start(0, 'tutorial')
        elif action == 'skill':
            self.skill = SKILLS[(SKILLS.index(self.skill)+1)%len(SKILLS)]
            self.store.set('skill_v3', self.skill)
        elif action == 'ability':
            self.ability = ABILITIES[(ABILITIES.index(self.ability)+1)%len(ABILITIES)]
            self.store.set('ability_v3', self.ability)
        elif action == 'coop':
            self.coop = not self.coop
            self.store.set('coop_v3', self.coop)
        elif action == 'cosmetic':
            choices = self.unlocked_cosmetics()
            idx = choices.index(self.cosmetic) if self.cosmetic in choices else 0
            self.cosmetic = choices[(idx+1)%len(choices)]
            self.store.set('cosmetic_v3', self.cosmetic)
        elif action == 'particles':
            self.particle_fx = not self.particle_fx
            self.particles.clear()
            self.store.set('particles_v3', self.particle_fx)
        elif action == 'adaptive':
            self.adaptive_music = not self.adaptive_music
            self.store.set('adaptive_v3', self.adaptive_music)
        elif action == 'journal_next':
            self.journal_page = (self.journal_page+1)%3
        elif action == 'challenge_play':
            try:
                parse_code(self.challenge_input)
                self.pending_code = self.challenge_input
                self.campaign_results = []
                self.start(mode='challenge')
                self.challenge_error = ''
            except ValueError as exc:
                self.challenge_error = str(exc)
        elif action == 'copy_code':
            if self.game:
                self.challenge_input = self.game.code
                self.challenge_error = 'Code shown below. You can also copy it from challenge_code.txt in your save folder.'
                (self.store.directory/'challenge_code.txt').write_text(self.game.code+'\n', encoding='utf-8')
                try:
                    if not pygame.scrap.get_init(): pygame.scrap.init()
                    pygame.scrap.put(pygame.SCRAP_TEXT, (self.game.code+'\0').encode())
                    self.challenge_error = 'Challenge code copied to the clipboard.'
                except pygame.error:
                    pass
                self.navigation.append((self.screen,self.return_screen))
                self.return_screen = self.screen
                self.screen = 'challenge'
        elif action == 'partner_escape' and self.screen == 'play':
            self.game.escape_partner()
            self.consume_events()
        else:
            return False
        self.focus = -1
        return True

    def draw_adventure(self):
        self.header('Pack for the next adventure.', 'Choose your rules before starting. All abilities are available immediately.')
        rows = [
            ('Challenge', self.skill, 'Relaxed: more help. Standard: tactical pursuit. Expert: faster birds.', 'skill'),
            ('Escape ability', self.ability, ABILITY_HELP[ABILITIES.index(self.ability)], 'ability'),
            ('Players', 'Two players' if self.coop else 'Solo', 'Co-op shares seeds, score and escape charges. Both apples must reach the shrine.', 'coop'),
            ('Apple style', self.cosmetic, 'Earned styles only. Rare green shiny colour is random and lasts for one run.', 'cosmetic'),
        ]
        for i,(label,value,caption,action) in enumerate(rows):
            y=149+i*96
            self.panel((43,y,1189,84))
            self.text(label,(65,y+12),21,TEXT,bold=True)
            self.text(caption,(65,y+48),14,MUTED)
            self.button(value,(956,y+14,253,48),action,small=True)
        self.text('Keyboard or controller: choose your bindings in Settings > Controls.',(48,555),17,GREEN)
        self.text('Partner caught? Touch them to help, or they recover at the nest in 8 seconds.', (48,587),16,MUTED)
        self.button('Start selected biome',(48,636,274,52),'practice',True)
        self.button('Five-stage expedition',(337,636,277,52),'campaign')
        self.button('Playable tutorial',(629,636,270,52),'tutorial')
        self.button('Challenge code',(914,636,317,52),'challenge')
        self.button('Back',(48,766,170,44),'back')
        self.button('Collection journal',(247,766,240,44),'journal')
        if self.store.get('active_expedition',None):
            self.button('Continue saved game',(919,766,312,44),'continue',True)

    def draw_challenge(self):
        self.header('One maze. A shared challenge.', 'AE42 uses tactical pursuit. AE31 and AE3 retain their original rules. Replays allow repeat maps.')
        self.panel((44,162,1188,244))
        self.text('TYPE OR PASTE AN AE42, AE31 OR AE3 CODE', (65,183),14,GREEN,bold=True)
        pygame.draw.rect(self.canvas,(12,25,28),(64,224,1146,58),border_radius=8)
        self.text(self.challenge_input or 'AE42-...' , (80,240),22,TEXT)
        self.text('Ctrl+V to paste   /   Backspace to edit   /   Enter to begin', (65,311),16,MUTED)
        if self.challenge_error:
            self.text(self.challenge_error,(65,357),14,GOLD)
        self.button('Play this challenge',(48,438,310,53),'challenge_play',True)
        self.text('Normal adventures still reject previously generated layouts on this computer.',(48,535),18,MUTED)
        self.text('A challenge starts from the beginning; it does not copy someone else\'s progress.',(48,571),18,MUTED)
        self.text('Use Share challenge from the pause or result screen to get your own code.',(48,608),18,MUTED)
        self.button('Back',(48,766,170,44),'back')

    def challenge_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.action('back')
        elif event.key == pygame.K_RETURN:
            self.action('challenge_play')
        elif event.key == pygame.K_BACKSPACE:
            self.challenge_input = self.challenge_input[:-1]
        elif event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
            try:
                if not pygame.scrap.get_init(): pygame.scrap.init()
                raw=pygame.scrap.get(pygame.SCRAP_TEXT)
                if raw: self.challenge_input=raw.decode('utf-8',errors='ignore').strip('\x00 \r\n')[:80].upper()
            except pygame.error:
                self.challenge_error='Clipboard unavailable. Type the code into the field.'
        elif event.unicode and all(c in '0123456789ABCDEFabcdef-' for c in event.unicode):
            self.challenge_input=(self.challenge_input+event.unicode.upper())[:80]

    def draw_journal(self):
        titles=('Meet the flock.', 'Small victories. Lasting memories.', 'Your personal bests.')
        self.header(titles[self.journal_page], 'Explore to reveal entries. Rewards are earned by playing, with no purchases.')
        if self.journal_page == 0:
            seen=self.store.get('seen_species',[])
            for i,(name,tip) in enumerate(SPECIES_HELP.items()):
                y=144+i*94
                self.panel((44,y,1188,84))
                self.canvas.blit(self.sprites.get(name.lower(),72,0),(59,y+4))
                self.text(name if name in seen else 'Undiscovered bird',(154,y+10),23,TEXT)
                self.text(tip if name in seen else 'Explore more biomes to meet this species.',(154,y+47),16,MUTED)
            visited=self.store.get('seen_biomes',[])
            self.text('BIOME STAMPS',(48,647),13,GREEN,bold=True)
            for i,tier in enumerate(TIERS):
                self.text(f'{i+1}. '+(tier.biome if i in visited else 'Unexplored'),(48+(i%3)*402,681+(i//3)*29),15,tier.color if i in visited else MUTED)
        elif self.journal_page == 1:
            achievements=self.store.get('achievements',[])
            goals=[('First sanctuary','Finish any non-tutorial stage. Unlocks Golden apple.'),
                   ('Untouched','Finish a stage without a hit. Unlocks Moonleaf.'),
                   ('Rescue ranger','Rescue both Budew and finish. Unlocks Blossom.'),
                   ('Highland hero','Clear the fifth biome.'),('Better together','Finish a stage with two players.'),
                   ('On foot','Win without spending an escape charge.')]
            for i,(name,tip) in enumerate(goals):
                y=148+i*89
                self.panel((44,y,1188,78))
                self.text('EARNED' if name in achievements else 'TO DISCOVER',(65,y+27),14,GOLD if name in achievements else MUTED)
                self.text(name,(238,y+10),22,TEXT)
                self.text(tip,(238,y+43),16,MUTED)
        else:
            bests=self.store.get('personal_bests',{})
            self.text('Best time and fewest steps may come from different runs. Each ruleset has its own record.',(48,147),16,MUTED)
            rows=list(bests.items())[-9:]
            if not rows: self.text('Reach a sanctuary to set your first record.',(48,222),25,TEXT)
            for i,(key,stats) in enumerate(reversed(rows)):
                parts=key.split('/')
                label=f'Biome {int(parts[0])+1} / {parts[1]} / {"Duo" if parts[2]=="True" else "Solo"} / {parts[3]}'
                y=192+i*56
                self.panel((44,y,1188,49),radius=7)
                self.text(label,(60,y+7),15,TEXT)
                self.text(parts[4].upper()+(' / v3.1' if 'v31' in parts else ' / v3.0'),(61,y+29),10,MUTED)
                self.text(f'{stats["seconds"]:.1f}s   /   {stats["steps"]} steps   /   '+('No-hit achieved' if stats['no_hit'] else 'No-hit pending'),(700,y+16),16,GOLD)
        self.button('Back',(48,766,170,44),'back')
        self.button('Next page',(1030,766,200,44),'journal_next',True)
        self.text(f'{self.journal_page+1} / 3',(640,782),16,MUTED,center=True)

    def hero_sprite(self, size, frame, direction, partner=False):
        style = 'Shiny' if self.game and self.game.shiny[int(partner)] else 'Moonleaf' if partner else self.cosmetic
        gaze=(0,0); blink=False
        if self.game and self.characters and not self.comfort:
            pos=self.game.partner['pos'] if partner else self.game.player
            nearest=min(self.game.enemies,key=lambda e:abs(e.pos[0]-pos[0])+abs(e.pos[1]-pos[1]))
            if abs(nearest.pos[0]-pos[0])+abs(nearest.pos[1]-pos[1]) <= 6:
                sign=lambda n:(n>0)-(n<0)
                gaze=(sign(nearest.pos[0]-pos[0])*(-1 if direction[0]<0 else 1),sign(nearest.pos[1]-pos[1]))
            blink=int(self.game.elapsed*10)%40==39
        pose='idle'
        if self.game and self.characters and not self.comfort:
            pos=self.game.partner['pos'] if partner else self.game.player
            visual=self.visual_partner if partner else self.visual_player
            if abs(pos[0]-visual[0])+abs(pos[1]-visual[1])>.04: pose='run'
            if self.game.escape_cooldown>.6: pose='escape'
            elif gaze!=(0,0): pose='alert'
        key=(size,frame,tuple(direction),style,gaze,blink,pose)
        if key in self.character_cache: return self.character_cache[key]
        sprite=applin(size,frame,direction[0] or 1,gaze,blink)
        # Apply an apple-body palette without recoloring eyes, leaves or transparent pixels.
        if style != 'Orchard':
            colors={'Shiny':(155,211,72),'Golden':(239,192,64),'Moonleaf':(113,172,227),'Blossom':(230,139,182)}
            target=colors[style]
            pixels=pygame.PixelArray(sprite)
            for x in range(size):
                for y in range(size):
                    c=sprite.unmap_rgb(pixels[x,y])
                    if c.a and c.r > c.g*1.25 and c.r > c.b*1.15:
                        shade=max(.40,min(1,c.r/230))
                        pixels[x,y]=(*[int(v*shade) for v in target],c.a)
            del pixels
        if style=='Blossom':
            cx,cy=int(size*.58),int(size*.17)
            for i in range(5):
                a=i*math.tau/5
                pygame.draw.circle(sprite,(249,203,222),(cx+int(math.cos(a)*size*.035),cy+int(math.sin(a)*size*.035)),max(1,size//32))
            pygame.draw.circle(sprite,GOLD,(cx,cy),max(1,size//45))
        if pose=='run':
            sprite=pygame.transform.rotate(sprite,(-4 if frame%2 else 4)*(direction[0] or 1))
            sprite=pygame.transform.smoothscale(sprite,(size,size))
        elif pose=='escape':
            squashed=pygame.transform.smoothscale(sprite,(size,max(1,int(size*.83))))
            sprite=pygame.Surface((size,size),pygame.SRCALPHA); sprite.blit(squashed,(0,int(size*.17)))
            pygame.draw.line(sprite,GREEN,(size*.12,size*.55),(size*.29,size*.55),2)
        elif pose=='alert':
            pygame.draw.line(sprite,GOLD,(size*.16,size*.15),(size*.10,size*.07),2)
            pygame.draw.line(sprite,GOLD,(size*.24,size*.11),(size*.24,size*.02),2)
        if len(self.character_cache)>768: self.character_cache.clear()
        self.character_cache[key]=sprite
        return sprite

    def bird_sprite(self, enemy, size, frame):
        if enemy.direction[1] == 0:
            return self.sprites.get(enemy.species.lower(),size,frame,enemy.direction[0] or 1)
        # Turn into a top view for north/south flight; distinct palettes and crests remain visible.
        key=('bird',enemy.species,size,frame,enemy.direction[1])
        if key in self.character_cache: return self.character_cache[key]
        palettes={'Pidgeotto':((182,139,83),(226,91,55)), 'Cramorant':((70,137,203),(240,190,88)),
                  'Spearow':((172,100,75),(108,64,48)), 'Murkrow':((69,70,109),(160,136,192)),
                  'Talonflame':((220,91,59),(59,62,78))}
        body,accent=palettes[enemy.species]
        s=pygame.Surface((size,size),pygame.SRCALPHA)
        c=size//2; phase=math.sin(frame*math.tau/8)
        spread=int(size*(.28+.12*phase)); d=pygame.draw
        d.polygon(s,accent,[(c,c),(c-spread,c-int(size*.15)),(c-int(size*.35),c+int(size*.20)),(c,c+int(size*.12))])
        d.polygon(s,accent,[(c,c),(c+spread,c-int(size*.15)),(c+int(size*.35),c+int(size*.20)),(c,c+int(size*.12))])
        d.polygon(s,accent,[(c-int(size*.09),int(size*.64)),(c-int(size*.14),int(size*.88)),(c+int(size*.14),int(size*.88)),(c+int(size*.09),int(size*.64))])
        d.ellipse(s,body,(int(size*.37),int(size*.27),int(size*.26),int(size*.45)))
        d.circle(s,body,(c,int(size*.28)),max(3,int(size*.15)))
        d.polygon(s,(244,193,91),[(c-2,int(size*.18)),(c,int(size*.03)),(c+3,int(size*.18))])
        d.line(s,accent,(c,int(size*.29)),(c,int(size*.40)),max(2,size//12))
        if enemy.direction[1]>0: s=pygame.transform.flip(s,False,True)
        self.character_cache[key]=s
        return s

    def draw_world_extras(self):
        g=self.game; d=pygame.draw
        animated=self.characters and not self.comfort
        for cell in g.rescues:
            x,y=self.center(cell); r=max(6,self.cell//4)
            bob=int(math.sin(g.elapsed*2)*1.5) if animated else 0
            y+=bob
            d.ellipse(self.canvas,(211,236,135),(x-r,y-r,2*r,2*r))
            leaf(self.canvas,(x-r//2,y-r),r*.8,(105,185,120),-.8)
            leaf(self.canvas,(x+r//2,y-r),r*.8,(139,206,117),.8)
            for dx in (-r//3,r//3): d.circle(self.canvas,(40,61,48),(x+dx,y),1)
            # Small twig enclosure opens when rescued, no outline around the collectible.
            for dx in (-r-3,r+2): d.line(self.canvas,(174,117,72),(x+dx,y-r),(x+dx,y+r),2)
            d.line(self.canvas,(174,117,72),(x-r-3,y+r),(x+r+2,y+r),2)
        x,y=self.center(g.switch)
        if not (g.rules_version>=31 and g.tier==1):
            d.polygon(self.canvas,(91,218,218),[(x,y-7),(x+9,y),(x,y+7),(x-9,y)])
            d.circle(self.canvas,(244,244,219),(x,y),3)
        if g.bridge and not (g.rules_version>=31 and g.tier in (1,3)):
            p,a,b=g.bridge
            x,y=self.center(p); r=max(7,self.cell//2-2)
            if g.bridge_open:
                for dy in (-4,0,4): d.line(self.canvas,(99,214,194),(x-r,y+dy),(x+r,y+dy),2)
                self.text(str(math.ceil(g.bridge_time)),(x,y-self.cell),11,GREEN,center=True)
            else:
                d.line(self.canvas,(96,158,165),(x-r,y-3),(x-r//2,y+3),3)
                d.line(self.canvas,(96,158,165),(x+r//2,y+3),(x+r,y-3),3)
        if g.ledge:
            _,a,b=g.ledge; x,y=self.center(a)
            dx=(b[0]-a[0])//2; dy=(b[1]-a[1])//2
            d.line(self.canvas,(249,239,203),(x-dx*4,y-dy*4),(x+dx*5,y+dy*5),3)
            d.polygon(self.canvas,(249,239,203),[(x+dx*9,y+dy*9),(x+dx*2-dy*4,y+dy*2+dx*4),(x+dx*2+dy*4,y+dy*2-dx*4)])
        for e in g.enemies:
            if e.warning > 0 or e.mood=='swoop':
                for p in e.attack:
                    x,y=self.center(p)
                    d.circle(self.canvas,(246,190,105),(x,y),max(3,self.cell//5),2)
                x,y=self.center(e.pos)
                self.text('!',(x,y-self.cell*.7),17,GOLD,bold=True,center=True)
        if animated:
            for pos in (g.player,g.partner['pos']) if g.coop else (g.player,):
                if pos in g.hidden_cells:
                    x,y=self.center(pos)
                    for i in (-1,1):
                        angle=i*(.5+math.sin(g.elapsed*6)*.12)
                        leaf(self.canvas,(x+i*self.cell*.28,y+self.cell*.23),max(3,self.cell*.14),(174,207,124),angle)
        if g.mode=='tutorial':
            targets = list(g.hidden_cells) if g.tutorial_step==1 else list(g.seeds) if g.tutorial_step==3 else [g.exit] if g.tutorial_step==4 and not g.seeds else []
            if targets:
                p=min(targets,key=lambda p:abs(p[0]-g.player[0])+abs(p[1]-g.player[1]))
                x,y=self.center(p)
                d.polygon(self.canvas,GOLD,[(x,y-14),(x+5,y-20),(x,y-26),(x-5,y-20)],2)

    def extra_update(self, dt):
        g=self.game
        self.celebrate=max(0,self.celebrate-dt)
        factor=1 if self.comfort or not self.characters else min(1,dt*24)
        for i in range(2): self.visual_partner[i]+=(g.partner['pos'][i]-self.visual_partner[i])*factor
        if g.board_revision != self.render_revision:
            offset=self.camera_offset[:]
            self.prepare_board()
            self.camera_offset=offset
            self.camera()
            self.render_revision=g.board_revision
        self.autosave_timer+=dt
        if self.autosave_timer>=3:
            self.save_expedition()
            self.autosave_timer=0
        danger=any(e.mood in ('chase','warning','swoop') for e in g.enemies)
        self.audio.set_danger(danger and self.adaptive_music)
