"""Sanctuary navigation, challenge collection, paginated records and local profile sharing."""
import pygame
from pathlib import Path
from challenge_hall import GOALS,TOTAL,combinations
from model import TIERS
from expedition import SKILLS,ABILITIES
from home_progress import home_progress

TEXT=(243,237,216); GREEN=(177,225,153); GOLD=(247,203,118); MUTED=(153,176,166)


class ChronicleUI:
    def chronicle_action(self,action):
        if action in ('home_hub','challenge_hall','profile','records','contract_collection'):
            if self.screen=='play': self.action('pause')
            self.navigation.append((self.screen,self.return_screen)); self.return_screen=self.screen
            self.screen=action
            if action=='profile': self.name_input=self.store.get('player_alias43','Applin Trainer')
        elif action.startswith('hub_tab:'):
            self.action('home_activities'); self.home_tab=int(action[-1])
        elif action=='collection_next': self.collection_page=(self.collection_page+1)%(TOTAL//8)
        elif action=='collection_previous': self.collection_page=(self.collection_page-1)%(TOTAL//8)
        elif action.startswith('contract_pick:'):
            index=int(action.split(':')[1])
            self.selected,self.skill,self.ability,self.coop,goal=combinations()[index]
            self.contract_goal=GOALS.index(goal)
            self.action('back')
        elif action=='contract_goal': self.contract_goal=(self.contract_goal+1)%len(GOALS)
        elif action=='contract_tier': self.selected=(self.selected+1)%5
        elif action=='contract_start':
            self.pending_contract=GOALS[self.contract_goal]; self.start(self.selected,'contract')
        elif action in ('record_previous','record_next'):
            count=self.store.db.execute('SELECT COUNT(*) FROM runs').fetchone()[0]
            self.record_offset=max(0,min(max(0,((count-1)//8)*8),self.record_offset+(8 if action=='record_next' else -8)))
        elif action=='profile_save':
            self.store.set('player_alias43',self.name_input.strip() or 'Applin Trainer')
            self.profile_notice='Player name saved locally.'
        elif action=='profile_share': self.share_profile()
        else: return False
        return True

    def chronicle_event(self,event):
        if self.screen=='contract_collection' and event.type==pygame.MOUSEWHEEL:
            self.action('collection_previous' if event.y>0 else 'collection_next'); return True
        if self.screen=='records':
            if event.type==pygame.MOUSEWHEEL:
                self.action('record_previous' if event.y>0 else 'record_next'); return True
            if event.type==pygame.KEYDOWN and event.key in (pygame.K_PAGEUP,pygame.K_PAGEDOWN):
                self.action('record_previous' if event.key==pygame.K_PAGEUP else 'record_next'); return True
        if self.screen=='profile' and event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: self.action('back')
            elif event.key==pygame.K_TAB: return False
            elif event.key==pygame.K_RETURN:
                self.action(self.buttons[self.focus][1] if 0<=self.focus<len(self.buttons) else 'profile_save')
            elif event.key==pygame.K_BACKSPACE: self.name_input=self.name_input[:-1]
            else:
                self.focus=-1
                chars=getattr(event,'unicode','')
                self.name_input=(self.name_input+''.join(c for c in chars if c.isalnum() or c in ' _-'))[:20]
            return True
        return False

    def draw_home_hub(self):
        self.header('Sanctuary square','Choose a place to visit. Every garden and resident activity is grouped here.')
        choices=(('Berry nursery','Four varieties with saved growing timers.','hub_tab:0'),
                 ('Resident lodge','Talk, share berries and build friendship.','hub_tab:1'),
                 ('Milestone board','See home goals and decoration unlocks.','hub_tab:2'),
                 ('Challenge hall','Choose a mastery contract and track your collection.','challenge_hall'),
                 ('Player journal','Browse all your recorded attempts.','records'),
                 ('Player name & sharing','Create a local name and export a share card.','profile'))
        for i,(title,desc,action) in enumerate(choices):
            x=48+(i%2)*601; y=157+(i//2)*180
            self.panel((x,y,582,160)); self.text(f'{i+1:02d}',(x+25,y+19),24,GOLD)
            self.flow_text(desc,x+25,y+58,535,16,MUTED)
            self.button(title,(x+23,y+107,535,38),action,small=True)
        self.button('Back',(48,762,181,45),'back',True)

    def draw_challenge_hall(self):
        self.header('The challenge hall','Build a contract. Completed combinations stay collected; no daily resets.')
        book=self.store.get('contract_book43',{})
        self.text(f'{len(book)} / {TOTAL} mastery combinations completed',(52,151),25,GOLD)
        self.button('Browse collection',(944,146,287,45),'contract_collection',small=True)
        self.text('Mastery milestones: 1, 10, 50, 120, 240 and all 960 combinations.',(52,187),14,MUTED)
        options=(('Biome',TIERS[self.selected].biome,'contract_tier'),('Difficulty',self.skill,'skill'),
                 ('Ability',self.ability,'ability'),('Players','Co-op' if self.coop else 'Solo','coop'),
                 ('Goal',GOALS[self.contract_goal],'contract_goal'))
        for i,(label,value,action) in enumerate(options):
            y=216+i*77; self.text(label,(65,y+10),21,TEXT)
            self.button(value,(344,y,853,53),action)
        key=f'{self.selected}/{self.skill}/{self.ability}/{int(self.coop)}/{GOALS[self.contract_goal]}'
        self.text('Already completed. Replay to improve your time.' if key in book else 'An uncompleted combination is selected.',(65,627),18,GREEN)
        self.flow_text('Clear: reach the shrine. Untouched: take no hits. Rescue duo: save both Budew. No escape: spend no escape charges. Combined goals require every listed condition.',65,662,1120,16,MUTED)
        self.button('Back',(48,762,181,45),'back')
        self.button('Start contract',(854,752,377,55),'contract_start',True)

    def draw_contract_collection(self):
        self.header('Mastery collection','Browse every combination. Select one to load it into the challenge hall.')
        book=self.store.get('contract_book43',{})
        items=combinations(); start=self.collection_page*8
        for i,(tier,skill,ability,coop,goal) in enumerate(items[start:start+8]):
            key=f'{tier}/{skill}/{ability}/{int(coop)}/{goal}'
            label=f'{start+i+1:03d} / Biome {tier+1} / {skill} / {ability} / '+('Co-op' if coop else 'Solo')+' / '+goal
            y=157+i*66
            self.button(('DONE  ' if key in book else '       ')+label,(48,y,1184,55),f'contract_pick:{start+i}',key in book,small=True)
        self.text(f'Page {self.collection_page+1}/{TOTAL//8}   /   {len(book)}/{TOTAL} completed',(52,704),20,GOLD)
        self.button('Back',(48,767,180,44),'back')
        self.button('Previous',(844,767,180,44),'collection_previous')
        self.button('Next',(1050,767,180,44),'collection_next')

    def draw_long_records(self):
        name=self.store.get('player_alias43','Applin Trainer')
        self.header(name+' / Records','Mouse wheel, Page Up / Page Down or the page buttons browse your full local history.')
        count,wins,best=self.store.summary()
        self.text(f'{count} unique mazes   /   {wins} clears   /   Best score {best:,}',(52,152),24,GOLD)
        total=self.store.db.execute('SELECT COUNT(*) FROM runs').fetchone()[0]
        self.record_offset=min(self.record_offset,max(0,((total-1)//8)*8))
        rows=self.store.db.execute('SELECT tier,outcome,seconds,steps,escapes,score FROM runs ORDER BY id DESC LIMIT 8 OFFSET ?',(self.record_offset,)).fetchall()
        for x,label in zip((65,325,556,734,906,1090),('BIOME','RESULT','TIME','STEPS','ESCAPES','SCORE')): self.text(label,(x,220),14,MUTED)
        for i,(tier,outcome,seconds,steps,escapes,score) in enumerate(rows):
            y=259+i*53; self.panel((48,y,1184,47))
            for x,value in zip((65,325,556,734,906,1090),(f'{tier+1} / {TIERS[tier].name}',outcome,f'{seconds:.1f}s',steps,escapes,score)):
                self.text(value,(x,y+13),16,TEXT)
        if not rows: self.text('Your first adventure is still ahead of you.',(65,300),25,TEXT)
        self.text(f'Page {self.record_offset//8+1} / {max(1,(total+7)//8)}',(52,713),18,GOLD)
        for title,rect,action in (('Back',(48,768,156,44),'back'),('Previous',(233,768,176,44),'record_previous'),('Next',(432,768,176,44),'record_next'),('Name & share',(953,768,277,44),'profile')):
            self.button(title,rect,action,small=True)

    def draw_profile(self):
        self.header('Your player name','A local display name, not an online account. Choose an alias you are comfortable sharing.')
        self.panel((48,164,1184,506)); self.text('TYPE A NAME / UP TO 20 CHARACTERS',(76,190),15,GREEN,bold=True)
        self.panel((75,239,1128,80),(40,60,54)); self.text(self.name_input+'|',(95,258),30,TEXT)
        self.flow_text('Press Enter to save. Export creates a PNG card and a text file with your name, summary and latest challenge code. Share those files yourself; nothing is posted online.',77,365,1090,22)
        self.flow_text(self.profile_notice,77,544,1090,18,GOLD)
        self.button('Back',(48,765,170,45),'back')
        self.button('Save name',(628,751,272,58),'profile_save')
        self.button('Export share card',(925,751,307,58),'profile_share',True)

    def share_profile(self):
        self.action('profile_save')
        name=self.store.get('player_alias43','Applin Trainer'); count,wins,best=self.store.summary()
        book=self.store.get('contract_book43',{})
        code=self.game.code if self.game else self.store.get('last_shared_code43','')
        if code: self.store.set('last_shared_code43',code)
        lines=[name,'Applin Escape / player card',f'{wins} clears | {count} unique maps | best score {best}',f'{len(book)} / {TOTAL} mastery contracts',('Challenge: '+code) if code else '']
        folder=self.store.directory/'exports'; folder.mkdir(exist_ok=True)
        card=pygame.Surface((1100,380)); card.fill((20,37,35))
        for i,line in enumerate(lines): card.blit(self.font(32 if i==0 else 20,bold=i==0).render(line,True,GOLD if i==0 else TEXT),(37,35+i*64))
        try:
            pygame.image.save(card,str(folder/'player_card.png'))
            (folder/'player_card.txt').write_text('\n'.join(lines),encoding='utf-8')
            self.profile_notice='Saved player_card.png and player_card.txt in '+str(folder)
        except OSError as exc: self.profile_notice='Could not export the card: '+str(exc)
