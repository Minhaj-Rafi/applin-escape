"""Optional sanctuary gardening and resident care. Saved timers and no gameplay bonuses."""
import pygame
import time
from garden_timers import BERRIES,migrate_crops,crop_stage,crop_action
from art import berry,leaf,heart
from sanctuary import budew
from home_progress import home_progress

TEXT=(243,237,216); GREEN=(177,225,153); GOLD=(247,203,118); MUTED=(153,176,166)
DECOR48=(('Natural','Always available.'),('Lanterns','Restore one biome.'),('Flowers','Bring three Budew home.'),('Fountain','Restore all five biomes.'),('Picnic','Harvest once and earn 3 friendship hearts.'),('Blossom arch','Harvest five times and earn 5 friendship hearts.'),('Market stall','Deliver three different community projects.'),('Welcome gazebo','Deliver all six community projects.'),('Sanctuary monument','Complete all 24 advanced mastery goals.'))
NAMES=('Clover','Dewdrop','Pip','Fern','Moss','Sunny','Willow','Pebble','Sprout','Bramble')


def care_state(progress):
    return progress.setdefault('care',{'beds':[0,0,0],'berries':0,'harvests':0,'friends':{},'chatted':[]})


def resident_name(index):
    return NAMES[index%len(NAMES)]+(f' {index//len(NAMES)+1}' if index>=len(NAMES) else '')


def care_action(store,action,index=0,kind=0):
    progress=home_progress(store); care=care_state(progress)
    notice='Choose a garden bed or resident.'
    from rewards44 import record_interaction
    migrate_crops(care)
    before_crops=repr(care.get('crops'))
    if action=='harvest' and 0<=index<3 and crop_stage(care['crops'][index])==3:
        from home_mastery46 import record_harvest
        record_harvest(care,care['crops'])
    if action in ('plant','water','harvest'):
        notice=crop_action(care,action,index,kind)
    elif action in ('chat','feed') and 0<=index<progress['rescued']:
        key=str(index); value=care['friends'].get(key,0); name=resident_name(index)
        if action=='chat':
            if index not in care['chatted']:
                care['chatted'].append(index); care['friends'][key]=min(3,value+1)
            from residents48 import talk
            notice=f'{name}: '+talk(care,index)
        elif value>=3: notice=f'{name} is already settled in and happy. Save the berry for another friend.'
        elif care['berries']<=0: notice='Grow and harvest a garden berry first. Your maze berries are separate.'
        else:
            care['berries']-=1; care['friends'][key]=value+1
            care['feeds45']=care.get('feeds45',0)+1
            from residents48 import profile
            favourite=profile(index)[1]
            inventory=care.get('berry_types',{})
            for berry_name in sorted(inventory,key=lambda n:n!=favourite):
                count=inventory[berry_name]
                if count>0:
                    care['berry_types'][berry_name]-=1; break
            notice=f'{name} enjoyed the berry! Friendship {value+1}/3.'
    if (action in ('plant','water','harvest') and before_crops!=repr(care.get('crops'))) or (action=='chat' and 0<=index<progress['rescued']) or notice.endswith('/3.'):
        record_interaction(care)
    store.set('sanctuary_v4',progress)
    return notice


