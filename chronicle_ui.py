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
        if action=='home_tour': self.home_tour47=0; return True
        if action=='tour_next': self.home_tour47=min(3,getattr(self,'home_tour47',0)+1); return True
        if action=='tour_previous': self.home_tour47=max(0,getattr(self,'home_tour47',0)-1); return True
        if action=='tour_done' or (action=='back' and self.screen=='home_hub' and getattr(self,'home_tour47',None) is not None):
            self.home_tour47=None; self.store.set('home_tour_seen47',True); return True
        if action in ('home_hub','challenge_hall','profile','records','contract_collection','garden_collection','reward_room','run_insights','support','team_journal'):
            if self.screen=='play': self.action('pause')
            self.navigation.append((self.screen,self.return_screen)); self.return_screen=self.screen
            self.screen=action
            if action=='support':
                from support49 import snapshot
                self.support_snapshot49=snapshot(self);self.support_notice49='Reports stay on your computer until you choose to share them.'
            if action=='profile': self.name_input=self.store.get('player_alias43','Applin Trainer')
        elif action=='insights_skill': self.insights_skill49=(getattr(self,'insights_skill49',0)+1)%3
        elif action=='insights_players': self.insights_duo49=not getattr(self,'insights_duo49',False)
        elif action=='support_export':
            from support49 import export
            try: self.support_notice49='Saved: '+str(export(self))
            except OSError: self.support_notice49='Could not write the report. Check free space and folder permissions.'
        elif action.startswith('hub_tab:'):
            self.action('home_activities'); self.home_tab=int(action[-1])
        elif action in ('maze_rewards','home_rewards'):
            self.reward_domain='maze' if action=='maze_rewards' else 'home'
            self.action('reward_room')
        elif action in ('garden_next','garden_previous'):
            pages=max(1,(len(self.filtered_home_tasks())+5)//6)
            self.garden_page=(self.garden_page+(1 if action=='garden_next' else -1))%pages
        elif action=='garden_filter':
            self.garden_filter=(getattr(self,'garden_filter',0)+1)%4; self.garden_page=0
        elif action=='garden_remaining':
            self.garden_remaining=not getattr(self,'garden_remaining',False); self.garden_page=0
        elif action.startswith('pin_home:'):
            self.store.set('pinned_home46',action.split(':')[1])
        elif action.startswith('equip_reward:'):
            from rewards44 import reward_rows
            rows=reward_rows(self.store,self.reward_domain); index=int(action.split(':')[1])
            if 0<=index<len(rows) and rows[index][2]: self.store.set('reward_frame44',[self.reward_domain,rows[index][1]])
        elif action=='completion_film':
            from rewards44 import reward_rows
            if reward_rows(self.store,self.reward_domain)[3 if self.reward_domain=='home' else -1][2]:
                self.navigation.append((self.screen,self.return_screen)); self.return_screen=self.screen
                self.screen='completion_film'
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
        if self.screen=='garden_collection':
            if event.type==pygame.MOUSEWHEEL:
                self.action('garden_previous' if event.y>0 else 'garden_next'); return True
            if event.type==pygame.KEYDOWN and event.key in (pygame.K_PAGEUP,pygame.K_PAGEDOWN):
                self.action('garden_previous' if event.key==pygame.K_PAGEUP else 'garden_next'); return True
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
        if getattr(self,'home_tour47',None) is not None:
            self.draw_home_tour47(); return
        self.header('Sanctuary square','Choose a place to visit. Every garden and resident activity is grouped here.')
        self.button('Sanctuary guide',(956,32,276,43),'home_tour',small=True)
        choices=(('Garden & residents','Berry nursery, resident album and home decorations.','hub_tab:0'),
                 ('Sanctuary achievements','Rescues, friendships, garden care and daily interaction goals.','garden_collection'))
        for i,(title,desc,action) in enumerate(choices):
            x=48+(i%2)*601; y=150+(i//2)*180
            self.panel((x,y,582,160)); self.text(f'{i+1:02d}',(x+25,y+19),24,GOLD)
            self.flow_text(desc,x+25,y+58,535,16,MUTED)
            self.button(title,(x+23,y+107,535,38),action,small=True)
        from story_art import draw_scene
        draw_scene(self.canvas,pygame.Rect(48,340,1184,350),0,2,phase=0)
        from rewards44 import sanctuary_tasks
        pinned=self.store.get('pinned_home46','')
        task=next((t for t in sanctuary_tasks(self.store) if t['id']==pinned),None)
        if task: self.text('Pinned: '+task['title']+f" / {min(task['current'],task['target'])}/{task['target']}",(52,716),18,GOLD)
        self.button('Back',(48,762,181,45),'back',True)

    def draw_challenge_hall(self):
        self.header('The challenge hall','Build a contract. Completed combinations stay collected; no daily resets.')
        book=self.store.get('contract_book43',{})
        self.text(f'{len(book)} / {TOTAL} mastery combinations completed',(52,151),25,GOLD)
        self.button('Collection',(824,146,195,45),'contract_collection',small=True)
        self.button('Rewards',(1034,146,197,45),'maze_rewards',small=True)
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
            self.button(('STAMP  ' if key in book else '       ')+label,(48,y,1184,55),f'contract_pick:{start+i}',key in book,small=True)
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
        self.button('Run insights',(660,768,266,44),'run_insights',small=True)
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
        from rewards44 import equipped
        title,color=equipped(self.store)
        lines[1]+=' / '+title
        card=pygame.Surface((1100,380)); card.fill((20,37,35))
        pygame.draw.rect(card,color,(8,8,1084,364),5,border_radius=18)
        for i,line in enumerate(lines): card.blit(self.font(32 if i==0 else 20,bold=i==0).render(line,True,GOLD if i==0 else TEXT),(37,35+i*64))
        try:
            pygame.image.save(card,str(folder/'player_card.png'))
            (folder/'player_card.txt').write_text('\n'.join(lines),encoding='utf-8')
            self.profile_notice='Saved player_card.png and player_card.txt in '+str(folder)
        except OSError as exc: self.profile_notice='Could not export the card: '+str(exc)

    def filtered_home_tasks(self):
        from rewards44 import sanctuary_tasks
        tasks=sanctuary_tasks(self.store); group=getattr(self,'garden_filter',0)
        if group==1: tasks=tasks[:36]
        elif group==2: tasks=tasks[36:72]
        elif group==3: tasks=tasks[72:]
        if getattr(self,'garden_remaining',False): tasks=[t for t in tasks if t['current']<t['target']]
        return tasks

    def draw_garden_collection(self):
        from rewards44 import sanctuary_tasks
        all_tasks=sanctuary_tasks(self.store); tasks=self.filtered_home_tasks()
        count=sum(t['current']>=t['target'] for t in all_tasks)
        pages=max(1,(len(tasks)+5)//6); self.garden_page%=pages
        self.header('Sanctuary achievements','Choose a category, find unfinished goals and select a row to pin it at home.')
        self.text(f'{count} / {len(all_tasks)} stamps earned',(52,151),24,GOLD)
        self.button('Sanctuary rewards',(944,145,288,45),'home_rewards',small=True)
        group=('All goals','Gardening','Community','Advanced mastery')[getattr(self,'garden_filter',0)]
        self.button(group,(48,194,370,38),'garden_filter',small=True)
        self.button('Unfinished only' if getattr(self,'garden_remaining',False) else 'Showing all',(439,194,340,38),'garden_remaining',small=True)
        pinned=self.store.get('pinned_home46','')
        for i,task in enumerate(tasks[self.garden_page*6:self.garden_page*6+6]):
            done=task['current']>=task['target']; y=247+i*69
            self.button('',(48,y,1184,61),'pin_home:'+task['id'],task['id']==pinned,small=True)
            ink=(25,45,34) if task['id']==pinned else GREEN if done else TEXT
            self.text(('DONE / ' if done else '')+task['title'],(71,y+5),19,ink)
            self.text(task['detail'],(71,y+34),13,ink if task['id']==pinned else MUTED)
            self.text(f"{min(task['current'],task['target'])}/{task['target']}",(1120,y+20),17,ink)
        if not tasks: self.text('All goals in this category are complete.',(71,285),24,GREEN)
        self.text('Advanced mastery unlocks the Sanctuary monument. Existing reward thresholds stay unchanged.',(52,697),15,MUTED)
        self.button('Back',(48,768,180,44),'back')
        self.text(f'Page {self.garden_page+1}/{pages}',(680,777),18,TEXT)
        self.button('Previous',(844,768,180,44),'garden_previous')
        self.button('Next',(1050,768,180,44),'garden_next')

    def draw_reward_room(self):
        from rewards44 import reward_rows,equipped
        rows=reward_rows(self.store,self.reward_domain); active,_=equipped(self.store)
        self.header('Maze mastery rewards' if self.reward_domain=='maze' else 'Sanctuary rewards','Earn permanent profile frames and titles. Select an unlocked reward to equip it.')
        for i,(target,title,earned) in enumerate(rows):
            y=156+i*78; self.panel((48,y,1184,67))
            self.text(f'{target} stamp'+('' if target==1 else 's')+f' / {title}',(73,y+19),23,GOLD if earned else MUTED)
            if earned: self.button('Equipped' if active==title else 'Equip frame & title',(902,y+11,304,44),f'equip_reward:{i}',active==title,small=True)
            else: self.text('Locked',(1090,y+24),16,MUTED)
        if self.reward_domain=='home': self.text('Frames use the original 72 goals. The 24 advanced goals unlock the Sanctuary monument.',(52,648),16,MUTED)
        if rows[3 if self.reward_domain=='home' else -1][2]: self.button('Watch completion celebration',(687,690,545,47),'completion_film',True)
        else: self.text('Complete this collection to unlock its final celebration.',(52,697),18,MUTED)
        self.button('Back',(48,767,180,44),'back')

    def draw_completion_film(self):
        import math
        from story_art import draw_scene
        from sanctuary import budew
        from rewards44 import reward_rows
        home=self.reward_domain=='home'
        from home_mastery46 import advanced_tasks
        master=home and all(t['current']>=t['target'] for t in advanced_tasks(home_progress(self.store)))
        self.header(('A thriving home' if master else 'The garden festival') if home else 'The master explorer returns','A permanent celebration of your completed collection.')
        phase=self.t if self.characters and not self.comfort else 0
        draw_scene(self.canvas,pygame.Rect(48,147,1184,350),0 if home else 4,3,phase=phase)
        for i in range(7):
            bob=int(math.sin(phase*2+i)*2) if phase else 0
            budew(self.canvas,((380,440,500,560,790,850,910)[i],465+bob),38)
        pygame.draw.polygon(self.canvas,GOLD,[(673,383),(667,359),(685,370),(698,348),(711,370),(729,359),(723,383)])
        self.panel((48,518,1184,203))
        self.flow_text('You rescued residents, built friendships and brought life to every garden. The residents gather to celebrate a garden that feels like home.' if home else 'Every route, ability and challenge has left its mark. Tonight the garden welcomes its master explorer home.',77,541,1120,25,GOLD)
        self.flow_text(('Sanctuary monument earned: all 24 advanced mastery goals.' if master else 'Sanctuary guardian earned: all 72 sanctuary stamps.' if reward_rows(self.store,'home')[-1][2] else 'Garden crown earned. Your sanctuary journey continues.') if home else 'Master crown earned: all 960 maze mastery stamps.',77,647,1120,21,GREEN)
        self.button('Return to rewards',(836,754,396,50),'back',True)

    def draw_home_tour47(self):
        from journey47 import TOUR
        from story_art import draw_scene
        index=self.home_tour47; title,body=TOUR[index]
        self.header('Welcome home',f'SANCTUARY GUIDE / {index+1} OF 4 / Read at your own pace')
        self.panel((48,150,1184,200))
        self.text(title,(76,172),28,GOLD)
        self.flow_text(body,76,222,1100,22,TEXT)
        draw_scene(self.canvas,pygame.Rect(48,371,1184,350),0,2,phase=0)
        self.button('Close guide',(48,766,230,46),'tour_done')
        if index: self.button('Previous',(694,766,230,46),'tour_previous')
        self.button('Finish' if index==3 else 'Next',(950,766,282,46),'tour_done' if index==3 else 'tour_next',True)

    def draw_run_insights49(self):
        from run_insights49 import summarize,guidance
        skill=('Standard','Expert','Relaxed')[getattr(self,'insights_skill49',0)]
        players='duo' if getattr(self,'insights_duo49',False) else 'solo'
        rows=summarize(self.store,skill,players)
        self.header('Your run insights','Personal history across recorded versions and modes. Descriptive totals, not a leaderboard.')
        self.button(skill,(48,146,280,45),'insights_skill',small=True)
        self.button('Co-op' if players=='duo' else 'Solo',(349,146,230,45),'insights_players',small=True)
        for x,title in ((69,'BIOME'),(499,'RUNS'),(626,'CLEAR %'),(805,'AVG CLEAR TIME'),(1016,'HITS / RUN')):self.text(title,(x,220),14,MUTED)
        for i,row in enumerate(rows):
            y=254+i*73;self.panel((48,y,1184,62))
            values=(row['biome'],row['attempts'],'--' if row['clear_rate'] is None else str(row['clear_rate'])+'%',
                    '--' if row['average_clear_seconds'] is None else str(row['average_clear_seconds'])+'s',
                    '--' if row['average_hits'] is None else row['average_hits'])
            for x,value in zip((69,499,626,805,1016),values):self.text(value,(x,y+19),18,TEXT)
        self.flow_text(guidance(rows),64,643,1150,20,GOLD)
        self.text('Tutorials, abandoned runs and legacy records without difficulty/player details are excluded.',(52,715),14,MUTED)
        self.button('Back',(48,768,180,44),'back')

    def draw_support49(self):
        self.header('Troubleshooting','Check this installation or export a small report when reporting a problem.')
        data=self.support_snapshot49
        rows=(('Game version',data['game_version']),('Python / Pygame',data['python']+' / '+data['pygame']),
              ('Window',str(data['window_size'][0])+' x '+str(data['window_size'][1])),
              ('Sound','Available' if data['audio_available'] else 'Unavailable'),
              ('Controllers',str(data['connected_controllers'])+' connected' if data['controller_support'] else 'Keyboard / mouse mode'),
              ('Save check',data['save_integrity']),('Backup warning','Yes' if data['backup_issue'] else 'None'))
        for i,(title,value) in enumerate(rows):
            y=148+i*59;self.panel((48,y,1184,50));self.text(title,(73,y+12),20,TEXT);self.text(value,(692,y+12),19,GOLD)
        self.flow_text(self.support_notice49,63,585,1150,18,GREEN)
        self.flow_text('For a separate startup check, close the game and run CHECK_SETUP.bat. Reports omit your username, save contents and raw crash log.',63,662,1150,17,MUTED)
        self.button('Back',(48,768,180,44),'back')
        self.button('Export support report',(856,760,376,51),'support_export',True)

    def draw_team_journal50(self):
        book=self.store.get('team_beacons50',{})
        self.header('Better together','An optional co-op collection. One team stamp for each biome.')
        self.panel((48,143,1184,168))
        self.flow_text('In a new co-op run, find the numbered beacon pedestals. P1 stands on 1 and P2 on 2 for 1.5 seconds together. If either leaves or needs rescue, progress resets. After both light up, finish at the shrine to bank the stamp.',74,166,1128,21,TEXT)
        self.text('No extra escape charges or score. Ignore the beacons whenever you prefer a normal run.',(74,272),16,MUTED)
        for i,tier in enumerate(TIERS):
            y=329+i*67;self.panel((48,y,1184,56))
            self.text(tier.biome,(74,y+14),21,TEXT)
            self.text('TEAM STAMP' if str(i) in book else 'Not yet earned',(1001,y+18),15,GREEN if str(i) in book else MUTED)
        self.text('PARTNER BADGE EARNED / all five biome stamps' if len(book)==5 else f'{len(book)} / 5 stamps toward the Partner badge',(52,693),21,GOLD)
        self.button('Back',(48,767,180,45),'back')
        self.text('Choose Co-op in Adventure setup. Existing saved runs keep their original objectives.',(267,780),14,MUTED)
