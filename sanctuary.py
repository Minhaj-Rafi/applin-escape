"""A calm, walkable home garden and five original story chapters."""
import math
from typing import NamedTuple
import pygame
from art import applin, leaf, seed
from biome_art import landmark
from biome_ui import KINDS
from story_art import draw_scene, tree
from home_progress import home_progress, decorations
from model import TIERS

TEXT=(244,239,217)
MUTED=(167,190,175)
GOLD=(246,205,124)
GREEN=(178,225,159)
class Chapter(NamedTuple):
    title: str
    lines: tuple
    goal: str


CHAPTERS=(
    ('The scattered light',
     ('A night wind scattered the sanctuary\'s sun seeds across the orchard.',
      'Applin sets out to bring their warmth home. A few Budew are missing, too.',
      'A falling apple might keep the birds busy while you find the first seeds.'),
     'Bring the orchard light home. Every rescued Budew has a place in the garden.'),
    ('Across the returning tide',
     ('The orchard is waking, but the garden pond is still quiet.',
      'Beyond it, stepping stones vanish beneath the returning tide.',
      'Watch their colour and take a longer route when the water rises.'),
     'Recover the wetland seeds to restore the pond.'),
    ('A bell beneath the leaves',
     ('A soft chime carries through the ferns. The old shrine is waiting.',
      'Its bells can draw the flock away from narrow woodland paths.',
      'Follow the sound, find the lost Budew, and carry the next light home.'),
     'Restore the woodland alcove and its sheltering ferns.'),
    ('The turning stone',
     ('Autumn leaves gather between the pillars of Copperleaf Ruins.',
      'A violet wheel still moves the old shortcut gates.',
      'Read the amber warning before choosing which corridor to cross.'),
     'Bring warmth back to the weathered terrace.'),
    ('A home under the stars',
     ('Only the highland seeds remain. The way home is almost lit.',
      'Windsocks point across the trails while the flock circles overhead.',
      'Ride the wind, gather the last light, and return to the waiting garden.'),
     'Restore the star garden. The sanctuary is ready to welcome everyone home.'),
)
CHAPTERS=tuple(Chapter(*entry) for entry in CHAPTERS)
PLOTS=((160,310),(535,290),(739,399),(190,574),(672,593))
RESIDENTS=((365,445),(420,470),(475,447),(365,540),(440,555),(505,545),(320,620),(390,645),(465,636),(534,615))


