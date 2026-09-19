"""Applin Escape — an original, unofficial Pokémon fan-game demo."""
import argparse
import math
import os
from pathlib import Path
import random
import sqlite3
import sys
import tempfile

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
try:
    import pygame
except ImportError:
    raise SystemExit('Pygame is missing. Double-click PLAY_WINDOWS.bat or run: python -m pip install -r requirements.txt')

from model import Store, Session, TIERS, DIRS, ROSTERS
from art import Sprites, seed, berry, heart, leaf
from audio import Audio
from world import World, TILE
from compose import TRACKS

W, H = 1280, 840
BG = (14, 24, 27)
PANEL = (23, 37, 39)
EDGE = (44, 63, 61)
TEXT = (243, 237, 216)
MUTED = (153, 176, 166)
GREEN = (177, 225, 153)
GOLD = (247, 203, 118)
RED = (239, 143, 133)


class App:
    def __init__(self, save_dir=None):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        info = pygame.display.Info()
        self.window_size = (min(1280, info.current_w), min(840, max(525, info.current_h - 70)))
        self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption('Applin Escape | Sunseed Edition')
        self.canvas = pygame.Surface((W, H))
        self.store = Store(save_dir)
        self.audio = Audio(self.store.get('music', True), self.store.get('effects', True))
        self.comfort = self.store.get('stationary_v22', False)
        self.motion = False if self.comfort else self.store.get('decoration_v22', False)
        self.characters = self.store.get('characters_v23', True)
        self.trail = self.store.get('trail', True)
        self.sprites = Sprites()
        pygame.display.set_icon(self.sprites.get('applin', 64, 0))
        self.font_cache = {}
        self.running = True
        self.screen = 'menu'
        self.return_screen = 'menu'
        self.selected = 0
        self.game = None
        self.buttons = []
        self.focus = -1
        self.fullscreen = False
        self.clock = pygame.time.Clock()
        self.t = 0.0
        self.move_timer = 0.0
        self.held_direction = (1, 0)
        self.particles = []
        self.visual_player = [1., 1.]
        self.visual_enemies = []
        self.campaign_results = []
        self.fx_rng = random.Random(13)
        self.error = ''
        self.cached_summary = self.store.summary()
        self.board = None
        self.overview = True
        self.draw()

    def font(self, size, serif=False, bold=False):
        key = size, serif, bold
        if key not in self.font_cache:
            family = 'georgia,dejavuserif' if serif else 'segoeui,dejavusans'
            self.font_cache[key] = pygame.font.SysFont(family, size, bold=bold)
        return self.font_cache[key]

    def text(self, value, pos, size=20, color=TEXT, serif=False, bold=False, center=False):
        surf = self.font(size, serif, bold).render(str(value), True, color)
        rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        self.canvas.blit(surf, rect)
        return rect

    def panel(self, rect, color=PANEL, radius=18, border=True):
        pygame.draw.rect(self.canvas, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.canvas, EDGE, rect, 1, border_radius=radius)

    def mouse(self):
        width, height = self.window.get_size()
        scale = min(width / W, height / H)
        x, y = pygame.mouse.get_pos()
        return ((x - (width-W*scale)/2) / scale, (y - (height-H*scale)/2) / scale)

    def button(self, label, rect, action, primary=False, small=False):
        rect = pygame.Rect(rect)
        focused = self.focus == len(self.buttons)
        hover = rect.collidepoint(self.mouse()) or focused
        fill = GREEN if primary else ((52, 73, 64) if hover else (32, 49, 48))
        pygame.draw.rect(self.canvas, fill, rect, border_radius=10)
        pygame.draw.rect(self.canvas, GREEN if hover else EDGE, rect, 2 if hover else 1, border_radius=10)
        self.text(label, rect.center, 16 if small else 19, BG if primary else TEXT, bold=primary, center=True)
        self.buttons.append((rect, action))

    def start(self, tier=0, mode='practice'):
        try:
            self.game = Session(self.store, tier, mode)
            self.shrine_open = 0.0
            self.overview = True
            self.prepare_board()
            self.audio.set_biome(tier)
            self.visual_player = list(map(float, self.game.player))
            self.visual_enemies = [list(map(float, e.pos)) for e in self.game.enemies]
            self.particles = []
            self.move_timer = .2
            self.screen = 'play'
            self.focus = -1
            self.error = ''
            self.cached_summary = self.store.summary()
        except (OSError, RuntimeError, sqlite3.Error) as exc:
            self.error = 'Could not start/save the maze: ' + str(exc)
            self.screen = 'error'

    def prepare_board(self):
        self.camera_offset = [0.,0.]
        self.world = World(self.game)
        self.board = self.world.surface
        self.camera()

    def camera(self):
        g=self.game
        full=self.overview or self.comfort
        self.cell=min(880//g.config.width,610//g.config.height) if full else 36
        ww,wh=g.config.width*self.cell,g.config.height*self.cell
        target=getattr(self,'visual_player',g.player)
        if not hasattr(self,'camera_offset'):
            self.camera_offset=[0.,0.]
        for i,(length,viewport) in enumerate(((ww,880),(wh,610))):
            if full or length<=viewport:
                self.camera_offset[i]=0
                continue
            pos=(target[i]+.5)*self.cell
            offset=self.camera_offset[i]
            # The middle 44% is a stationary zone. Camera has no independent drift.
            lo,hi=viewport*.28,viewport*.72
            if pos-offset<lo:
                offset=pos-lo
            elif pos-offset>hi:
                offset=pos-hi
            self.camera_offset[i]=max(0,min(length-viewport,offset))
        self.ox=30+(880-ww)//2 if ww<=880 else 30-int(self.camera_offset[0])
        self.oy=150+(610-wh)//2 if wh<=610 else 150-int(self.camera_offset[1])

    def minimap(self):
        g=self.game
        area=pygame.Rect(962,623,266,106)
        scale=min(area.w/g.config.width,area.h/g.config.height)
        ww,hh=int(g.config.width*scale),int(g.config.height*scale)
        x,y=area.x+(area.w-ww)//2,area.y+(area.h-hh)//2
        self.canvas.blit(pygame.transform.scale(self.world.surface,(ww,hh)),(x,y))
        for pos,color,r in [(g.player,(255,251,215),3),(g.exit,GREEN,3)]+[(q,GOLD,2) for q in g.seeds]+[(e.pos,RED,2) for e in g.enemies]:
            pygame.draw.circle(self.canvas,color,(int(x+(pos[0]+.5)*scale),int(y+(pos[1]+.5)*scale)),r)
        if not self.overview:
            view=pygame.Rect(x+(30-self.ox)/self.cell*scale,y+(150-self.oy)/self.cell*scale,880/self.cell*scale,610/self.cell*scale)
            view.clamp_ip(pygame.Rect(x,y,ww,hh))
            pygame.draw.rect(self.canvas,(249,237,205),view,1)

    def center(self, p):
        return int(self.ox+(p[0]+.5)*self.cell), int(self.oy+(p[1]+.5)*self.cell)

    def action(self, action):
        self.audio.play('click')
        self.focus = -1
        if action.startswith('tier:'):
            self.selected = int(action.split(':')[1])
        elif action == 'campaign':
            self.campaign_results = []
            self.start(0, 'campaign')
        elif action == 'practice':
            self.campaign_results = []
            self.start(self.selected, 'practice')
        elif action in ('help', 'settings', 'records'):
            self.return_screen = self.screen
            self.screen = action
        elif action == 'back':
            self.screen = self.return_screen
        elif action == 'overview':
            if self.comfort:
                self.game.notify('Comfort Mode keeps the map still. Camera options are in Settings.')
            else:
                self.overview = not self.overview
            self.camera()
        elif action == 'pause':
            self.screen = 'paused'
        elif action == 'resume':
            self.screen = 'play'
            self.move_timer = .2
        elif action == 'escape' and self.screen == 'play':
            self.game.escape()
            self.consume_events()
        elif action == 'end':
            self.game.abandon()
            self.screen = 'menu'
            self.audio.set_biome(None)
            self.cached_summary = self.store.summary()
        elif action == 'menu':
            self.screen = 'menu'
            self.audio.set_biome(None)
            self.cached_summary = self.store.summary()
        elif action == 'next':
            self.start(self.game.tier+1, 'campaign')
        elif action == 'retry':
            self.start(self.game.tier, self.game.mode)
        elif action == 'music':
            self.audio.music = not self.audio.music
            self.audio.apply()
            self.store.set('music', self.audio.music)
        elif action == 'effects':
            self.audio.effects = not self.audio.effects
            self.store.set('effects', self.audio.effects)
        elif action == 'comfort':
            self.comfort = not self.comfort
            self.store.set('stationary_v22', self.comfort)
            self.motion = False if self.comfort else self.store.get('decoration_v22', False)
            self.overview = True
            self.particles.clear()
            if self.game:
                self.camera()
        elif action == 'characters':
            self.characters = not self.characters
            if not self.characters:
                self.particles.clear()
            self.store.set('characters_v23',self.characters)
        elif action == 'motion':
            if not self.comfort:
                self.motion = not self.motion
                self.store.set('decoration_v22', self.motion)
        elif action == 'trail':
            self.trail = not self.trail
            self.store.set('trail', self.trail)
        elif action == 'fullscreen':
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                self.window_size = self.window.get_size()
                self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        elif action == 'quit':
            self.running = False

    def events(self):
        key_dirs = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
                    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1), pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0)}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.WINDOWFOCUSLOST and self.screen == 'play':
                self.screen = 'paused'
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, action in self.buttons:
                    if rect.collidepoint(self.mouse()):
                        self.action(action)
                        break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.action('fullscreen')
                elif event.key == pygame.K_m:
                    self.action('music')
                elif event.key == pygame.K_TAB and self.screen != 'play':
                    self.focus = (self.focus+1) % max(1, len(self.buttons))
                elif event.key == pygame.K_RETURN:
                    if self.screen != 'play' and 0 <= self.focus < len(self.buttons):
                        self.action(self.buttons[self.focus][1])
                    elif self.screen == 'menu':
                        self.action('campaign')
                    elif self.screen == 'paused':
                        self.action('resume')
                    elif self.screen == 'result':
                        self.action(self.result_primary())
                elif event.key == pygame.K_ESCAPE:
                    if self.screen == 'play':
                        self.screen = 'paused'
                    elif self.screen == 'paused':
                        self.action('resume')
                    elif self.screen in ('help', 'settings', 'records'):
                        self.action('back')
                elif self.screen == 'menu' and pygame.K_1 <= event.key <= pygame.K_5:
                    self.selected = event.key-pygame.K_1
                elif self.screen == 'play':
                    if event.key in key_dirs:
                        self.held_direction = key_dirs[event.key]
                        if self.move_timer <= 0:
                            self.game.move(self.held_direction)
                            self.move_timer = Session.PLAYER_DELAY
                            self.consume_events()
                    elif event.key == pygame.K_SPACE:
                        self.action('escape')
                    elif event.key == pygame.K_p:
                        self.screen = 'paused'
                    elif event.key == pygame.K_v:
                        self.action('overview')
                    elif event.key == pygame.K_t:
                        self.action('trail')
                    elif event.key == pygame.K_F1:
                        self.screen = 'paused'
                        self.action('help')

    def consume_events(self):
        g = self.game
        for kind, cell in g.events:
            self.audio.play(kind)
            if kind in ('seed', 'berry', 'escape', 'land', 'hit', 'cleared'):
                color = GOLD if kind == 'seed' else RED if kind == 'hit' else GREEN
                x, y = self.center(cell)
                for _ in range(20 if self.characters and not self.comfort else 0):
                    angle = self.fx_rng.uniform(0, math.tau)
                    speed = self.fx_rng.uniform(20, 105)
                    self.particles.append([x, y, math.cos(angle)*speed, math.sin(angle)*speed, .7, color])
            if kind in ('land', 'respawn'):
                self.visual_player = list(map(float, g.player))
            if kind == 'respawn':
                self.visual_enemies = [list(map(float, e.pos)) for e in g.enemies]
            if kind in ('cleared', 'caught'):
                self.screen = 'result'
                self.focus = -1
                self.cached_summary = self.store.summary()
                if kind == 'cleared' and g.mode == 'campaign':
                    self.campaign_results.append((g.elapsed, g.steps, g.score))
        g.events.clear()

    def update(self, dt):
        self.t += dt
        if self.screen != 'play':
            return
        g = self.game
        self.move_timer -= dt
        keys = pygame.key.get_pressed()
        held = []
        for pair, direction in [((pygame.K_UP, pygame.K_w), DIRS[0]), ((pygame.K_RIGHT, pygame.K_d), DIRS[1]),
                                ((pygame.K_DOWN, pygame.K_s), DIRS[2]), ((pygame.K_LEFT, pygame.K_a), DIRS[3])]:
            if any(keys[k] for k in pair):
                held.append(direction)
        if held and self.move_timer <= 0:
            direction = self.held_direction if self.held_direction in held else held[0]
            self.held_direction = direction
            # Buffered turns: while the requested turn is blocked, continue forward if held.
            moved = g.move(direction)
            if not moved and g.direction in held and g.direction != direction:
                g.move(g.direction)
            self.move_timer = Session.PLAYER_DELAY
        g.update(dt)
        self.consume_events()
        self.shrine_open = min(1.0,self.shrine_open+dt/1.1) if not g.seeds else 0.0
        factor = 1 if self.comfort else min(1,dt*24)
        for i in range(2):
            self.visual_player[i] += (g.player[i]-self.visual_player[i])*factor
        for enemy, visual in zip(g.enemies, self.visual_enemies):
            for i in range(2):
                visual[i] += (enemy.pos[i]-visual[i])*factor
        for p in self.particles:
            p[0] += p[2]*dt
            p[1] += p[3]*dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]

    def header(self, label, caption):
        self.text('ORCHARD / FIELD NOTES', (42, 24), 13, GREEN, bold=True)
        self.text(label, (40, 47), 36, TEXT, serif=True)
        self.text(caption, (42, 99), 16, MUTED)

    def draw_menu(self):
        self.text('AN UNOFFICIAL POKEMON FAN GAME', (46, 28), 12, GREEN, bold=True)
        self.button('How to play', (823, 23, 130, 38), 'help', small=True)
        self.button('Records', (967, 23, 106, 38), 'records', small=True)
        self.button('Settings', (1087, 23, 145, 38), 'settings', small=True)
        self.text('A small apple.', (45, 104), 57, TEXT, serif=True)
        self.text('A very big escape.', (45, 169), 57, GREEN, serif=True)
        self.text('Save Applin from a flock of roaming bird Pokemon.', (49, 254), 19, MUTED)
        self.text('Read the maze. Outsmart the chase. Find sanctuary.', (49, 285), 19, MUTED)
        self.button('Begin five-stage expedition', (48, 340, 361, 55), 'campaign', True)
        self.button('Play selected tier', (425, 340, 233, 55), 'practice')
        self.text('ENTER  expedition     /     1-5  select tier', (49, 411), 14, MUTED)
        # Original illustrated hero vignette.
        self.panel((732, 91, 500, 351), (29, 46, 42), radius=26)
        for i in range(6):
            pygame.draw.arc(self.canvas, (45, 67, 52), (778+i*11, 105+i*13, 378-i*22, 306-i*26), .1, 5.8, 1)
        pygame.draw.ellipse(self.canvas, (42, 63, 46), (777, 333, 396,  60))
        frame = int(self.t*6) % 8 if self.characters and not self.comfort else 0
        self.canvas.blit(self.sprites.get('applin', 210, frame), (779, 191))
        self.canvas.blit(self.sprites.get('cramorant', 220, frame, -1), (993, 127))
        for i in range(8):
            leaf(self.canvas, (769+i*59, 122+(i*47)%260), 5, (123, 158, 92), (self.t*.3 if self.motion else 0)+i)
        self.text('THE BIOME EXPEDITION', (980, 413), 12, GREEN, bold=True, center=True)
        self.text('CHOOSE YOUR CHALLENGE', (48, 470), 13, MUTED, bold=True)
        for i, tier in enumerate(TIERS):
            x = 48+i*240
            rect = pygame.Rect(x, 503, 224, 211)
            self.panel(rect, (36, 54, 46) if i == self.selected else PANEL, 14)
            if i == self.selected:
                pygame.draw.rect(self.canvas, tier.color, rect, 2, border_radius=14)
            self.text(f'0{i+1}', (x+17, 518), 25, tier.color, serif=True)
            self.text(tier.name, (x+17, 557), 17, TEXT, bold=True)
            self.text(tier.biome, (x+17, 588), 12, MUTED)
            self.text(f'{tier.enemies} birds  /  {tier.escapes} escapes', (x+17, 615), 14, MUTED)
            self.button('Selected' if i == self.selected else 'Select tier', (x+16, 652, 192, 43), f'tier:{i}', small=True)
        count, wins, best = self.cached_summary
        self.text(f'{count} unique maps explored     /     {wins} stages cleared     /     best {best:,}', (48, 754), 16, MUTED)
        self.text('Five landscapes / Five original soundtracks / Offline single-player', (48, 796), 12, MUTED)
        self.button('Quit', (1120, 763, 112,  40), 'quit', small=True)

    def draw_game(self):
        g = self.game
        tier = g.config
        self.text('APPLIN ESCAPE', (30, 23), 13, GREEN, bold=True)
        self.text(tier.biome, (28, 47), 33, TEXT, serif=True)
        self.text(f'{g.mode.upper()}   /   STAGE {g.tier+1:02d}   /   {tier.name}', (31, 101), 13, tier.color, bold=True)
        self.button('Pause  [P]', (1090,  30, 159, 43), 'pause', small=True)
        self.text('WASD / arrows to move', (827, 42), 15, MUTED)
        self.panel((20, 139, 900, 636), (19, 33, 33), 16)
        self.camera()
        self.canvas.set_clip((30,150,880,610))
        self.world.draw(self.canvas,(self.ox,self.oy),self.cell,self.t,self.motion)
        # Reduce scenery competition without changing the biome palette or collisions.
        scenery_shade = pygame.Surface((880,610),pygame.SRCALPHA)
        scenery_shade.fill((8,18,24, 40))
        self.canvas.blit(scenery_shade,(30,150))
        if self.trail:
            for pos in g.visited:
                pygame.draw.circle(self.canvas, (78, 108, 79), self.center(pos), 2)
        for cell in g.dew:
            pygame.draw.circle(self.canvas, (246, 244, 190), self.center(cell), 2)
        for cell in g.seeds:
            seed(self.canvas, self.center(cell), max(8, self.cell//4), self.t if self.characters and not self.comfort else 0)
        for cell in g.berries:
            berry(self.canvas, self.center(cell), max(8, self.cell//4), self.t if self.characters and not self.comfort else 0)
        frame = int(self.t*10) % 8 if self.characters and not self.comfort else 0
        size = int(self.cell*1.48)
        if g.decoy_time > 0:
            decoy = self.sprites.get('applin', size, 0).copy()
            decoy.set_alpha(100)
            x, y = self.center(g.decoy)
            self.canvas.blit(decoy, (x-size//2, y-size//2))
        for index,(e, visual) in enumerate(zip(g.enemies, self.visual_enemies)):
            x,y=self.center(visual)
            pygame.draw.ellipse(self.canvas,(45,57, 50),(x-self.cell//3,y+self.cell//5,self.cell*2//3,max(3,self.cell//5)))
            flight_frame=(frame+index*2)%8 if self.characters and not self.comfort else 0
            if e.stunned>0:flight_frame=0
            sprite=self.sprites.get(e.species.lower(),size,flight_frame,e.direction[0] or 1)
            self.canvas.blit(sprite,(x-size//2,y-size//2-max(2,self.cell//8)))
            if e.stunned > 0:
                pygame.draw.circle(self.canvas, GOLD, (x, y-self.cell//2), 3)
            elif e.mood == 'chase':
                pygame.draw.circle(self.canvas, RED, (x, y-self.cell//2), 2)
        x, y = self.center(self.visual_player)
        if g.invulnerable > 0:
            pygame.draw.circle(self.canvas, GREEN, (x, y), self.cell//2, 2)
        self.canvas.blit(self.sprites.get('applin', size, frame, g.direction[0] or 1), (x-size//2, y-size//2))
        for x, y, vx, vy, life, color in self.particles:
            leaf(self.canvas, (int(x), int(y)), max(1, life*6), color, self.t*3)
        self.draw_exit_marker()
        self.canvas.set_clip(None)
        self.panel((940, 139, 310, 636), radius=16)
        self.text('KEEP APPLIN SAFE', (960,153),13,MUTED,bold=True)
        for i in range(tier.hearts):
            heart(self.canvas,974+i*31,185,i<g.health)
        self.text(f'{int(g.elapsed)//60:02d}:{int(g.elapsed)%60:02d}',(960,204),37,TEXT)
        self.text('TIME',(962,251),11,MUTED,bold=True)
        self.text(f'{g.steps:,}',(1130,211),27,TEXT)
        self.text('STEPS',(1130,251),11,MUTED,bold=True)
        self.text(f'SUN SEEDS   {tier.seeds-len(g.seeds)} / {tier.seeds}',(962,280),19,GOLD,bold=True)
        for i in range(tier.seeds):
            width=260/tier.seeds
            rect=pygame.Rect(962+i*width,310,width-4,9)
            pygame.draw.rect(self.canvas,GOLD if i<tier.seeds-len(g.seeds) else EDGE,rect,border_radius=3)
        self.text('Follow the light to the shrine' if not g.seeds else 'Gather every seed for the shrine',(962,324),12,MUTED)
        self.text(f'LEAF SLIP / {g.escapes} left',(962,343),17,GREEN,bold=True)
        self.button('Escape  [SPACE]',(960,375,270,43),'escape',True)
        status = 'Shield active' if g.invulnerable > 0 else 'Birds slowed' if g.slow_time > 0 else 'Concealed in tall grass' if g.player in g.hidden_cells else 'Watch the trails'
        self.text(status,(962,430),14,MUTED)
        pygame.draw.line(self.canvas,EDGE,(960,459),(1230,459))
        statuses=self.predator_statuses()
        chasing=sum(status=='CHASING' for _,status in statuses)
        self.text(f'PREDATORS {len(statuses)} / CHASING {chasing}',(961,473),16,RED if chasing else TEXT,bold=True)
        for i,(enemy,status) in enumerate(statuses):
            y=504+i*24
            self.canvas.blit(self.sprites.get(enemy.species.lower(),25,0),(960,y-3))
            self.text(enemy.species,(990,y),14,TEXT)
            self.text(status,(1133,y+1),11,RED if status=='CHASING' else GOLD if status=='STUNNED' else MUTED,bold=True)
        self.text(f'SCORE {g.score:,} / HITS {g.hits}',(962,632),15,GOLD)
        self.text(f'DEW {g.dew_collected}/{g.initial_dew}',(962,657),12,MUTED)
        seed(self.canvas,(972,692),8,0)
        self.text('Seed',(986,683),12,TEXT)
        berry(self.canvas,(1052,692),7)
        self.text('Berry',(1065,683),12,TEXT)
        pygame.draw.rect(self.canvas,(182,144,88),(1130,685,14,16),3)
        self.text('Exit',(1150,683),12,TEXT)
        self.text('Seeds fill the bar. The shrine is home.',(962,711),12,MUTED)
        self.button('Comfort ON / map stays still' if self.comfort else 'V  Full map / quiet camera',
                    (960,737,270,27),'overview',small=True)
        notice = g.notice if g.notice_time > 0 else f'{TRACKS[g.tier][1]}  /  {len(g.enemies)} pursuers  /  V map  /  M music  /  F1 guide'
        self.text(notice, (30, 793), 16, GREEN if g.notice_time > 0 else MUTED)

    def predator_statuses(self):
        return [(enemy, 'STUNNED' if enemy.stunned>0 else 'DECOY' if self.game.decoy_time>0 else
                 'CHASING' if enemy.mood=='chase' else 'PATROL') for enemy in self.game.enemies]

    def draw_exit_marker(self):
        g=self.game
        x,y=self.center(g.exit)
        r=max(14,self.cell//2)
        d=pygame.draw
        d.ellipse(self.canvas,(42,52, 50),(x-r-3,y+r-3,2*r+6,7))
        # Ivory columns and a plum roof read across green, amber and blue terrain.
        for dx in (-r+2,r-5):
            d.rect(self.canvas,(231,215,177),(x+dx,y-r//2,4,r+r//2))
        d.polygon(self.canvas,(94,68,112),[(x-r-3,y-r//2),(x,y-r-6),(x+r+3,y-r//2)])
        d.line(self.canvas,(192,149,116),(x-r-2,y-r//2),(x+r+2,y-r//2),2)
        animated=self.characters and not self.comfort
        opened=0.0 if g.seeds else self.shrine_open if animated else 1.0
        inner=pygame.Rect(x-r+7,y-r//2+2,max(8,2*r-14),r+r//2-3)
        d.rect(self.canvas,(126,196,148),inner)
        d.rect(self.canvas,(239,252,183),inner.inflate(-4,-2))
        panel_width=max(0,int(inner.w/2*(1-opened)))
        if panel_width:
            for px in (inner.left,inner.right-panel_width):
                d.rect(self.canvas,(139,90,49),(px,inner.y,panel_width,inner.h))
                d.line(self.canvas,(195,143,77),(px+1,inner.y+1),(px+1,inner.bottom-1),1)
        if g.seeds:
            d.circle(self.canvas,(250,213,117),(x+2,y+3),2)
        elif animated and opened>.5:
            # Gentle, local motes only; no strobe, screen flash or camera shake.
            for i in range(3):
                phase=(g.elapsed*.35+i/3)%1
                px=x+int(math.sin(i*2+g.elapsed)*r*.35)
                py=y+r-int(phase*(r+5))
                d.circle(self.canvas,(242,246,174),(px,py),1)
        d.rect(self.canvas,(173,159,127),(x-r,y+r-1,2*r,3))
        d.polygon(self.canvas,(231,176,103),[(x-r-1,y-2),(x-r-5,y+5),(x-r-1,y+4)])
        d.polygon(self.canvas,(231,176,103),[(x+r,y-2),(x+r+4,y+5),(x+r,y+4)])

    def backdrop(self):
        if self.game and self.return_screen == 'paused':
            self.draw_game()
            shade = pygame.Surface((W, H), pygame.SRCALPHA)
            shade.fill((10, 18, 22, 235))
            self.canvas.blit(shade, (0, 0))
        self.buttons = []

    def draw_help(self):
        self.backdrop()
        self.header('A field guide to getting home.', 'All five tiers are available in practice. Expedition mode takes you through them in order.')
        items = [
            ('01', 'Gather the light', 'Collect every gold sun seed, then step onto the sanctuary gate.', 'Small dew drops are optional: each adds 10 points.'),
            ('02', 'Read the flock', 'Pidgeotto, Spearow, Murkrow, Talonflame and Cramorant each have a role.', 'Tall grass reduces detection. Blue berries slow the flock for 6 seconds.'),
            ('03', 'Make your escape', 'SPACE uses one Leaf Slip: hop to a safer corridor and leave a decoy.', 'You gain a 2-second shield; nearby birds pause. Charges do not refill.'),
            ('04', 'Keep your footing', 'Getting caught costs a heart and sends you back to the nest.', 'Collected items stay collected. Run out of hearts and the attempt ends.'),
        ]
        for i, (number, title, a, b) in enumerate(items):
            y = 159+i*125
            self.panel((42, y, 1190, 108))
            self.text(number, (65, y+27), 34, GREEN, serif=True)
            self.text(title, (132, y+15), 22, TEXT, bold=True)
            self.text(a, (132, y+49), 17, MUTED)
            self.text(b, (132, y+77), 15, MUTED)
        self.text('WASD / arrows: move    SPACE: escape    P / ESC: pause    V: map    M: music    F11: fullscreen', (48, 688), 17, TEXT)
        self.text('Full map is the default. V enables the optional camera. Character and scenery animation have separate settings.', (48, 723), 15, MUTED)
        self.button('Back', (48, 766, 170, 44), 'back', True)

    def draw_settings(self):
        self.backdrop()
        self.header('Make yourself at home.', 'Settings are saved automatically on this computer.')
        options = [
            ('Comfort Mode', 'Locks the full map and disables character animation', self.comfort, 'comfort'),
            ('Music', 'Five original biome themes; changes automatically with the stage', self.audio.music, 'music'),
            ('Sound effects', 'Collectibles, Leaf Slip, close calls and victory', self.audio.effects, 'effects'),
            ('Character animation', 'Wingbeats, item highlights, collection bursts and shrine doors', self.characters, 'characters'),
            ('Scenery animation', 'Disabled by Comfort Mode' if self.comfort else 'Optional bobbing, particles, ripples and movement smoothing', self.motion, 'motion'),
            ('Footstep trail', 'Show the corridors you have visited', self.trail, 'trail'),
            ('Fullscreen', 'Also available with F11', self.fullscreen, 'fullscreen'),
        ]
        for i, (label, caption, value, action) in enumerate(options):
            y = 148+i*75
            self.panel((43, y, 1189, 67))
            self.text(label, (65, y+8), 23, TEXT)
            self.text(caption, (65, y+38), 14, MUTED)
            self.button('ON' if value else 'OFF', (1074, y+12, 132, 42), action, value)
        self.text('Audio ready' if self.audio.available else 'Audio unavailable on this device; the game remains playable.', (49, 704), 16, MUTED)
        self.button('Back', (48, 766, 170, 44), 'back', True)

    def draw_records(self):
        self.header('Your orchard journal.', 'Local results, including cleared, caught and abandoned attempts. No online account needed.')
        count, wins, best = self.store.summary()
        for i, (label, value) in enumerate((('UNIQUE MAPS', count), ('STAGES CLEARED', wins), ('BEST STAGE SCORE', f'{best:,}'))):
            x = 44+i*401
            self.panel((x, 151, 386, 112))
            self.text(label, (x+22, 169), 13, MUTED, bold=True)
            self.text(value, (x+22, 197), 36, GREEN)
        self.text('TIER', (63, 302), 14, MUTED)
        self.text('RESULT', (330, 302), 14, MUTED)
        self.text('TIME', (559, 302), 14, MUTED)
        self.text('STEPS', (736, 302), 14, MUTED)
        self.text('ESCAPES', (909, 302), 14, MUTED)
        self.text('SCORE', (1100, 302), 14, MUTED)
        records = self.store.records()
        if not records:
            self.text('Your first adventure is still ahead of you.', (65, 376), 24, TEXT, serif=True)
        for i, (tier, outcome, seconds, steps, escapes, score) in enumerate(records):
            y = 340+i* 49
            self.panel((44, y, 1188, 42), (24, 39, 39), 6, False)
            for value, x, color in ((TIERS[tier].name, 63, TEXT), (outcome.upper(), 330, GREEN if outcome == 'cleared' else MUTED),
                                    (f'{seconds:.1f}s', 559, TEXT), (steps, 736, TEXT), (escapes, 909, TEXT), (f'{score:,}', 1100, GOLD)):
                self.text(value, (x, y+10), 16, color)
        self.button('Back', (48, 766, 170, 44), 'back', True)

    def result_primary(self):
        if self.game.state == 'cleared' and self.game.mode == 'campaign':
            return 'next' if self.game.tier < 4 else 'menu'
        return 'retry'

    def draw_overlay(self):
        self.draw_game()
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((7, 16, 19, 220))
        self.canvas.blit(shade, (0, 0))
        self.buttons = []
        self.panel((300, 127, 680, 596), (26, 42, 40), 25)
        if self.screen == 'paused':
            self.canvas.blit(self.sprites.get('applin', 112, 0), (584, 148))
            self.text('A moment in the shade.', (640, 287), 37, TEXT, serif=True, center=True)
            self.text('Applin is safe. The timer and flock are paused.', (640, 338), 17, MUTED, center=True)
            self.button('Resume adventure', (373, 391, 534, 52), 'resume', True)
            self.button('Settings', (373, 458, 257, 47), 'settings')
            self.button('How to play', (650, 458, 257, 47), 'help')
            self.button('End attempt & return to menu', (373, 522, 534, 47), 'end')
            self.text('Ending records this attempt as abandoned.', (640, 615), 15, MUTED, center=True)
        else:
            g = self.game
            won = g.state == 'cleared'
            campaign_done = won and g.mode == 'campaign' and g.tier == 4
            self.canvas.blit(self.sprites.get('applin' if won else 'cramorant', 98, 0), (591, 143))
            title = 'Home at last.' if campaign_done else 'Sanctuary reached.' if won else 'The flock found you.'
            self.text(title, (640, 268), 38, GREEN if won else GOLD, serif=True, center=True)
            self.text('Five stages. One brave little apple.' if campaign_done else 'A fresh maze awaits your next attempt.',
                      (640, 319), 17, MUTED, center=True)
            stats = [(f'{g.elapsed:.1f}s', 'TIME'), (g.steps, 'STEPS'), (g.escapes_used, 'ESCAPES'), (f'{g.score:,}', 'SCORE')]
            for i, (value, label) in enumerate(stats):
                x = 407+i*155
                self.text(value, (x, 382), 28, TEXT, center=True)
                self.text(label, (x, 419), 12, MUTED, bold=True, center=True)
            if campaign_done:
                total = sum(r[2] for r in self.campaign_results)
                self.text(f'Expedition score: {total:,}  /  {sum(r[1] for r in self.campaign_results)} steps',
                          (640, 468), 18, GOLD, center=True)
            else:
                self.text(f'{g.hits} close calls  /  {g.dew_collected} dew collected  /  {g.health} hearts left',
                          (640, 468), 17, MUTED, center=True)
            action = self.result_primary()
            label = {'next': 'Continue to next difficulty', 'retry': 'Try a fresh maze', 'menu': 'Return to the orchard'}[action]
            self.button(label, (373, 519, 534, 53), action, True)
            if action != 'menu':
                self.button('Return to menu', (373, 589, 534, 47), 'menu')
            self.text('Result saved to your local journal.', (640, 675), 14, MUTED, center=True)

    def draw(self):
        self.canvas.fill(BG)
        self.buttons = []
        if self.screen == 'menu':
            self.draw_menu()
        elif self.screen == 'play':
            self.draw_game()
        elif self.screen in ('paused', 'result'):
            self.draw_overlay()
        elif self.screen == 'help':
            self.draw_help()
        elif self.screen == 'settings':
            self.draw_settings()
        elif self.screen == 'records':
            self.draw_records()
        elif self.screen == 'error':
            self.header('The adventure needs a moment.', 'A local file or save operation could not be completed.')
            # Wrap long OS messages instead of clipping.
            for i in range(0, len(self.error), 95):
                self.text(self.error[i:i+95], (48, 200+(i//95)*32), 18, RED)
            self.button('Back to menu', (48, 650, 260, 50), 'menu', True)
        width, height = self.window.get_size()
        scale = min(width/W, height/H)
        dest = (max(1, int(W*scale)), max(1, int(H*scale)))
        self.window.fill((7, 14, 17))
        self.window.blit(pygame.transform.smoothscale(self.canvas, dest), ((width-dest[0])//2, (height-dest[1])//2))
        pygame.display.flip()

    def close(self):
        if self.game:
            self.game.abandon()
        self.store.close()
        pygame.quit()

    def run(self):
        try:
            while self.running:
                dt = min(self.clock.tick(60)/1000, .05)
                self.events()
                self.update(dt)
                self.draw()
        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save-dir', help='Optional separate local save directory')
    parser.add_argument('--preview', help='Render menu and all five tiers to this folder using a temporary save')
    args = parser.parse_args()
    if args.preview:
        folder = Path(args.preview)
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as directory:
            app = App(directory)
            pygame.image.save(app.canvas, str(folder/'menu.png'))
            for tier in range(5):
                app.start(tier)
                app.draw()
                pygame.image.save(app.canvas, str(folder/f'tier_{tier+1}.png'))
                app.game.abandon()
            app.screen = 'help'
            app.draw()
            pygame.image.save(app.canvas, str(folder/'help.png'))
            app.close()
    else:
        App(args.save_dir).run()


if __name__ == '__main__':
    main()
