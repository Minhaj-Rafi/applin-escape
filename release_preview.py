"""Render every current destination using temporary progress, including frozen builds."""
import json,tempfile
from pathlib import Path
import pygame
from release_info import VERSION

def render_release(folder,verify=False):
    from main import App
    from home_progress import home_progress
    folder.mkdir(parents=True,exist_ok=True)
    names=[]
    with tempfile.TemporaryDirectory() as directory:
        app=App(directory)
        def capture(name):
            app.draw()
            pygame.image.save(app.canvas,str(folder/(name+'.png')))
            names.append(name)
        try:
            app.events()
            if verify:
                if not app.audio.available or len(app.audio.danger_layers)!=5 or not app.controls.enabled:
                    raise RuntimeError('Bundled audio or controller support did not load.')
                if not {'fruit','bell','turn','wind','warning','rescue'}<=app.audio.sounds.keys():
                    raise RuntimeError('Bundled biome effects missing.')
            capture('menu')
            for tier in range(5):
                app.start(tier);capture(f'tier_{tier+1}');app.game.abandon()
            for screen in ('help','settings','controls','adventure','challenge','journal','biome_guide','sanctuary','story','accessibility','home_activities','home_hub','challenge_hall','contract_collection','profile','records','garden_collection','reward_room','run_insights','team_journal'):
                app.screen=screen;capture(screen)
            # Seed illustrative test progress in the temporary database only.
            p=home_progress(app.store);p['rescued']=3;app.store.set('sanctuary_v4',p)
            app.screen='home_activities'
            for tab,name in ((0,'berry_garden'),(1,'resident_album'),(2,'home_milestones'),(3,'projects'),(4,'resident_profile'),(5,'decor_preview')):
                app.home_tab=tab;capture(name)
            app.screen='home_hub';app.home_tour47=0;capture('sanctuary_guide');app.home_tour47=None
            app.action('support');capture('support')
            app.coop=True;app.start(2);capture('coop')
            # Every story panel, with stable low-motion composition and readable text.
            app.screen='story';app.comfort=True
            for tier in range(5):
                app.story_chapter=tier
                for page in range(3):app.story_page=page;capture(f'story_{tier+1}_{page+1}')
            for domain in ('home','maze'):
                app.screen='completion_film';app.reward_domain=domain;capture(domain+'_celebration')
            # Logical canvas has fixed geometry; verify letterboxing and draw at multiple window sizes.
            app.screen='home_activities';app.home_tab=4
            for w,h in ((800,600),(1280,720),(1600,900)):
                app.window=pygame.display.set_mode((w,h),pygame.RESIZABLE);app.draw()
            (folder/'release_check.json').write_text(json.dumps({'version':VERSION,'screens':names,'count':len(names),'window_sizes':[[800,600],[1280,720],[1600,900]],'asset_check':verify},indent=2))
        finally:app.close()
