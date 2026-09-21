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

from model import Store, TIERS, DIRS, ROSTERS
from expedition import Session
from adventure_ui import ExpeditionUI
from controls import ControlUI
from biome_ui import BiomeUI
from sanctuary import SanctuaryUI
from polish_ui import PolishUI
from home_activities import HomeActivitiesUI
from chronicle_ui import ChronicleUI
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


class App(ChronicleUI, HomeActivitiesUI, PolishUI, SanctuaryUI, ControlUI, BiomeUI, ExpeditionUI):
    def __init__(self, save_dir=None):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        info = pygame.display.Info()
        self.window_size = (min(1280, info.current_w), min(840, max(525, info.current_h - 70)))
        self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption('Applin Escape | Homeward 5.0')
        self.canvas = pygame.Surface((W, H))
        self.store = Store(save_dir)
        self.init_adventure()
        self.init_controls()
        self.init_sanctuary()
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
        self.init_polish()
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

    def start(self, tier=0, mode='practice', shiny_state=None):
        try:
            if self.resume_data:
                data, self.resume_data = self.resume_data, None
                self.game = Session.restore(self.store, data['game'])
                self.campaign_results = data.get('campaign', [])
                self.story_mode = data.get('story',False)
            else:
                contract=self.pending_contract or (getattr(self.game,'contract',None) if mode=='contract' and self.game else None)
                self.pending_contract=None
                if self.game and self.game.state == 'playing': self.game.abandon()
                self.game = Session(self.store, tier, mode, skill=self.skill, ability=self.ability,
                                    coop=self.coop and mode != 'tutorial', code=self.pending_code, shiny_state=shiny_state,contract=contract)
                self.pending_code = None
                if mode!='campaign': self.story_mode=False
                self.game.story_run=self.story_mode
                if any(self.game.shiny):
                    who='Both players are' if all(self.game.shiny) else 'Player 2 is' if self.game.shiny[1] else 'Applin is'
                    self.game.notify(who+' shiny! This rare green colour lasts for this run.')
            self.store.set('last_shared_code43',self.game.code)
            self.navigation.clear()
            self.pings={}
            self.render_revision = self.game.board_revision
            self.visual_partner = list(map(float, self.game.partner['pos']))
            self.partner_timer = .2
            self.autosave_timer = 0
            self.celebrate = 0
            self.save_expedition()
            self.shrine_open = 0.0
            self.overview = True
            self.prepare_board()
            self.audio.set_biome(self.game.tier)
            self.visual_player = list(map(float, self.game.player))
            self.visual_enemies = [list(map(float, e.pos)) for e in self.game.enemies]
            self.particles = []
            self.move_timer = .2
            self.screen = 'play' if self.game.state == 'playing' else 'result'
            self.focus = -1
            self.error = ''
            self.cached_summary = self.store.summary()
        except (OSError, RuntimeError, sqlite3.Error, ValueError, KeyError, TypeError) as exc:
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
        if self.chronicle_action(action): return
        if self.activities_action(action): return
        if self.polish_action(action): return
        if self.sanctuary_action(action): return
        if self.controls_action(action): return
        if self.extra_action(action): return
        if action.startswith('tier:'):
            self.selected = int(action.split(':')[1])
        elif action == 'campaign':
            self.story_mode=False
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
            self.save_expedition()
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
            self.skill, self.ability, self.coop = self.game.skill, self.game.ability, self.game.coop
            self.start(self.game.tier+1, 'campaign', shiny_state=self.game.shiny[:])
        elif action == 'retry':
            self.skill, self.ability, self.coop = self.game.skill, self.game.ability, self.game.coop
            if self.game.mode == 'challenge': self.pending_code = self.game.code
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
        from event_safety import read_events
        for event in read_events(self):
            if self.chronicle_event(event): continue
            if self.control_event(event): continue
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.WINDOWFOCUSLOST and self.screen == 'play':
                self.action('pause')
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, action in self.buttons:
                    if rect.collidepoint(self.mouse()):
                        self.action(action)
                        break
            elif event.type == pygame.KEYDOWN:
                if self.screen == 'challenge':
                    self.challenge_key(event)
                    continue
                if event.key in (pygame.K_F3,pygame.K_F4) and self.screen=='play' and self.game.coop and event.key not in [key for row in self.controls.keys for key in row]:
                    self.action('ping:'+str(int(event.key==pygame.K_F4)))
                elif event.key == pygame.K_F11:
                    self.action('fullscreen')
                elif event.key == pygame.K_m:
                    self.action('music')
                elif event.key == pygame.K_TAB and self.screen != 'play':
                    self.focus = (self.focus+1) % max(1, len(self.buttons))
                elif event.key == pygame.K_RETURN:
                    if self.screen != 'play' and 0 <= self.focus < len(self.buttons):
                        self.action(self.buttons[self.focus][1])
                    elif self.screen == 'menu': self.action('story')
                    elif self.screen == 'paused': self.action('resume')
                    elif self.screen == 'result': self.action(self.result_primary())
                elif event.key == pygame.K_ESCAPE:
                    if self.screen == 'play': self.action('pause')
                    elif self.screen == 'paused': self.action('resume')
                    elif self.screen in ('help','settings','records','adventure','journal','controls','sanctuary','story','biome_guide','accessibility','object_info','ending','home_activities','home_hub','challenge_hall','profile','contract_collection','garden_collection','reward_room','completion_film','run_insights','support','team_journal'):
                        self.action('back')
                elif self.screen == 'menu' and pygame.K_1 <= event.key <= pygame.K_5:
                    self.selected = event.key-pygame.K_1
                elif self.screen == 'sanctuary':
                    command=self.controls.key_command(event.key,False)
                    if command and command[1]==5: self.home_interact()
                elif self.screen == 'play':
                    command=self.controls.key_command(event.key,self.game.coop)
                    if command:
                        player,index=command
                        if index<4:
                            timer=self.partner_timer if player else self.move_timer
                            if not player: self.held_direction=DIRS[index]
                            if timer<=0:
                                (self.game.move_partner if player else self.game.move)(DIRS[index])
                                if player: self.partner_timer=Session.PLAYER_DELAY
                                else: self.move_timer=Session.PLAYER_DELAY
                        elif index==4:
                            (self.game.escape_partner if player else self.game.escape)()
                        else:
                            self.game.interact(partner=bool(player))
                        self.consume_events()
                    elif event.key == pygame.K_p: self.action('pause')
                    elif event.key == pygame.K_v: self.action('overview')
                    elif event.key == pygame.K_t: self.action('trail')
                    elif event.key == pygame.K_F1:
                        self.action('pause'); self.action('help')

    def consume_events(self):
        g = self.game
        for kind, cell in g.events:
            self.audio.play(kind)
            if kind in ('seed', 'berry', 'escape', 'land', 'hit', 'cleared'):
                color = GOLD if kind == 'seed' else RED if kind == 'hit' else GREEN
                if kind == 'seed': self.celebrate = .7
                x, y = self.center(cell)
                for _ in range(20 if self.particle_fx and self.characters and not self.comfort else 0):
                    angle = self.fx_rng.uniform(0, math.tau)
                    speed = self.fx_rng.uniform(20, 105)
                    self.particles.append([x, y, math.cos(angle)*speed, math.sin(angle)*speed, .7, color])
            if kind in ('land', 'respawn'):
                self.visual_player = list(map(float, g.player))
                self.visual_partner = list(map(float, g.partner['pos']))
            if kind == 'respawn':
                self.visual_enemies = [list(map(float, e.pos)) for e in g.enemies]
            if kind in ('cleared', 'caught'):
                self.screen = 'result'
                self.focus = -1
                self.cached_summary = self.store.summary()
                if kind == 'cleared' and g.mode == 'campaign':
                    self.campaign_results.append((g.elapsed, g.steps, g.score))
                    self.save_expedition()
        g.events.clear()

    def update(self, dt):
        self.t += dt
        if self.screen != 'play':
            if self.screen=='sanctuary': self.update_sanctuary(dt)
            self.audio.set_danger(False)
            return
        g = self.game
        self.move_timer -= dt
        keys = pygame.key.get_pressed()
        held = self.controls.held(keys,0,g.coop)
        if held and self.move_timer <= 0:
            direction = self.held_direction if self.held_direction in held else held[0]
            self.held_direction = direction
            # Buffered turns: while the requested turn is blocked, continue forward if held.
            moved = g.move(direction)
            if not moved and g.direction in held and g.direction != direction:
                g.move(g.direction)
            self.move_timer = Session.PLAYER_DELAY
        self.partner_timer -= dt
        if g.coop and self.partner_timer <= 0:
            held_partner=self.controls.held(keys,1,True)
            if held_partner:
                g.move_partner(held_partner[0])
                self.partner_timer=Session.PLAYER_DELAY
        g.update(dt)
        self.extra_update(dt)
        self.consume_events()
        self.shrine_open = min(1.0,self.shrine_open+dt/1.1) if not g.seeds else 0.0
        factor = 1 if self.comfort or not self.characters else min(1,dt*24)
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
        self.button('Story expedition', (48,340,361,55), 'story',True)
        self.button('Play selected tier', (425, 340, 233, 55), 'practice')
        self.button('Adventure setup', (48,410,211,42), 'adventure', small=True)
        self.button('Tutorial', (272,410,155,42), 'tutorial', small=True)
        if self.store.get('active_expedition',None):
            self.button('Continue saved', (440,410,218,42), 'continue', True, small=True)
        else:
            self.button('Collection journal', (440,410,218,42), 'journal', small=True)
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
        self.text(f'CHOOSE YOUR CHALLENGE / {self.skill.upper()} / {self.ability.upper()} / '+('DUO' if self.coop else 'SOLO'), (48,470),13,MUTED,bold=True)
        for i, tier in enumerate(TIERS):
            x = 48+i*240
            rect = pygame.Rect(x, 503, 224, 211)
            self.panel(rect, (36, 54, 46) if i == self.selected else PANEL, 14)
            if i == self.selected:
                pygame.draw.rect(self.canvas, tier.color, rect, 2, border_radius=14)
            self.text(f'0{i+1}', (x+17, 518), 25, tier.color, serif=True)
            self.text(tier.name, (x+17, 557), 17, TEXT, bold=True)
            self.text(tier.biome, (x+17, 588), 12, MUTED)
            self.text(f'{tier.enemies} birds  /  {tier.escapes+(2 if self.skill=="Relaxed" else 0)} escapes', (x+17, 615), 14, MUTED)
            self.button('Selected' if i == self.selected else 'Select tier', (x+16, 652, 192, 43), f'tier:{i}', small=True)
        if getattr(self,'input_notice',''): self.text(self.input_notice,(48,728),12,GOLD)
        count, wins, best = self.cached_summary
        self.text(f'{count} maps / {wins} clears / best {best:,}', (48, 754), 16, MUTED)
        self.text('v5.0 / Separate maze mastery and sanctuary collections', (48, 796), 12, MUTED)
        self.button('Maze challenges',(610,758,235,46),'challenge_hall',small=True)
        self.button('Home sanctuary',(862,758,235,46),'sanctuary',small=True)
        self.button('Quit', (1114,758,118,46),'quit',small=True)

    def draw_game(self):
        g = self.game
        tier = g.config
        self.text('APPLIN ESCAPE', (30, 23), 13, GREEN, bold=True)
        self.text(tier.biome, (28, 47), 33, TEXT, serif=True)
        self.text(f'{g.mode.upper()} / STAGE {g.tier+1:02d} / {g.skill.upper()} / '+('DUO' if g.coop else 'SOLO'), (31, 101), 13, tier.color, bold=True)
        self.button('Pause  [P]', (1090,  30, 159, 43), 'pause', small=True)
        if not g.coop: self.text('Click landmarks to inspect', (827,42),14,MUTED)
        self.panel((20, 139, 900, 636), (19, 33, 33), 16)
        self.camera()
        self.canvas.set_clip((30,150,880,610))
        self.world.draw(self.canvas,(self.ox,self.oy),self.cell,self.t,self.motion)
        # Reduce scenery competition without changing the biome palette or collisions.
        scenery_shade = pygame.Surface((880,610),pygame.SRCALPHA)
        scenery_shade.fill((8,18,24, 40))
        self.canvas.blit(scenery_shade,(30,150))
        self.draw_biome_features()
        if self.trail:
            for pos in g.visited:
                trail_color={'Golden':(158,139,80),'Moonleaf':(98,145,169),'Blossom':(163,113,145)}.get(self.cosmetic,(78,108,79))
                pygame.draw.circle(self.canvas,trail_color,self.center(pos),2)
        for cell in g.dew:
            pygame.draw.circle(self.canvas, (246, 244, 190), self.center(cell), 2)
        for cell in g.seeds:
            seed(self.canvas, self.center(cell), max(8, self.cell//4), self.t if self.characters and not self.comfort else 0)
        for cell in g.berries:
            berry(self.canvas, self.center(cell), max(8, self.cell//4), self.t if self.characters and not self.comfort else 0)
        self.draw_world_extras()
        self.draw_team_beacons50()
        frame = int(g.elapsed*10) % 8 if self.characters and not self.comfort else 0
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
            sprite=self.bird_sprite(e,size,flight_frame)
            if self.characters and not self.comfort and e.mood=='swoop':
                sprite=pygame.transform.smoothscale(pygame.transform.rotate(sprite,-14*(e.direction[0] or 1)),(size,size))
            height=0 if e.stunned>0 else max(2,self.cell//8)
            if self.characters and not self.comfort and e.mood=='search': height+=int(math.sin(g.elapsed*3)*2)
            self.canvas.blit(sprite,(x-size//2,y-size//2-height))
            if e.stunned > 0:
                pygame.draw.circle(self.canvas, GOLD, (x, y-self.cell//2), 3)
            elif e.mood == 'chase':
                pygame.draw.circle(self.canvas, RED, (x, y-self.cell//2), 2)
        x, y = self.center(self.visual_player)
        if g.coop and g.partner['pos']==g.player: x-=self.cell//4
        if g.invulnerable > 0:
            pygame.draw.circle(self.canvas, GREEN, (x, y), self.cell//2, 2)
        hero=self.hero_sprite(size,frame,g.direction)
        if g.camouflage > 0:
            hero=hero.copy(); hero.set_alpha(125)
        lift=int(math.sin(self.celebrate/.7*math.pi)*3) if self.celebrate>0 and self.characters and not self.comfort else 0
        self.canvas.blit(hero, (x-size//2,y-size//2-lift))
        if g.shiny[0]: self.draw_shiny_mark(x,y,self.cell)
        if g.coop:
            self.text('1',(x,y-self.cell*.7),11,TEXT,center=True)
            px,py=self.center(self.visual_partner)
            if g.partner['pos']==g.player:
                px+=self.cell//4
                py+=self.cell//8
            hero2=self.hero_sprite(size,frame,g.partner['direction'],True)
            if g.partner['down'] or g.partner['camouflage']>0:
                hero2=hero2.copy(); hero2.set_alpha(115)
            self.canvas.blit(hero2,(px-size//2,py-size//2))
            if g.shiny[1]: self.draw_shiny_mark(px,py,self.cell)
            self.text('HELP' if g.partner['down'] else '2',(px,py-self.cell*.7),11,GOLD if g.partner['down'] else TEXT,center=True)
        for x, y, vx, vy, life, color in self.particles:
            leaf(self.canvas, (int(x), int(y)), max(1, life*6), color, self.t*3)
        self.draw_exit_marker()
        self.draw_polish_world()
        self.canvas.set_clip(None)
        self.panel((940, 139, 310, 636), radius=16)
        shiny_label='SHINY: P1 + P2' if all(g.shiny) else 'SHINY: P2' if g.shiny[1] else 'SHINY APPLIN' if g.shiny[0] else 'KEEP APPLIN SAFE'
        self.text(shiny_label,(960,153),13,GOLD if any(g.shiny) else MUTED,bold=True)
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
        self.text(f'{g.ability.upper()} / {g.escapes}',(962,343),17,GREEN,bold=True)
        self.button(f'Escape [{self.controls.key_name(0,4)}]',(960,375,270,43),'escape',True)
        status = 'Camouflaged' if g.camouflage > 0 else 'Shield active' if g.invulnerable > 0 else 'Birds slowed' if g.slow_time > 0 else 'Concealed in tall grass' if g.player in g.hidden_cells else 'Watch the trails'
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
        self.text(f'RESCUED {g.rescued}/2 / DEW {g.dew_collected}',(962,657),12,MUTED)
        seed(self.canvas,(972,692),8,0)
        self.text('Seed',(986,683),12,TEXT)
        berry(self.canvas,(1052,692),7)
        self.text('Berry',(1065,683),12,TEXT)
        pygame.draw.rect(self.canvas,(182,144,88),(1130,685,14,16),3)
        self.text('Exit',(1150,683),12,TEXT)
        self.text(f'{self.controls.key_name(0,5)}: interact / ledge',(962,711),12,MUTED)
        self.button('Comfort ON / map stays still' if self.comfort else 'V  Full map / quiet camera',
                    (960,737,270,27),'overview',small=True)
        self.draw_biome_badge()
        self.buttons.append((pygame.Rect(610,91,620,43),'biome_guide'))
        notice = g.notice if g.notice_time > 0 else self.interaction_hint()
        self.flow_text(notice,30,788,1210,16,GREEN if g.notice_time>0 else MUTED)
        self.draw_polish_hud()

    def predator_statuses(self):
        return [(enemy, 'STUNNED' if enemy.stunned>0 else 'DECOY' if self.game.decoy_time>0 else
                 'WARNING' if enemy.warning>0 else 'LURED' if enemy.mood=='lured' else 'RECOVER' if enemy.mood=='recover' else 'CHASING' if enemy.mood in ('chase','swoop') else 'SEARCH' if enemy.mood=='search' else 'PATROL') for enemy in self.game.enemies]

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
        if self.cosmetic!='Orchard':
            accent={'Golden':GOLD,'Moonleaf':(147,201,241),'Blossom':(243,171,207)}[self.cosmetic]
            for dx in (-r//2,r//2):
                leaf(self.canvas,(x+dx,y-r//2-3),3,accent,dx*.2)
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
            ('01', 'Gather the light', 'Collect every gold sun seed, then step onto the sanctuary gate.', 'Dew adds 10 points. Rescue each enclosed Budew for an optional 350 points.'),
            ('02', 'Read the flock', 'Pidgeotto, Spearow, Murkrow, Talonflame and Cramorant each have a role.', 'Gold route circles warn of a swoop. Grass hides you; blue berries slow birds.'),
            ('03', 'Make your escape', 'Choose Leaf Slip, Quick Dash, Decoy Apple or Camouflage in Adventure setup.', 'SPACE uses P1 ability; RIGHT SHIFT uses P2 ability. Co-op shares limited charges.'),
            ('04', 'Keep your footing', 'Each biome has a special interaction. Press your Interact key near its marker.', 'Fruit lures, tides, bells, turning gates and wind rides create different routes.'),
        ]
        for i, (number, title, a, b) in enumerate(items):
            y = 159+i*125
            self.panel((42, y, 1190, 108))
            self.text(number, (65, y+27), 34, GREEN, serif=True)
            self.text(title, (132, y+15), 22, TEXT, bold=True)
            self.text(a, (132, y+49), 17, MUTED)
            self.text(b, (132, y+77), 15, MUTED)
        self.text('Default keys: WASD / arrows move, SPACE escape, E interact. Remap them in Settings > Controls.', (48, 688), 17, TEXT)
        self.text('Gamepad: left stick / D-pad moves, A uses ability, X interacts, Start pauses. V toggles the optional camera.', (48, 723), 15, MUTED)
        self.button('Back',(48,766,170,44),'back',True)
        self.button('Illustrated biome guide',(905,766,327,44),'biome_guide',small=True)

    def draw_settings(self):
        self.backdrop()
        self.header('Make yourself at home.', 'Settings are saved automatically on this computer.')
        options = [
            ('Comfort Mode', 'Locks the full map and disables character animation', self.comfort, 'comfort'),
            ('Music', 'Five original biome themes; changes automatically with the stage', self.audio.music, 'music'),
            ('Sound effects', 'Collectibles, Leaf Slip, close calls and victory', self.audio.effects, 'effects'),
            ('Character animation', 'Wingbeats, item highlights, expressions and shrine doors', self.characters, 'characters'),
            ('Scenery animation', 'Disabled by Comfort Mode' if self.comfort else 'Optional bobbing, particles, ripples and movement smoothing', self.motion, 'motion'),
            ('Particles', 'Local collection bursts; independent from scenery and character animation', self.particle_fx, 'particles'),
            ('Adaptive music', 'A quiet rhythmic layer accompanies pursuit', self.adaptive_music, 'adaptive'),
            ('Footstep trail', 'Show the corridors you have visited', self.trail, 'trail'),
            ('Fullscreen', 'Also available with F11', self.fullscreen, 'fullscreen'),
        ]
        for i, (label, caption, value, action) in enumerate(options):
            y = 140+i*62
            self.panel((43, y, 1189, 56))
            self.text(label, (65, y+5), 20, TEXT)
            self.text(caption, (65, y+31), 13, MUTED)
            self.button('ON' if value else 'OFF', (1074, y+7, 132, 42), action, value)
        self.button('Sound / readable text',(275,764,294,44),'accessibility',small=True)
        self.button('Troubleshooting',(590,764,330,44),'support',small=True)
        self.button('Controls / gamepads',(947,764,285,44),'controls',small=True)
        self.text('Audio ready' if self.audio.available else 'Audio unavailable on this device; the game remains playable.', (49, 704), 16, MUTED)
        self.button('Back', (48, 766, 170, 44), 'back', True)

    def draw_records(self):
        self.draw_long_records()

    def result_primary(self):
        if self.game.state == 'cleared' and self.game.mode == 'campaign':
            return 'next' if self.game.tier < 4 else 'sanctuary' if self.story_mode else 'menu'
        return 'retry'

    def draw_overlay(self):
        self.draw_game()
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((7, 16, 19, 220))
        self.canvas.blit(shade, (0, 0))
        self.buttons = []
        self.panel((300, 127, 680, 596), (26, 42, 40), 25)
        if self.screen == 'paused':
            self.canvas.blit(self.hero_sprite(112,0,self.game.direction),(584,148))
            self.text('A moment in the shade.', (640, 287), 37, TEXT, serif=True, center=True)
            self.text('Applin is safe. The timer and flock are paused.', (640, 338), 17, MUTED, center=True)
            self.button('Resume adventure', (373, 391, 534, 52), 'resume', True)
            self.button('Settings', (373, 458, 257, 47), 'settings')
            self.button('How to play', (650, 458, 257, 47), 'help')
            self.button('Save & return to menu', (373, 522, 534, 47), 'save_menu')
            self.button('Share challenge', (373,581,257,43), 'copy_code',small=True)
            self.button('Abandon attempt', (650,581,257,43), 'end',small=True)
            self.button('Inspect nearest landmark',(373,633,534,27),'inspect_nearest',small=True)
            self.text('Progress also saves every 3 seconds and when you close.', (640,665),15,MUTED,center=True)
        else:
            g = self.game
            won = g.state == 'cleared'
            campaign_done = won and g.mode == 'campaign' and g.tier == 4
            self.canvas.blit(self.hero_sprite(98,0,g.direction) if won else self.sprites.get('cramorant',98,0),(591,143))
            title = 'Home at last.' if campaign_done else 'Sanctuary reached.' if won else 'The flock found you.'
            self.text(title, (640, 268), 38, GREEN if won else GOLD, serif=True, center=True)
            self.text(f'Seeds {g.config.seeds-len(g.seeds)}/{g.config.seeds} / Budew {g.rescued}/2 / Berries {getattr(g,"berries_collected",0)}',
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
            label = {'next': 'Continue to next difficulty', 'retry': 'Replay challenge' if g.mode=='challenge' else 'Try a fresh maze', 'menu': 'Return to the orchard', 'sanctuary':'Visit your restored home'}[action]
            self.button(label, (373, 519, 534, 53), action, True)
            if action != 'menu':
                self.button('Return to menu', (373, 589, 534, 47), 'menu')
            self.button('Share challenge',(373,650,257,40),'copy_code',small=True)
            self.button('Chapter ending' if won else 'Collection journal',(650,650,257,40),'ending' if won else 'journal',small=True)
            self.text(self.result_comparison(),(640,493),12,MUTED,center=True)

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
        elif self.screen == 'run_insights': self.draw_run_insights49()
        elif self.screen == 'team_journal': self.draw_team_journal50()
        elif self.screen == 'support': self.draw_support49()
        elif self.screen == 'home_hub': self.draw_home_hub()
        elif self.screen == 'garden_collection': self.draw_garden_collection()
        elif self.screen == 'reward_room': self.draw_reward_room()
        elif self.screen == 'completion_film': self.draw_completion_film()
        elif self.screen == 'contract_collection': self.draw_contract_collection()
        elif self.screen == 'challenge_hall': self.draw_challenge_hall()
        elif self.screen == 'profile': self.draw_profile()
        elif self.screen == 'home_activities': self.draw_home_activities()
        elif self.screen == 'accessibility': self.draw_accessibility()
        elif self.screen == 'object_info': self.draw_object_info()
        elif self.screen == 'ending': self.draw_ending()
        elif self.screen == 'sanctuary':
            self.draw_sanctuary()
        elif self.screen == 'story':
            self.draw_story()
        elif self.screen == 'biome_guide':
            self.draw_biome_guide()
        elif self.screen == 'controls':
            self.draw_controls()
        elif self.screen == 'adventure':
            self.draw_adventure()
        elif self.screen == 'journal':
            self.draw_journal()
        elif self.screen == 'challenge':
            self.draw_challenge()
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
        if self.game: self.consume_events()
        self.save_expedition()
        self.controls.close()
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
    parser.add_argument('--verify-build', action='store_true', help='With --preview, verify bundled audio and controller imports')
    parser.add_argument('--preview', help='Render menu and all five tiers to this folder using a temporary save')
    args = parser.parse_args()
    if args.preview:
        folder = Path(args.preview)
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as directory:
            app = App(directory)
            if args.verify_build:
                if not app.audio.available or len(app.audio.danger_layers)!=5 or not app.controls.enabled:
                    raise RuntimeError('Bundled audio or controller support did not load.')
                required={'fruit','bell','turn','wind','warning','rescue'}
                if not required <= app.audio.sounds.keys():
                    raise RuntimeError('Bundled biome effects are missing.')
            pygame.image.save(app.canvas, str(folder/'menu.png'))
            for tier in range(5):
                app.start(tier)
                app.draw()
                pygame.image.save(app.canvas, str(folder/f'tier_{tier+1}.png'))
                app.game.abandon()
            for screen in ('help','settings','controls','adventure','journal','biome_guide','sanctuary','story','accessibility','home_activities','home_hub','challenge_hall','contract_collection','profile','records','garden_collection','reward_room'):
                app.screen=screen
                app.draw()
                pygame.image.save(app.canvas,str(folder/f'{screen}.png'))
            app.close()
    else:
        App(args.save_dir).run()


if __name__ == '__main__':
    main()
