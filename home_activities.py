"""Optional sanctuary gardening and resident care. Saved timers and no gameplay bonuses."""
import pygame
import time
from garden_timers import BERRIES,migrate_crops,crop_stage,crop_action
from art import berry,leaf,heart
from sanctuary import budew
from home_progress import home_progress

TEXT=(243,237,216); GREEN=(177,225,153); GOLD=(247,203,118); MUTED=(153,176,166)
NAMES=('Clover','Dewdrop','Pip','Fern','Moss','Sunny','Willow','Pebble','Sprout','Bramble')


def care_state(progress):
    return progress.setdefault('care',{'beds':[0,0,0],'berries':0,'harvests':0,'friends':{},'chatted':[]})


def resident_name(index):
    return NAMES[index%len(NAMES)]+(f' {index//len(NAMES)+1}' if index>=len(NAMES) else '')


def care_action(store,action,index=0,kind=0):
    progress=home_progress(store); care=care_state(progress)
    notice='Choose a garden bed or resident.'
    if action in ('plant','water','harvest'):
        notice=crop_action(care,action,index,kind)
    elif action in ('chat','feed') and 0<=index<progress['rescued']:
        key=str(index); value=care['friends'].get(key,0); name=resident_name(index)
        if action=='chat':
            if index not in care['chatted']:
                care['chatted'].append(index); care['friends'][key]=min(3,value+1)
            notice=f'{name}: '+('The garden feels like home now.' if value>=2 else ('I like watching the pond.','Those little berry plants smell lovely.','I can hear the wind beyond the trees.')[index%3])
        elif value>=3: notice=f'{name} is already settled in and happy. Save the berry for another friend.'
        elif care['berries']<=0: notice='Grow and harvest a garden berry first. Your maze berries are separate.'
        else:
            care['berries']-=1; care['friends'][key]=value+1
            for name,count in care.get('berry_types',{}).items():
                if count>0:
                    care['berry_types'][name]-=1; break
            notice=f'{name} enjoyed the berry! Friendship {value+1}/3.'
    store.set('sanctuary_v4',progress)
    return notice