class HomeActivitiesUI:
    def activities_action(self,action):
        from journey47 import home_snapshot,home_feedback
        tracked=action.startswith('care:') or action=='project_deliver'
        before=home_snapshot(self.store) if tracked else None
        if action=='home_activities':
            if self.screen=='play': self.action('pause')
            self.navigation.append((self.screen,self.return_screen)); self.return_screen=self.screen
            self.screen='home_activities'; self.home_tab=0; self.resident_page=0
            self.care_notice='Grow a little garden, share berries and get to know your rescued Budew.'
        elif action.startswith('resident_profile:'):
            self.resident_selected48=int(action.split(':')[1]); self.home_tab=4
        elif action.startswith('resident_request:'):
            from residents48 import complete_request
            progress=home_progress(self.store)
            self.care_notice=complete_request(progress,self.resident_selected48,int(action.split(':')[1]))
            self.store.set('sanctuary_v4',progress)
        elif action=='decor_preview':
            self.action('home_activities'); self.home_tab=5; self.decor_preview48=0
        elif action=='decor_next': self.decor_preview48=(getattr(self,'decor_preview48',0)+1)%9
        elif action=='decor_apply':
            from home_progress import decorations
            name=DECOR48[getattr(self,'decor_preview48',0)][0]
            if name in decorations(home_progress(self.store)):
                self.home_decor=name; self.store.set('home_decor_v4',name); self.care_notice='Decoration applied: '+name
        elif action.startswith('home_tab:'):
            self.home_tab=int(action[-1]); self.resident_page=0
        elif action in ('milestone_next','milestone_previous'):
            self.milestone_page=(getattr(self,'milestone_page',0)+(1 if action=='milestone_next' else -1))%4
        elif action=='project_next': self.project_index=(getattr(self,'project_index',0)+1)%6
        elif action=='project_deliver':
            from home_mastery46 import deliver
            progress=home_progress(self.store); care_state(progress)
            self.care_notice=deliver(progress,getattr(self,'project_index',0))
            self.store.set('sanctuary_v4',progress)
        elif action=='resident_next':
            count=home_progress(self.store)['rescued']; pages=max(1,(count+2)//3)
            self.resident_page=(self.resident_page+1)%pages
        elif action.startswith('berry_kind:'):
            self.selected_berry=(self.selected_berry+1)%len(BERRIES)
        elif action.startswith('care:'):
            _,kind,index=action.split(':'); self.care_notice=care_action(self.store,kind,int(index),self.selected_berry)
            self.care_timer_bed=int(index) if self.care_notice.startswith('Still growing:') else None
        else: return False
        if tracked:
            feedback=home_feedback(before,home_snapshot(self.store))
            if feedback: self.care_notice+=' '+feedback
        return True

    def draw_home_activities(self):
        progress=home_progress(self.store); care=care_state(progress)
        self.header('Life in the sanctuary','An optional, peaceful place to grow things and spend time with the residents.')
        for i,title in enumerate(('Berry garden','Resident album','Home milestones','Projects')):
            self.button(title,(48+i*300,145,283,47),f'home_tab:{i}',i==(1 if self.home_tab==4 else self.home_tab))
        if self.home_tab==0: self.draw_care_garden(care)
        elif self.home_tab==1: self.draw_resident_album(progress,care)
        elif self.home_tab==2: self.draw_home_milestones(progress,care)
        elif self.home_tab==3: self.draw_projects(progress,care)
        elif self.home_tab==4: self.draw_resident_profile48(progress,care)
        else: self.draw_decor_preview48(progress)
        self.flow_text(self.live_care_notice(care),52,699,1170,17,GREEN)
        self.button('Back to sanctuary',(48,781,246,40),'back',True)
        self.text('Crops grow while you are away and never spoil. Shiny odds stay unchanged.',(326,790),14,MUTED)

    def live_care_notice(self,care,now=None):
        index=getattr(self,'care_timer_bed',None)
        if index is None or not self.care_notice.startswith('Still growing:'): return self.care_notice
        crop=migrate_crops(care)[index]
        if crop is None: return 'This bed is empty. Plant a new berry when you like.'
        seconds=max(0,int(crop['ready_at']-(time.time() if now is None else now)+.999))
        return 'Ready to harvest. Ripe berries will wait for you.' if not seconds else f'Still growing: {seconds//60}:{seconds%60:02d} remaining. Ripe berries will wait for you.'

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
            from residents48 import profile
            personality,favourite,_=profile(index)
            self.text(personality+' / '+favourite,(x+191,330),15,GOLD,center=True)
            budew(self.canvas,(x+191,400),76)
            points=care['friends'].get(str(index),0)
            for j in range(3): heart(self.canvas,x+160+j*31,463,j<points)
            self.text(('New arrival','Getting comfortable','Growing close','Settled and happy')[points],(x+191,495),17,GREEN,center=True)
            self.button('Talk',(x+27,540,329,43),f'care:chat:{index}')
            self.button('Meet & requests',(x+27,594,329,43),f'resident_profile:{index}',True,small=True)
        self.button('Next residents',(970,211,262,37),'resident_next',small=True)

    def draw_home_milestones(self,progress,care):
        from home_mastery46 import home_milestones
        goals=home_milestones(progress); page=getattr(self,'milestone_page',0)
        self.text(f'{sum(g[1] for g in goals)} / {len(goals)} home milestones',(52,209),19,GOLD)
        for i,(title,done,detail) in enumerate(goals[page*4:page*4+4]):
            y=244+i*86; self.panel((48,y,1184,76))
            self.text('DONE' if done else 'GOAL',(70,y+27),15,GREEN if done else MUTED)
            self.text(title,(144,y+9),23,TEXT)
            self.flow_text(detail,144,y+43,1050,16,GREEN if done else MUTED)
        self.text(f'Page {page+1}/4',(52,636),18,GOLD)
        self.button('Previous',(844,628,180,42),'milestone_previous',small=True)
        self.button('Next',(1050,628,180,42),'milestone_next',small=True)

    def draw_projects(self,progress,care):
        from home_mastery46 import PROJECTS,happy
        index=getattr(self,'project_index',0); name,recipe,rescues,friends=PROJECTS[index]
        self.panel((48,214,1184,464))
        self.text(f'PROJECT {index+1}/6 / '+name,(76,239),27,GOLD)
        self.text('No deadline. Deliveries spend only the berries listed below.',(76,281),17,MUTED)
        for i,(kind,needed) in enumerate(recipe.items()):
            y=327+i*44; owned=care.get('berry_types',{}).get(kind,0)
            self.text(f'{kind}: {owned} / {needed}',(91,y),23,GREEN if owned>=needed else TEXT)
        for label,current,required,y in (('Rescued residents',progress['rescued'],rescues,332),('Happy residents',happy(care),friends,377)):
            status=f'{current} / {required} required' if required else 'not required'
            self.text(f'{label}: {status}',(695,y),18,GREEN if current>=required else TEXT)
        count=care.get('projects46',{}).get(str(index),0)
        self.text(f'Deliveries completed: {count}',(695,422),21,GOLD)
        self.flow_text('Plan berry varieties across your three beds. Complete different projects to unlock home decorations.',695,471,475,17,MUTED)
        ready=progress['rescued']>=rescues and happy(care)>=friends and all(care.get('berry_types',{}).get(k,0)>=v for k,v in recipe.items())
        if ready: self.button('Deliver berries',(76,596,540,51),'project_deliver',True)
        else: self.text('Gather the listed berries and resident support.',(76,611),18,MUTED)
        self.button('Next project',(872,596,325,51),'project_next')

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

        elif self.home_decor in ('Market stall','Welcome gazebo','Sanctuary monument'):
            x,y=515,410
            if self.home_decor=='Market stall':
                d.rect(self.canvas,(133,92,65),(x-50,y-12,100,42))
                d.rect(self.canvas,(233,194,125),(x-60,y-66,120,24),border_radius=5)
                for xx in (x-48,x+48): d.line(self.canvas,(126,91,67),(xx,y-50),(xx,y+32),5)
                for i,color in enumerate((BERRIES[0][2],BERRIES[1][2],BERRIES[2][2])): self.draw_variety_berry((x-29+i*29,y-15),10,color)
            elif self.home_decor=='Welcome gazebo':
                d.ellipse(self.canvas,(176,159,119),(x-68,y+14,136,26))
                for xx in (x-48,x+48): d.line(self.canvas,(223,208,160),(xx,y-51),(xx,y+24),7)
                d.polygon(self.canvas,(103,145,118),[(x-72,y-49),(x,y-94),(x+72,y-49)])
                d.line(self.canvas,GOLD,(x-72,y-49),(x+72,y-49),4)
            else:
                d.rect(self.canvas,(151,162,151),(x-42,y-2,84,32),border_radius=4)
                d.rect(self.canvas,(192,199,173),(x-27,y-60,54,61),border_radius=5)
                for dx,dy in ((0,-78),(-13,-64),(13,-64)): leaf(self.canvas,(x+dx,y+dy),18,GOLD,dx*.1)

    def draw_resident_profile48(self,progress,care):
        from residents48 import profile,requests
        index=getattr(self,'resident_selected48',0)
        if not 0<=index<progress['rescued']:
            self.text('Rescue a Budew to meet your first resident.',(65,280),24,TEXT); return
        personality,favourite,_=profile(index); rows=requests(care,index)
        self.panel((48,215,356,464)); self.text(resident_name(index),(226,242),27,GOLD,center=True)
        self.text(personality+' / likes '+favourite,(226,283),17,TEXT,center=True)
        budew(self.canvas,(226,365),98)
        for j in range(3): heart(self.canvas,195+j*31,438,j<care['friends'].get(str(index),0))
        if all(r[3] for r in rows): self.text('HOME RIBBON EARNED',(226,478),16,GOLD,center=True)
        self.button('Talk',(74,528,304,43),f'care:chat:{index}')
        self.button('Share one berry',(74,585,304,43),f'care:feed:{index}',small=True)
        for number,(title,detail,ready,done) in enumerate(rows):
            y=215+number*154; self.panel((424,y,808,140))
            self.text(f'{number+1}. '+title+(' / Complete' if done else ''),(445,y+12),23,GREEN if done else GOLD)
            self.flow_text(detail,445,y+48,754,17,TEXT)
            if not done and ready and (number==0 or rows[number-1][3]):
                self.button('Complete request',(926,y+90,285,37),f'resident_request:{number}',small=True)
            elif not done: self.text('Continue caring for this resident.' if number==0 or rows[number-1][3] else 'Complete the previous request first.',(445,y+99),15,MUTED)

    def draw_decor_preview48(self,progress):
        from home_progress import decorations
        name,requirement=DECOR48[getattr(self,'decor_preview48',0)]
        unlocked=name in decorations(progress)
        self.panel((48,214,1184,464)); self.text('DECOR PREVIEW / '+name,(76,237),28,GOLD)
        self.flow_text(requirement,76,288,1090,19,TEXT)
        # Reuse the actual drawing for the complex decorations, isolated from the live garden.
        target=pygame.Surface((1280,840),pygame.SRCALPHA); old_canvas=self.canvas; old_decor=self.home_decor
        try:
            self.canvas=target; self.home_decor=name; self.draw_care_decor()
        finally: self.canvas=old_canvas; self.home_decor=old_decor
        if name in ('Picnic','Blossom arch','Market stall','Welcome gazebo','Sanctuary monument'):
            area=(385,550,150,160) if name=='Blossom arch' else (375,275,280,220)
            art=target.subsurface(area); art=pygame.transform.smoothscale(art,(int(art.get_width()*1.25),int(art.get_height()*1.25)))
            self.canvas.blit(art,art.get_rect(center=(380,472)))
        else:
            d=pygame.draw
            if name=='Natural':
                from story_art import tree
                tree(self.canvas,380,446,1.8,(80,140,79),True)
            elif name=='Flowers':
                for x in (335,380,425):
                    for dx,dy in ((-10,0),(10,0),(0,-10),(0,10)): d.circle(self.canvas,(234,157,190),(x+dx,455+dy),10)
                    d.circle(self.canvas,GOLD,(x,455),6)
            elif name=='Lanterns':
                for x in (345,410):
                    d.line(self.canvas,(112,83,60),(x,520),(x,415),8);d.rect(self.canvas,(246,207,112),(x-16,416,32,43),border_radius=5)
            else:
                d.ellipse(self.canvas,(151,166,168),(312,468,136,45));d.ellipse(self.canvas,(91,174,193),(324,475,112,26))
                d.rect(self.canvas,(196,208,199),(372,425,16,55));d.arc(self.canvas,(206,243,247),(351,398,57,49),0,3.142,5)
        self.text('Available now' if unlocked else 'Not unlocked yet',(754,422),25,GREEN if unlocked else MUTED)
        self.flow_text('Previewing never changes your current garden. Apply when you are ready.',754,473,423,19,MUTED)
        self.button('Next decoration',(76,607,339,44),'decor_next')
        if unlocked: self.button('Apply decoration',(847,607,351,44),'decor_apply',True)
