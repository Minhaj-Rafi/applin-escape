import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
import unittest
from unittest.mock import patch
import pygame
from main import App
from home_activities import care_action,care_state
from home_progress import home_progress,decorations


class HomeActivities(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.a=App(self.tmp.name)
    def tearDown(self): self.a.close(); self.tmp.cleanup()
    def residents(self,count):
        p=home_progress(self.a.store); p['rescued']=count; self.a.store.set('sanctuary_v4',p)
    def grow(self,index=0):
        with patch('garden_timers.time.time',return_value=1000):
            for action in ('plant','water','water'): care_action(self.a.store,action,index)
        with patch('garden_timers.time.time',return_value=2000): care_action(self.a.store,'harvest',index)
    def test_garden_lifecycle_and_invalid_actions(self):
        s=self.a.store
        care_action(s,'harvest',0); self.assertEqual(care_state(home_progress(s))['berries'],0)
        self.grow(); c=care_state(home_progress(s))
        self.assertEqual(c['beds'],[0,0,0]); self.assertEqual(c['berries'],2); self.assertEqual(c['harvests'],1)
        care_action(s,'plant',-1); self.assertEqual(care_state(home_progress(s))['beds'],[0,0,0])
    def test_friendship_is_capped_and_unlocks_decor(self):
        self.residents(2); self.grow(); s=self.a.store
        for _ in range(3): care_action(s,'chat',0)
        self.assertEqual(care_state(home_progress(s))['friends']['0'],1)
        care_action(s,'feed',0); care_action(s,'feed',0)
        self.assertEqual(care_state(home_progress(s))['friends']['0'],3)
        self.assertIn('Picnic',decorations(home_progress(s)))
        for _ in range(4): self.grow()
        care_action(s,'chat',1); care_action(s,'feed',1)
        self.assertIn('Blossom arch',decorations(home_progress(s)))
        before=care_state(home_progress(s))['berries']; care_action(s,'feed',0)
        self.assertEqual(care_state(home_progress(s))['berries'],before)
    def test_no_residents_or_berries_cannot_feed(self):
        s=self.a.store; care_action(s,'feed',0)
        self.assertEqual(care_state(home_progress(s))['friends'],{})
        self.residents(1); care_action(s,'feed',0)
        self.assertEqual(care_state(home_progress(s))['berries'],0)
    def test_activity_tabs_clicks_pages_back_and_saved_run_unchanged(self):
        a=self.a; self.residents(11); a.start(); a.action('pause'); saved=a.game.snapshot()
        a.action('sanctuary'); a.action('home_activities')
        with patch('home_progress.secrets.randbelow',side_effect=AssertionError('home rerolled shiny')):
            a.draw(); rect=next(r for r,key in a.buttons if key=='care:plant:0')
            pygame.event.clear()
            with patch.object(a,'mouse',return_value=rect.center):
                pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center)); a.events()
            self.assertEqual(care_state(home_progress(a.store))['beds'][0],1)
            for tab in range(3):
                a.action(f'home_tab:{tab}'); a.large_text=True; a.draw()
            a.action('home_tab:1')
            for _ in range(4): a.action('resident_next'); a.draw()
            self.assertEqual(a.resident_page,0)
            a.action('back'); self.assertEqual(a.screen,'sanctuary')
        self.assertEqual(a.game.snapshot(),saved)
    def test_decorations_render_and_are_stationary(self):
        a=self.a; a.action('sanctuary'); a.comfort=True
        for decor in ('Picnic','Blossom arch'):
            a.home_decor=decor; a.t=0; a.draw(); first=pygame.image.tostring(a.canvas,'RGB')
            a.t=4; a.draw(); self.assertEqual(first,pygame.image.tostring(a.canvas,'RGB'))

if __name__=='__main__': unittest.main()