class HomeActivitiesUI:
    def activities_action(self,action):
        if action=='home_activities':
            if self.screen=='play': self.action('pause')
            self.navigation.append((self.screen,self.return_screen)); self.return_screen=self.screen
            self.screen='home_activities'; self.home_tab=0; self.resident_page=0
            self.care_notice='Grow a little garden, share berries and get to know your rescued Budew.'
        elif action.startswith('home_tab:'):
            self.home_tab=int(action[-1]); self.resident_page=0
        elif action=='resident_next':
            count=home_progress(self.store)['rescued']; pages=max(1,(count+2)//3)
            self.resident_page=(self.resident_page+1)%pages
        elif action.startswith('berry_kind:'):
            self.selected_berry=(self.selected_berry+1)%len(BERRIES)
        elif action.startswith('care:'):
            _,kind,index=action.split(':'); self.care_notice=care_action(self.store,kind,int(index),self.selected_berry)
        else: return False
        return True

    def draw_home_activities(self):
        progress=home_progress(self.store); care=care_state(progress)
        self.header('Life in the sanctuary','An optional, peaceful place to grow things and spend time with the residents.')
        for i,title in enumerate(('Berry garden','Resident album','Home milestones')):
            self.button(title,(48+i*400,145,383,47),f'home_tab:{i}',i==self.home_tab)
        if self.home_tab==0: self.draw_care_garden(care)
        elif self.home_tab==1: self.draw_resident_album(progress,care)
        else: self.draw_home_milestones(progress,care)
        self.flow_text(self.care_notice,52,699,1170,17,GREEN)
        self.button('Back to sanctuary',(48,781,246,40),'back',True)
        self.text('Crops grow while you are away and never spoil. Shiny odds stay unchanged.',(326,790),14,MUTED)

    def draw_care_garden(self,care):
        d=pygame.draw
        self.text(f'Garden berries: {care["berries"]}   /   Harvests: {care["harvests"]}',(52,214),20,GOLD)
        crops=migrate_crops(care)
        self.text('  /  '.join(f'{name}: {care.get("berry_types",{}).get(name,0)}' for name,_,_ in BERRIES),(52,243),12,MUTED)
        self.button('Plant: '+BERRIES[self.selected_berry][0],(922,207,309,40),'berry_kind:next',small=True)
        for i,crop in enumerate(crops):
            stage=crop_stage(crop)
            x=48+i*400; self.panel((x,261,383,405),(30,49,41))
            self.text(f'BED {i+1}',(x+24,280),16,GREEN,bold=True)
            center=x+191
            d.ellipse(self.canvas,(20,35,30),(x+71,476,242,30))
            d.polygon(self.canvas,(174,110,72),[(x+68,423),(x+315,423),(x+289,496),(x+93,496)])
            d.ellipse(self.canvas,(92,66,48),(x+66,408,250,35))
            d.ellipse(self.canvas,(54,47,34),(x+81,414,220,24))
            if stage:
                d.line(self.canvas,(123,183,86),(center,426),(center,391-stage*24),7)
                for sign in (-1,1): leaf(self.canvas,(center+sign*24,401-stage*12),27,(156,206,104),sign*.8)
                if stage>=2:
                    for sign in (-1,1): leaf(self.canvas,(center+sign*34,385-stage*12),30,(179,224,120),sign)
                if stage==3:
                    for dx,dy in ((-32,362),(30,355),(0,330)): self.draw_variety_berry((center+dx,dy),20,BERRIES[crop['kind']][2])
            if crop:
                seconds=max(0,int(crop['ready_at']-time.time()+.999))
                label=BERRIES[crop['kind']][0]+(' / ripe' if stage==3 else f' / {seconds//60}:{seconds%60:02d}')
            else: label='Empty bed'
            self.text(label,(center,536),21,TEXT,center=True)
            action='plant' if stage==0 else 'harvest' if stage==3 else 'water'
            self.button('Check growth' if crop and crop['watered'] and stage<3 else action.title(),(x+35,587,313,48),f'care:{action}:{i}',True)

    def draw_variety_berry(self,pos,r,color):
        x,y=pos
        if color==BERRIES[1][2]:
            pygame.draw.polygon(self.canvas,color,[(x,y+r),(x-r,y),(x-r//2,y-r),(x,y-r//2),(x+r//2,y-r),(x+r,y)])
        elif color==BERRIES[2][2]:
            pygame.draw.circle(self.canvas,color,(x-r//2,y+r//3),r*2//3)
            pygame.draw.circle(self.canvas,color,(x+r//2,y+r//3),r*2//3)
            pygame.draw.lines(self.canvas,(111,149,77),False,[(x-r//2,y),(x,y-r),(x+r//2,y)],2)
        elif color==BERRIES[3][2]: pygame.draw.ellipse(self.canvas,color,(x-r,y-r,2*r,2*r+5))
        else: pygame.draw.circle(self.canvas,color,(x,y),r)
        pygame.draw.circle(self.canvas,tuple(min(255,c+35) for c in color),(x-r//3,y-r//3),max(2,r//4))
        leaf(self.canvas,(x,y-r),r*.5,(142,204,100),.5)

    def draw_resident_album(self,progress,care):
        count=progress['rescued']; pages=max(1,(count+2)//3)
        self.resident_page%=pages
        self.text(f'{count} Budew brought home / page {self.resident_page+1} of {pages}',(52,214),20,GOLD)
        if not count:
            self.panel((48,272,1184,374)); self.flow_text('Rescue a Budew in a maze, then reach the shrine safely. Your first resident will appear here.',101,368,1040,27)
            return
        for slot,index in enumerate(range(self.resident_page*3,min(count,self.resident_page*3+3))):
            x=48+slot*400; self.panel((x,263,383,391))
            self.text(resident_name(index),(x+191,294),25,TEXT,center=True)
            budew(self.canvas,(x+191,386),96)
            points=care['friends'].get(str(index),0)
            for j in range(3): heart(self.canvas,x+160+j*31,463,j<points)
            self.text(('New arrival','Getting comfortable','Growing close','Settled and happy')[points],(x+191,495),17,GREEN,center=True)
            self.button('Talk',(x+27,540,329,43),f'care:chat:{index}')
            self.button('Share a garden berry',(x+27,594,329,43),f'care:feed:{index}',True,small=True)
        self.button('Next residents',(970,211,262,37),'resident_next',small=True)

    def draw_home_milestones(self,progress,care):
        friends=sum(care['friends'].values())
        goals=(('First harvest',care['harvests']>=1,'Grow and harvest a bed of berries.'),
               ('A shared picnic',care['harvests']>=1 and friends>=3,'Harvest once and earn 3 friendship hearts. Unlocks Picnic decor.'),
               ('A garden in bloom',care['harvests']>=5 and friends>=5,'Harvest five times and earn 5 friendship hearts. Unlocks Blossom arch.'),
               ('Lights across the garden',len(progress['restored'])==5,'Restore all five biomes. Unlocks the existing Fountain.'))
        for i,(title,done,detail) in enumerate(goals):
            y=230+i*103; self.panel((48,y,1184,91))
            self.text('✓' if done else '○',(77,y+24),28,GREEN if done else MUTED)
            self.text(title,(129,y+12),23,TEXT)
            self.flow_text(detail,129,y+49,1058,16,GREEN if done else MUTED)
        self.text('Choose unlocked decorations back in the sanctuary.',(52,659),16,GOLD)

    def draw_care_decor(self):
        d=pygame.draw
        if self.home_decor=='Picnic':
            d.rect(self.canvas,(213,153,127),(488,369,78,45),border_radius=5)
            for x in range(493,563,12): d.line(self.canvas,(247,222,178),(x,373),(x,409),2)
            for y in range(378,410,10): d.line(self.canvas,(247,222,178),(492,y),(562,y),2)
            berry(self.canvas,(515,385),7); berry(self.canvas,(539,394),7)
        elif self.home_decor=='Blossom arch':
            d.arc(self.canvas,(162,122,90),(411,577,81,110),0,3.142,7)
            for i in range(7):
                import math
                angle=i*math.pi/6; x=451+int(math.cos(angle)*40); y=632-int(math.sin(angle)*55)
                d.circle(self.canvas,(237,171,194),(x,y),8); d.circle(self.canvas,(251,221,148),(x,y),3)