def budew(surface,pos,size=25,phase=0):
    x,y=pos; r=size//2; d=pygame.draw
    d.ellipse(surface,(43,83,58),(x-r,y+r//2,2*r,8))
    d.ellipse(surface,(208,229,119),(x-r,y-r,2*r,2*r))
    leaf(surface,(x-r//2,y-r+1),r*.8,(105,180,92),-.7)
    leaf(surface,(x+r//2,y-r+1),r*.8,(132,205,101),.7)
    for dx in (-r//3,r//3): d.circle(surface,(41,65,43),(x+dx,y),max(1,size//15))
    d.arc(surface,(70,110,58),(x-3,y+1,6,5),math.pi,math.tau,1)


class SanctuaryUI:
    def init_sanctuary(self):
        self.story_mode=False
        self.story_chapter=0
        self.story_next=False
        self.story_page=0
        self.story_replay=False
        self.home_selected=None
        self.home_pos=[443.,657.]
        self.home_direction=(0,-1)
        self.home_notice='A quiet place to return to. Explore the garden and talk to your rescued Budew.'
        self.home_decor=self.store.get('home_decor_v4','Natural')
        home_progress(self.store)

    def sanctuary_action(self,action):
        if action in ('sanctuary','biome_guide'):
            if self.screen=='play': self.action('pause')
            self.navigation.append((self.screen,self.return_screen))
            self.return_screen=self.screen
            self.screen=action
            if action=='sanctuary': self.audio.set_biome(None)
        elif action=='story':
            self.navigation.append((self.screen,self.return_screen))
            self.return_screen=self.screen
            self.story_chapter=0
            self.story_next=False
            self.story_page=0
            self.story_replay=False
            self.screen='story'
        elif action in ('story_forward','story_previous'):
            self.story_page=max(0,min(2,self.story_page+(1 if action=='story_forward' else -1)))
        elif action.startswith('memory:'):
            i=self.garden_index(action)
            if i is None or i not in home_progress(self.store)['restored']: return True
            self.navigation.append((self.screen,self.return_screen))
            self.return_screen=self.screen
            self.story_chapter=i
            self.story_page=0
            self.story_replay=True
            self.screen='story'
        elif action=='story_begin':
            if self.story_replay: return True
            carry=self.game.shiny[:] if self.story_next and self.game else None
            self.story_mode=True
            if not self.story_next: self.campaign_results=[]
            self.start(self.story_chapter,'campaign',shiny_state=carry)
        elif action=='next' and self.story_mode and self.game and self.game.mode=='campaign':
            self.skill,self.ability,self.coop=self.game.skill,self.game.ability,self.game.coop
            if self.game.tier>=len(CHAPTERS)-1:
                self.action('sanctuary')
                return True
            self.story_chapter=self.game.tier+1
            self.story_page=0
            self.story_replay=False
            self.story_next=True
            self.navigation.append((self.screen,self.return_screen))
            self.return_screen=self.screen
            self.screen='story'
        elif action=='home_decor':
            choices=decorations(home_progress(self.store))
            idx=choices.index(self.home_decor) if self.home_decor in choices else 0
            self.home_decor=choices[(idx+1)%len(choices)]
            self.store.set('home_decor_v4',self.home_decor)
        elif action.startswith('home_plot:'):
            i=self.garden_index(action)
            if i is None: return True
            self.home_selected=i
            progress=home_progress(self.store)
            self.home_notice=TIERS[i].biome+(': restored. '+CHAPTERS[i].goal if i in progress['restored'] else ': clear this biome to restore its garden.')
        else: return False
        return True

    @staticmethod
    def garden_index(action):
        try: i=int(action.split(':',1)[1])
        except (ValueError,IndexError): return None
        return i if 0<=i<len(CHAPTERS) else None

    def home_interact(self):
        progress=home_progress(self.store); x,y=self.home_pos
        if math.hypot(x-390,y-334)<58:
            self.action('home_hub'); return
        residents=RESIDENTS[:min(progress['rescued'],len(RESIDENTS))]
        nearby=[p for p in residents if math.hypot(p[0]-x,p[1]-y)<55]
        if nearby:
            lines=('Budew: The garden feels warmer with every seed you bring home.',
                   'Budew: Thank you for finding us. There is room for everyone here.',
                   'Budew: I like the quiet pond. The birds cannot chase us here.')
            from home_activities import care_action
            self.home_notice=care_action(self.store,'chat',residents.index(nearby[0]))
        else:
            nearest=min(range(5),key=lambda i:math.hypot(PLOTS[i][0]-x,PLOTS[i][1]-y))
            if math.hypot(PLOTS[nearest][0]-x,PLOTS[nearest][1]-y)<150:
                self.sanctuary_action(f'home_plot:{nearest}')
            else: self.home_notice='Rescue Budew and reach a shrine to bring them home. Clear biomes to restore each garden.'

    def update_sanctuary(self,dt):
        keys=pygame.key.get_pressed()
        held=self.controls.held(keys,0,False)
        if held:
            dx,dy=held[0]; self.home_direction=(dx,dy)
            x=max(80,min(840,self.home_pos[0]+dx*155*dt))
            y=max(215,min(699,self.home_pos[1]+dy*155*dt))
            # The cottage and pond are solid; the camera never follows or scrolls.
            if not pygame.Rect(321,200,139,135).collidepoint(x,y) and not pygame.Rect(321,355,120,58).collidepoint(x,y):
                self.home_pos=[x,y]

    def draw_story(self):
        chapter=CHAPTERS[self.story_chapter]
        prefix='Memory' if self.story_replay else 'Chapter'
        self.header(f'{prefix} {self.story_chapter+1}: {chapter.title}', TIERS[self.story_chapter].biome+' / An original illustrated story')
        animated=self.characters and not self.comfort
        phase=self.t if animated else 0
        hero=None
        if self.story_next and not self.story_replay and self.game:
            hero=self.hero_sprite(90,int(phase*3)%4,(1,0))
        draw_scene(self.canvas,pygame.Rect(48,147,1184,350),self.story_chapter,self.story_page,hero,phase)
        self.panel((48,512,1184,211),(29,48,43),20)
        self.text(f'SCENE {self.story_page+1} / 3  ·  '+('The journey' if self.story_page==0 else 'A way through' if self.story_page==1 else 'The way home'),(72,534),14,GREEN,bold=True)
        y=self.flow_text(chapter.lines[self.story_page],72,575,1120,22,TEXT)
        self.flow_text(chapter.goal,72,max(620,y+8),1120,17,GOLD)
        if not self.large_text: self.text('Scenes wait for you. Use the buttons or Tab + Enter / controller navigation.',(72,675),14,MUTED)
        if self.story_replay:
            self.button('Return to garden',(894,748,338,52),'back',True)
        else:
            self.button('Begin chapter',(894,748,338,52),'story_begin',True)
        self.button('Back',(48,752,145,44),'back')
        if self.story_page>0: self.button('Previous scene',(214,752,208,44),'story_previous')
        if self.story_page<2: self.button('Next scene',(439,752,208,44),'story_forward')

    def draw_sanctuary(self):
        progress=home_progress(self.store); restored=progress['restored']; d=pygame.draw
        self.header('A little place called home.', 'Your victories restore this garden. Rescued Budew arrive when you reach a sanctuary.')
        self.button('Sanctuary square',(954,33,278,44),'home_hub',True,small=True)
        self.panel((42,147,842,588),(69,111,74),22)
        # Pebbles and grass details use fixed coordinates: no moving background.
        for i in range(135):
            x=66+(i*137)%793; y=202+(i*79)%491
            d.line(self.canvas,(87,132,81),(x,y),(x+2,y-4),1)
        # Layered paths, hedges and five distinct garden patches.
        for x in range(62,861,35):
            for y in (176,712):
                d.circle(self.canvas,(38,77,55),(x,y),18)
                d.circle(self.canvas,(83,143,83),(x-3,y-4),13)
        d.rect(self.canvas,(191,180,125),(431,196,43,511),border_radius=17)
        d.rect(self.canvas,(191,180,125),(104,435,686,37),border_radius=15)
        d.rect(self.canvas,(184,175,122),(149,303,42,265),border_radius=12)
        d.rect(self.canvas,(184,175,122),(635,310,40,285),border_radius=12)
        palette=((115,176,85),(85,160,157),(87,151,110),(184,141,79),(97,133,168))
        for i,((x,y),color) in enumerate(zip(PLOTS,palette)):
            active=i in restored
            d.ellipse(self.canvas,color if active else (88,113,79),(x-87,y-67,174,133))
            for j in range(9):
                px=x-60+(j%3)*60; py=y-42+(j//3)*39
                if active:
                    leaf(self.canvas,(px,py),8,(191,225,129),j)
                    d.circle(self.canvas,(255,221,141),(px,py),3)
                else:
                    d.line(self.canvas,(122,116,86),(px-4,py+5),(px,py-5),2)
            self.canvas.blit(landmark(KINDS[i],65),(x-32,y-43))
            self.text(('Restored' if active else 'Waiting')+f' / {i+1}',(x,y+54),13,TEXT,center=True)
            self.buttons.append((pygame.Rect(x-86,y-65,172,132),f'home_plot:{i}'))
        for x,y in ((87,255),(265,218),(832,282),(80,654),(820,649)):
            tree(self.canvas,x,y,.62,(60,125,71),0 in restored)
        # Cottage: an original little refuge, not an extracted game asset.
        d.rect(self.canvas,(215,190,137),(325,245,130,89),border_radius=5)
        d.polygon(self.canvas,(127,81,90),[(305,248),(390,193),(475,248)])
        d.line(self.canvas,(231,176,121),(310,248),(470,248),5)
        d.rect(self.canvas,(64,98,72),(374,289,31,45),border_radius=13)
        for x in (341,423):
            d.rect(self.canvas,(249,219,133),(x,265,18,21),border_radius=3)
            d.line(self.canvas,(145,109,81),(x+9,265),(x+9,286),2)
        for y in (217,228,239):
            d.line(self.canvas,(155,102,100),(390-(y-193)*1.45,y),(390+(y-193)*1.45,y),2)
        self.text('HOME',(390,238),12,TEXT,center=True,bold=True)
        # A pond opens with the wetland garden.
        d.ellipse(self.canvas,(49,94,111) if 1 in restored else (103,109,80),(322,356,116,56))
        if 1 in restored:
            for i in range(3): d.arc(self.canvas,(149,222,210),(337+i*9,365+i*5,76-i*13,26-i*4),.2,2.7,2)
        if self.home_decor=='Fountain' and len(restored)==5:
            d.ellipse(self.canvas,(212,214,191),(489,368,66,39))
            d.ellipse(self.canvas,(82,169,197),(495,372,54,28))
            d.line(self.canvas,(206,243,247),(522,383),(522,352),4)
            d.arc(self.canvas,(206,243,247),(505,347,35,31),0,math.pi,3)
        if self.home_decor in ('Lanterns','Flowers','Fountain'):
            for x,y in ((92,440),(804,440),(292,665),(588,665)):
                if self.home_decor=='Flowers':
                    for j in range(5):
                        d.circle(self.canvas,(234,157,190),(x+int(math.cos(j*math.tau/5)*7),y+int(math.sin(j*math.tau/5)*7)),5)
                    d.circle(self.canvas,GOLD,(x,y),4)
                else:
                    d.line(self.canvas,(112,83,60),(x,y+20),(x,y-9),4)
                    d.rect(self.canvas,(246,207,112),(x-6,y-10,12,16),border_radius=4)
        self.draw_care_decor()
        animated=self.characters and not self.comfort
        for i,pos in enumerate(RESIDENTS[:min(progress['rescued'],len(RESIDENTS))]):
            bob=int(math.sin(self.t*2+i)*1.5) if animated else 0
            budew(self.canvas,(pos[0],pos[1]+bob),26)
        frame=int(self.t*5)%8 if animated else 0
        self.canvas.blit(applin(49,frame,self.home_direction[0] or 1),(int(self.home_pos[0])-24,int(self.home_pos[1])-25))
        self.panel((903,147,332,588))
        self.text('THE GARDEN REMEMBERS',(923,171),14,GREEN,bold=True)
        self.text(f'{len(restored)} / 5 gardens restored',(923,205),20,TEXT)
        self.text(f'{progress["rescued"]} Budew brought home',(923,243),18,TEXT)
        self.text(f'{len(progress["chapters"])} / 5 story chapters',(923,281),18,TEXT)
        self.text('DECORATIONS',(923,317),13,GREEN,bold=True)
        self.button(self.home_decor,(922,345,294,43),'home_decor',small=True)
        self.button('Preview decorations',(922,402,294,39),'decor_preview',small=True)
        self.text('See rewards before applying them.',(923,449),13,MUTED)
        if self.home_selected is not None:
            i=self.home_selected
            if i in restored:
                self.button(f'Garden {i+1}: story memories',(922,483,294,43),f'memory:{i}',small=True)
            else:
                self.text(f'Garden {i+1} is waiting for its seeds.',(923,491),14,GOLD)
        else: self.text('Select a garden to inspect it.',(923,491),14,MUTED)
        self.text('Garden displays are decorative.',(923,466),12,MUTED)
        self.button('Story expedition',(922,543,294,48),'story',True)
        self.button('Adventure setup',(922,604,294,43),'adventure',small=True)
        if self.store.get('active_expedition',None):
            self.button('Continue saved run',(922,663,294,43),'continue',small=True)
        self.flow_text(self.home_notice,47,739,1175,14,TEXT,line_height=18)
        self.button('Back',(48,783,139,37),'back',small=True)
        self.text('Movement keys / left stick: walk     Interact: talk or inspect a garden',(218,794),14,MUTED)

    def draw_shiny_mark(self,x,y,cell):
        sx=x+cell*.42; sy=y-cell*.38
        pygame.draw.polygon(self.canvas,(254,249,180),[(sx,sy-5),(sx+1.5,sy-1.5),(sx+5,sy),(sx+1.5,sy+1.5),(sx,sy+5),(sx-1.5,sy+1.5),(sx-5,sy),(sx-1.5,sy-1.5)])
